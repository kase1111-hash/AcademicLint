"""Tests for Markdown and LaTeX text extraction."""

from academiclint.core.parser import (
    CITATION_PLACEHOLDER,
    latex_to_text,
    markdown_to_text,
    parse_file,
    parse_latex,
    parse_markdown,
)

MARKDOWN = """# Intro

```python
x = 1
```

- See [the docs](https://example.com) because many experts agree.
<!-- a
comment -->
## Methods
We did things.

Para one.

- item one
- item two
"""

LATEX = r"""\section{Introduction}
Freedom is being free.

\begin{figure}
\caption{A figure}
\end{figure}
\subsection[Short]{Done.}

Prior work \cite{smith2019,
  jones2020} is cited. Text with $x
+ y$ math.
"""


def line_of(text: str, needle: str) -> int:
    return text[: text.index(needle)].count("\n") + 1


class TestSourceLines:
    """Lines of the extracted text map back to the right source lines."""

    def test_markdown_lines_map_to_source(self):
        parsed = markdown_to_text(MARKDOWN)

        for needle in ("many experts", "We did things", "Para one", "item two"):
            assert parsed.source_line(line_of(parsed.text, needle)) == line_of(MARKDOWN, needle)

    def test_latex_lines_map_to_source(self):
        parsed = latex_to_text(LATEX)

        for needle in ("Freedom is being free", "is cited", "math."):
            assert parsed.source_line(line_of(parsed.text, needle)) == line_of(LATEX, needle)

    def test_flag_lines_reported_against_source(self, tmp_path):
        """check_file reports the source line, not the line in the extracted text."""
        from academiclint import FlagType, Linter

        path = tmp_path / "paper.tex"
        path.write_text(
            "\\section{Intro}\nWe begin here.\n\nPrior work \\cite{a,\n  b} is cited.\n\n"
            "Many experts agree that this is true.\n",
            encoding="utf-8",
        )

        result = Linter().check_file(path)

        weasel = [f for f in result.flags if f.type == FlagType.WEASEL]
        assert [f.line for f in weasel] == [7]

    def test_list_items_start_sentences(self):
        """Each list item's start is recorded, without moving its text."""
        markdown = markdown_to_text("Two groups:\n- first item\n  wrapped\n1. second item\n")
        latex = latex_to_text(
            "Two groups:\n\\begin{itemize}\n  \\item first item\n\\item second item\n"
        )

        for parsed in (markdown, latex):
            starts = parsed.sentence_starts
            assert [parsed.text[i:].split("\n")[0].strip() for i in starts] == [
                "first item",
                "second item",
            ]
        assert markdown.text.splitlines()[1].index("first") == 2

    def test_markdown_line_markers_keep_columns(self):
        parsed = parse_markdown("- many experts\n> some scholars\n## Heading here\n")

        assert parsed.splitlines()[0].index("many") == 2
        assert parsed.splitlines()[1].index("some") == 2


class TestStructure:
    """Paragraph and sentence structure survives markup removal."""

    def test_blank_line_before_list_kept(self):
        parsed = parse_markdown("Para one.\n\n- item one\n- item two\n")

        assert "Para one.\n\n" in parsed

    def test_heading_directly_above_text_gets_its_own_paragraph(self):
        assert parse_markdown("## Methods\nWe did things.") == "   Methods\n\nWe did things."
        assert parse_latex("\\section{Experiment A}\nWe did things.") == (
            "Experiment A\n\nWe did things."
        )

    def test_heading_with_text_on_the_same_line(self):
        assert parse_latex("\\section{Results} We found things.") == "Results\n\nWe found things."

    def test_heading_followed_by_line_left_blank(self):
        """A \\label (with a comment) under a heading leaves only spaces behind."""
        parsed = parse_latex("\\section{Background}\n\\label{sec:b} % c\nDemocracy is a system.")

        assert parsed.split("\n\n")[0] == "Background"

    def test_heading_title_with_formatting(self):
        parsed = parse_latex("\\section{The Meaning of \\emph{Freedom} Today}\nFreedom is free.")

        assert parsed == "The Meaning of Freedom Today\n\nFreedom is free."

    def test_multi_line_citation_keeps_sentence_whole(self):
        """Lines freed by an inline command must not become paragraph breaks."""
        source = (
            "Recent studies show \\cite{\n  smith2019,\n  jones2020\n} that this was a trial.\n"
        )
        parsed = latex_to_text(source)

        assert "\n\n" not in parsed.text
        assert parsed.text.count("\n") == source.rstrip().count("\n")

    def test_multi_line_citation_ending_its_line(self):
        """The closing brace's line must not be left empty either."""
        parsed = parse_latex("Several studies \\cite{a,\n b,\n c}\nhave shown it.")

        assert "\n\n" not in parsed

    def test_dollars_across_paragraph_break_are_not_math(self):
        """Math can't hold a blank line, so the paragraph break stays."""
        parsed = parse_latex("Next para with $x\n\ny$ math.")

        assert "\n\n" in parsed

    def test_footnote_of_two_paragraphs_keeps_sentence_whole(self):
        parsed = parse_latex(
            "Sleep loss causes deficits\\footnote{Measured with n-back.\n\n"
            "Two studies differ.} in adolescents (Walker, 2017)."
        )

        assert "\n\n" not in parsed

    def test_less_than_sign_is_not_an_html_tag(self):
        """'p < .001' must not swallow text up to the next '>' (a quote marker)."""
        source = "Recall improved (p < .001).\n\n## Discussion\n\n> Rest is good."

        assert parse_markdown(source).split("\n\n") == [
            "Recall improved (p < .001).",
            "   Discussion",
            "  Rest is good.",
        ]

    def test_escaped_dollars_are_not_math(self):
        assert parse_latex("It costs \\$5 and then \\$10.") == "It costs \\$5 and then \\$10."

    def test_line_break_before_math(self):
        """A dollar after a \\\\ line break opens math; it isn't an escaped \\$."""
        parsed = parse_latex("\\author{Jane Doe\\\\$^{1}$ Dept}\nSome studies show $x$ is true.")

        assert "Some studies show  is true." in parsed

    def test_multi_line_inline_match_at_line_start(self):
        """A removed construct starting a line must not leave that line empty."""
        latex = parse_latex(
            "Supervised methods dominate\n\\footnote{See the survey\nby Smith.} while others lag.\n"
            "Kernel methods\n$k(x,\ny)$ scale poorly."
        )
        markdown = parse_markdown(
            "It is widely accepted that sleep aids consolidation\n<!-- TODO: check\nthis -->\n"
            "(Walker, 2017)."
        )

        assert "\n\n" not in latex
        assert "\n\n" not in markdown

    def test_citation_after_punctuation_goes_before_it(self):
        """A citation after the period stays with its sentence, not the next one."""
        parsed = parse_latex("It was a failure.\\footcite{smith1990}\nResearch shows more.")

        assert parsed == f"It was a failure {CITATION_PLACEHOLDER}.\nResearch shows more."

    def test_heading_title_with_nested_commands(self):
        parsed = parse_latex(
            "\\section{\\texorpdfstring{\\emph{In vitro}}{In vitro}}\nFreedom is being free."
        )

        assert parsed.split("\n\n") == ["In vitro", "Freedom is being free."]

    def test_heading_followed_by_blank_line_unchanged(self):
        assert parse_markdown("## Methods\n\nWe did things.") == "   Methods\n\nWe did things."

    def test_markdown_closing_hashes(self):
        """Only a run of #'s after a space closes a heading, so "C#" keeps its '#'."""
        assert parse_markdown("## Why C#") == "   Why C#"
        assert parse_markdown("# foo#") == "  foo#"
        assert parse_markdown("# foo ##") == "  foo"

    def test_markdown_extension_parsed_as_markdown(self, tmp_path):
        path = tmp_path / "notes.markdown"
        path.write_text("# Title\n\nSome **bold** text.\n", encoding="utf-8")

        assert parse_file(path) == "  Title\n\nSome bold text."
