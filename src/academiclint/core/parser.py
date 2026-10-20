"""Document parsing utilities for AcademicLint."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# What citation commands such as \\cite{...} become; detectors treat it as a
# citation. Its brackets (U+27E6/U+27E7) keep a "[citation]" typed in a draft as
# a reminder from counting as one, and the parsers don't split them off.
CITATION_PLACEHOLDER = "\u27e6citation\u27e7"

# Marks the end of a heading's title until _finish splits headings off from
# the text after them. Removed from the input first so it can't be forged.
_HEADING_END = "\x1e"
# Marks where a list item starts until _finish records it (and blanks it).
# Removed from the input first, like _HEADING_END.
_ITEM_START = "\x1a"
# Stands in for a removed LaTeX comment until the end of parsing, so a line
# that held only a comment isn't taken for a blank line before then (inline
# math may wrap around it). Removed from the input first, like _HEADING_END.
_COMMENT = "\x1b"


@dataclass
class ParsedText:
    """Text extracted from a document, with a map back to the source lines."""

    text: str
    # Source line (1-based) of each line of text; None when they are the same
    source_lines: list[int] | None = None
    # Offsets in text where a sentence starts whatever the parser finds, such
    # as list items, which rarely end with a full stop
    sentence_starts: list[int] = field(default_factory=list)

    def source_line(self, line: int) -> int:
        """Map a 1-based line of the extracted text to its line in the source."""
        if self.source_lines is None or not 1 <= line <= len(self.source_lines):
            return line
        return self.source_lines[line - 1]


def parse_document(path: Path | str) -> ParsedText:
    """Parse a file and extract its text, with a map back to source lines.

    Supports .md/.markdown, .tex and plain text files.

    Args:
        path: Path to the file

    Returns:
        Extracted text and its source line map

    Raises:
        FileNotFoundError: If the file doesn't exist
        UnicodeDecodeError: If the file is not valid UTF-8
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    if suffix in (".md", ".markdown"):
        return markdown_to_text(content)
    if suffix == ".tex":
        return latex_to_text(content)
    # Plain text
    return ParsedText(content)


def parse_file(path: Path | str) -> str:
    """Parse a file and extract text content.

    Args:
        path: Path to the file

    Returns:
        Extracted text content
    """
    return parse_document(path).text


def _sub_keep_lines(
    pattern: str,
    repl: str | Callable[[re.Match[str]], str],
    text: str,
    *,
    inline: bool,
    keep_blank: bool = False,
) -> str:
    """re.sub that keeps the line breaks of each replaced match.

    Flag positions are reported as line numbers in the parsed text, so they
    only point at the right source line if parsing never drops one. Removed
    block constructs (code blocks, figures) leave empty lines, which separate
    paragraphs. Removed inline constructs (a \\cite spread over several lines,
    a footnote of two paragraphs) leave lines holding a space instead, so the
    sentence around them stays whole. With keep_blank, a line that was blank
    in the source stays empty: an HTML comment holding a blank line ends the
    paragraph before it, as in Markdown.
    """

    def replace(match: re.Match[str]) -> str:
        new = repl(match) if callable(repl) else match.expand(repl)
        removed = match.group(0).count("\n") - new.count("\n")
        if removed <= 0:
            return new
        if not inline:
            return new + "\n" * removed
        if not keep_blank:
            # A space on every line, the first included: the match may start it
            return new + " \n" * removed + " "
        parts = match.group(0).split("\n")
        head = " " if parts[0].strip() else ""
        return (
            new + head + "".join("\n" + (" " if part.strip() else "") for part in parts[-removed:])
        )

    return re.sub(pattern, replace, text)


_SECTION = re.compile(r"\\(?:section|subsection|subsubsection|chapter)\*?(?:\[[^\]\n]*\])?\{")


def _convert_sections(text: str) -> str:
    """Replace LaTeX section commands with their titles, marked as headings.

    The title's closing brace is found by counting braces (escaped ones
    excepted), so titles holding commands such as \\emph{...} at any depth
    are kept whole; those commands are removed later. A title whose braces
    don't balance on its line is left for the later clean-up.
    """
    out = []
    pos = 0
    for match in _SECTION.finditer(text):
        if match.start() < pos:
            continue
        depth = 1
        i = match.end()
        while i < len(text) and text[i] != "\n":
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth:
            continue
        out += [text[pos : match.start()], text[match.end() : i].strip(), _HEADING_END]
        pos = i + 1
    out.append(text[pos:])
    return "".join(out)


def _citation(match: re.Match[str]) -> str:
    """The placeholder for a citation command, before any punctuation it follows."""
    if match.group(1):
        return f" {CITATION_PLACEHOLDER}{match.group(1)}"
    return CITATION_PLACEHOLDER


def _blank(match: re.Match[str]) -> str:
    """Replace a match with spaces, keeping columns on the line unchanged."""
    return " " * len(match.group(0))


def _item(match: re.Match[str]) -> str:
    """Replace a list marker with spaces, marking where the item starts."""
    return " " * (len(match.group(0)) - 1) + _ITEM_START


# The end of a sentence or lead-in: punctuation, then closing quotes or
# brackets or a footnote reference ('failure."', "documented.[^1]")
_LINE_END = re.compile(r"[.:!?][\"'\u201d\u2019)\]]*(?:\[\^[^\]]*\])?$")


_BULLET = re.compile(r"[ \t]*[-*+][ \t]+")
_NUMBERED = re.compile(r"[ \t]*(\d+)\.[ \t]+")


def _mark_list_items(text: str) -> str:
    """Mark Markdown list items (see _item).

    As in CommonMark, a numbered item other than "1." can't interrupt a
    paragraph, so a wrapped line starting "2019. The..." stays text.
    """
    lines = text.split("\n")
    in_list = False  # After a list item, up to the next blank line
    prev_blank = True
    for i, line in enumerate(lines):
        match = _BULLET.match(line) or _NUMBERED.match(line)
        if match and match.re is _NUMBERED and not (prev_blank or in_list):
            match = None if match.group(1) != "1" else match
        if match:
            lines[i] = _item(match) + line[match.end() :]
            in_list = True
        elif not line.strip():
            in_list = False
        prev_blank = not line.strip()
    return "\n".join(lines)


def _continues(prev: str, in_list: bool) -> bool:
    """Whether a list item carries on the sentence of the line before it.

    It does after a comma, semicolon, "and" or "or" ("predicted by\n- a,\n-
    b, and\n- c [12].") and after a lead-in clause without punctuation; a
    new item after an unpunctuated item, after a lead-in ending "...groups:",
    or after a short label ("Strengths", a setext underline) starts a sentence.
    """
    prev = prev.rstrip()
    words = prev.split()
    if prev.endswith((",", ";")) or (words and words[-1].lower() in ("and", "or")):
        return True
    return not in_list and len(words) >= 4 and not _LINE_END.search(prev)


def _finish(text: str) -> ParsedText:
    """Split headings off from the text after them and map lines to the source.

    Every step before this keeps the source's line breaks. A heading directly
    followed by text (on its own line or the next) would run into the first
    sentence, so a blank line is added after it to make it a paragraph of its
    own; the added lines are recorded so line numbers still match the source.
    """
    lines = text.split("\n")
    out: list[str] = []
    source: list[int] = []
    in_list = False  # After a list item, up to the next blank line
    for number, raw in enumerate(lines, 1):
        line = raw
        if not line.strip():
            in_list = False
        elif _ITEM_START in line:
            if out and out[-1].strip() and _continues(out[-1], in_list):
                line = line.replace(_ITEM_START, " ")
            in_list = True
        if _HEADING_END not in line:
            out.append(line)
            source.append(number)
            continue

        title, _, rest = line.partition(_HEADING_END)
        rest = rest.replace(_HEADING_END, "").strip()
        out.append(title.rstrip())
        source.append(number)
        if rest:
            # Text on the heading's own line, e.g. \section{Results} We found...
            out += ["", rest]
            source += [number, number]
        elif number < len(lines) and lines[number] != "":
            # Text on the next line. A line left holding only spaces (e.g. by a
            # removed \\label) is not a paragraph break, so it gets one too.
            out.append("")
            source.append(number)

    text = "\n".join(out).rstrip()
    starts = [i for i, c in enumerate(text) if c == _ITEM_START]
    text = text.replace(_ITEM_START, " ")
    return ParsedText(text, source[: text.count("\n") + 1], starts)


def parse_markdown(content: str) -> str:
    """Parse Markdown content and extract text.

    Args:
        content: Raw Markdown content

    Returns:
        Plain text with formatting removed
    """
    return markdown_to_text(content).text


def markdown_to_text(content: str) -> ParsedText:
    """Parse Markdown content and extract text, with a map back to source lines.

    Removes Markdown formatting while preserving text structure.

    Args:
        content: Raw Markdown content

    Returns:
        Plain text with formatting removed, and its source line map
    """
    text = content.replace(_HEADING_END, "").replace(_ITEM_START, "")

    # Remove code blocks
    text = _sub_keep_lines(r"```[\s\S]*?```", "", text, inline=False)
    # A code span can't hold a blank line; a match across one is two stray backticks
    text = _sub_keep_lines(r"`(?:[^`\n]|\n(?![ \t]*\n))+`", "", text, inline=True)

    # Remove images
    text = _sub_keep_lines(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text, inline=True)

    # Convert links to just text
    text = _sub_keep_lines(r"\[([^\]]+)\]\([^)]+\)", r"\1", text, inline=True)

    # Remove HTML comments and tags. A tag must start like one ("<a", "</a"),
    # so "p < .001" ... ">" is not taken for a tag and deleted.
    text = _sub_keep_lines(r"<!--[\s\S]*?-->", "", text, inline=True, keep_blank=True)
    text = _sub_keep_lines(r"</?[A-Za-z][^<>]*>", "", text, inline=True, keep_blank=True)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}[ \t]*$", "", text, flags=re.MULTILINE)

    # Remove heading markers but keep text. Line-start markers become spaces
    # of the same width so columns on those lines still match the source. A
    # closing run of #'s only counts after a space, so "C#" keeps its '#'.
    text = re.sub(
        r"^([ \t]{0,3}#{1,6}[ \t]+)(.*?)(?:[ \t]+#+)?[ \t]*$",
        lambda m: " " * len(m.group(1)) + m.group(2) + _HEADING_END,
        text,
        flags=re.MULTILINE,
    )

    # Remove blockquote and list markers ([ \t], not \s, so the blank line
    # before a list stays). Before emphasis, which would pair up '*' bullets.
    text = re.sub(r"^>[ \t]*", _blank, text, flags=re.MULTILINE)
    text = _mark_list_items(text)

    # Remove emphasis markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    return _finish(text)


def parse_latex(content: str) -> str:
    """Parse LaTeX content and extract text.

    Args:
        content: Raw LaTeX content

    Returns:
        Plain text with LaTeX commands removed
    """
    return latex_to_text(content).text


def latex_to_text(content: str) -> ParsedText:
    """Parse LaTeX content and extract text, with a map back to source lines.

    Removes LaTeX commands while preserving text content.

    Args:
        content: Raw LaTeX content

    Returns:
        Plain text with LaTeX commands removed, and its source line map
    """
    text = content.replace(_HEADING_END, "").replace(_ITEM_START, "").replace(_COMMENT, "")

    # Remove comments
    text = re.sub(r"(?<!\\)((?:\\\\)*)%.*$", rf"\1{_COMMENT}", text, flags=re.MULTILINE)

    # Remove document class and packages
    text = re.sub(r"\\documentclass(\[.*?\])?\{.*?\}", "", text)
    text = re.sub(r"\\usepackage(\[.*?\])?\{.*?\}", "", text)

    # Remove begin/end document
    text = re.sub(r"\\begin\{document\}", "", text)
    text = re.sub(r"\\end\{document\}", "", text)

    # Remove common environments but keep content
    for env in ["abstract", "quote", "quotation", "center"]:
        text = re.sub(rf"\\begin\{{{env}\}}", "", text)
        text = re.sub(rf"\\end\{{{env}\}}", "", text)

    # Remove figure/table environments entirely
    text = _sub_keep_lines(r"\\begin\{(figure|table)\}[\s\S]*?\\end\{\1\}", "", text, inline=False)

    # Remove equations
    text = _sub_keep_lines(r"\$\$[\s\S]*?\$\$", "", text, inline=False)
    # Inline math. A dollar sign after an odd number of backslashes is a
    # literal \\$; after an even number (a \\\\ line break) it opens math. Math
    # can't hold a blank line, so a match across one is two stray dollar signs.
    text = _sub_keep_lines(
        r"(?<!\\)((?:\\\\)*)\$(?:[^$\\\n]|\\.|\n(?![ \t]*\n))+\$", r"\1", text, inline=True
    )
    text = _sub_keep_lines(r"\\begin\{equation\}[\s\S]*?\\end\{equation\}", "", text, inline=False)
    text = _sub_keep_lines(r"\\begin\{align\}[\s\S]*?\\end\{align\}", "", text, inline=False)

    # Convert section commands to their titles
    text = _convert_sections(text)

    # Remove formatting commands but keep content
    text = re.sub(r"\\(textbf|textit|emph|underline)\{([^}]+)\}", r"\2", text)

    # Replace citations with a placeholder. A run of parenthetical or note
    # citations on a line becomes one, and one placed after the punctuation
    # (".\\footcite{...}") goes before it, so it stays with the sentence it
    # cites rather than joining it to the next one. \\citet and \\textcite are
    # part of their sentence ("\\citet{x} showed..."), so they stand alone.
    args = r"\*?(?:\[[^\]]*\])*\{[^}]+\}"
    note = rf"\\(?:cite|citep|parencite|autocite|footcite){args}"
    text = _sub_keep_lines(rf"([.!?])?{note}(?:[ \t]*{note})*", _citation, text, inline=True)
    text = _sub_keep_lines(rf"\\(?:citet|textcite){args}", CITATION_PLACEHOLDER, text, inline=True)

    # Remove references
    text = _sub_keep_lines(r"\\ref\{[^}]+\}", "[ref]", text, inline=True)

    # Remove labels
    text = _sub_keep_lines(r"\\label\{[^}]+\}", "", text, inline=True)

    # List items, marked so that each starts a sentence
    text = re.sub(r"^[ \t]*\\item\b[ \t]*", _item, text, flags=re.MULTILINE)

    # Remove other common commands
    text = re.sub(r"\\(newpage|clearpage|pagebreak)", "", text)
    text = re.sub(r"\\(small|large|Large|LARGE|huge|Huge)", "", text)

    # Remove remaining commands with braces
    text = _sub_keep_lines(r"\\[a-zA-Z]+\{[^}]*\}", "", text, inline=True)

    # Remove remaining simple commands
    text = re.sub(r"\\[a-zA-Z]+", "", text)

    # Clean up braces
    text = re.sub(r"[{}]", "", text)

    return _finish(text.replace(_COMMENT, ""))
