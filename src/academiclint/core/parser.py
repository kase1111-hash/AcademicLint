"""Document parsing utilities for AcademicLint."""

import re
from dataclasses import dataclass
from pathlib import Path

# What citation commands such as \\cite{...} become; detectors treat it as a citation
CITATION_PLACEHOLDER = "[citation]"

# Marks the end of a heading's title until _finish splits headings off from
# the text after them. Removed from the input first so it can't be forged.
_HEADING_END = "\x1e"


@dataclass
class ParsedText:
    """Text extracted from a document, with a map back to the source lines."""

    text: str
    # Source line (1-based) of each line of text; None when they are the same
    source_lines: list[int] | None = None

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


def _sub_keep_lines(pattern: str, repl: str, text: str, *, inline: bool) -> str:
    """re.sub that keeps the line breaks of each replaced match.

    Flag positions are reported as line numbers in the parsed text, so they
    only point at the right source line if parsing never drops one. Removed
    block constructs (code blocks, figures) leave empty lines, which separate
    paragraphs. Removed inline constructs (a \\cite spread over several lines)
    mirror the source instead: a line stays empty only if it was blank in the
    source, so a sentence around them stays whole and a real paragraph break
    inside them is kept.
    """

    def replace(match: re.Match[str]) -> str:
        new = match.expand(repl)
        removed = match.group(0).count("\n") - new.count("\n")
        if removed <= 0:
            return new
        if not inline:
            return new + "\n" * removed
        tail = match.group(0).split("\n")[-removed:]
        return new + "".join("\n" + (" " if part.strip() else "") for part in tail)

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


def _blank(match: re.Match[str]) -> str:
    """Replace a match with spaces, keeping columns on the line unchanged."""
    return " " * len(match.group(0))


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
    for number, line in enumerate(lines, 1):
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
    return ParsedText(text, source[: text.count("\n") + 1])


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
    text = content.replace(_HEADING_END, "")

    # Remove code blocks
    text = _sub_keep_lines(r"```[\s\S]*?```", "", text, inline=False)
    text = _sub_keep_lines(r"`[^`]+`", "", text, inline=True)

    # Remove images
    text = _sub_keep_lines(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text, inline=True)

    # Convert links to just text
    text = _sub_keep_lines(r"\[([^\]]+)\]\([^)]+\)", r"\1", text, inline=True)

    # Remove HTML comments and tags. A tag must start like one ("<a", "</a"),
    # so "p < .001" ... ">" is not taken for a tag and deleted.
    text = _sub_keep_lines(r"<!--[\s\S]*?-->", "", text, inline=True)
    text = _sub_keep_lines(r"</?[A-Za-z][^<>]*>", "", text, inline=True)

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

    # Remove emphasis markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove blockquote and list markers ([ \t], not \s, so the blank line
    # before a list stays)
    text = re.sub(r"^>[ \t]*", _blank, text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*[-*+][ \t]+", _blank, text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*\d+\.[ \t]+", _blank, text, flags=re.MULTILINE)

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
    text = content.replace(_HEADING_END, "")

    # Remove comments
    text = re.sub(r"%.*$", "", text, flags=re.MULTILINE)

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
    # Inline math; an escaped \\$ is a literal dollar sign
    text = _sub_keep_lines(r"(?<!\\)\$(?:[^$\\]|\\.)+\$", "", text, inline=True)
    text = _sub_keep_lines(r"\\begin\{equation\}[\s\S]*?\\end\{equation\}", "", text, inline=False)
    text = _sub_keep_lines(r"\\begin\{align\}[\s\S]*?\\end\{align\}", "", text, inline=False)

    # Convert section commands to their titles
    text = _convert_sections(text)

    # Remove formatting commands but keep content
    text = re.sub(r"\\(textbf|textit|emph|underline)\{([^}]+)\}", r"\2", text)

    # Remove citations (keep as placeholder)
    text = _sub_keep_lines(
        r"\\(?:cite[pt]?|parencite|textcite|autocite|footcite)\*?(?:\[[^\]]*\])*\{[^}]+\}",
        CITATION_PLACEHOLDER,
        text,
        inline=True,
    )

    # Remove references
    text = _sub_keep_lines(r"\\ref\{[^}]+\}", "[ref]", text, inline=True)

    # Remove labels
    text = _sub_keep_lines(r"\\label\{[^}]+\}", "", text, inline=True)

    # Remove other common commands
    text = re.sub(r"\\(newpage|clearpage|pagebreak)", "", text)
    text = re.sub(r"\\(small|large|Large|LARGE|huge|Huge)", "", text)

    # Remove remaining commands with braces
    text = _sub_keep_lines(r"\\[a-zA-Z]+\{[^}]*\}", "", text, inline=True)

    # Remove remaining simple commands
    text = re.sub(r"\\[a-zA-Z]+", "", text)

    # Clean up braces
    text = re.sub(r"[{}]", "", text)

    return _finish(text)
