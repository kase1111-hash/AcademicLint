"""Tests for Markdown and LaTeX text extraction."""

from academiclint.core.parser import parse_file, parse_latex, parse_markdown

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
\subsection{Done.}

Text with $x
+ y$ math.
"""


def line_of(text: str, needle: str) -> int:
    return text[: text.index(needle)].count("\n") + 1


class TestLinePreservation:
    """Parsed text keeps every source line, so flag line numbers match the file."""

    def test_markdown_keeps_line_numbers(self):
        parsed = parse_markdown(MARKDOWN)

        for needle in ("many experts", "We did things", "Para one", "item two"):
            assert line_of(parsed, needle) == line_of(MARKDOWN, needle)

    def test_latex_keeps_line_numbers(self):
        parsed = parse_latex(LATEX)

        for needle in ("Freedom is being free", "math."):
            assert line_of(parsed, needle) == line_of(LATEX, needle)

    def test_markdown_line_markers_keep_columns(self):
        parsed = parse_markdown("- many experts\n> some scholars\n## Heading here\n")

        assert parsed.splitlines()[0].index("many") == 2
        assert parsed.splitlines()[1].index("some") == 2


class TestStructure:
    """Paragraph and sentence structure survives markup removal."""

    def test_blank_line_before_list_kept(self):
        parsed = parse_markdown("Para one.\n\n- item one\n- item two\n")

        assert "Para one.\n\n" in parsed

    def test_heading_directly_above_text_ends_as_sentence(self):
        assert parse_markdown("## Methods\nWe did things.").split("\n")[0].strip() == "Methods."
        assert parse_latex("\\section{Methods}\nWe did things.").startswith("Methods.\n")

    def test_heading_followed_by_blank_line_unchanged(self):
        assert parse_markdown("## Methods\n\nWe did things.").split("\n")[0].strip() == "Methods"
        assert parse_latex("\\section{Done.}\nText.").startswith("Done.\n")

    def test_markdown_extension_parsed_as_markdown(self, tmp_path):
        path = tmp_path / "notes.markdown"
        path.write_text("# Title\n\nSome **bold** text.\n", encoding="utf-8")

        assert parse_file(path) == "  Title\n\nSome bold text."
