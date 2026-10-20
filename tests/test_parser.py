"""Tests for Markdown and LaTeX text extraction."""

import pytest

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
        stars = markdown_to_text("Two groups:\n* first item\n* second item\n")
        latex = latex_to_text(
            "Two groups:\n\\begin{itemize}[noitemsep]\n  \\item first item\n\\item second item\n"
        )

        for parsed in (markdown, stars, latex):
            starts = parsed.sentence_starts
            assert [parsed.text[i:].split("\n")[0].strip() for i in starts] == [
                "first item",
                "second item",
            ]
        assert markdown.text.splitlines()[1].index("first") == 2
        assert "noitemsep" not in latex.text

    def test_list_items_continuing_a_sentence(self):
        """Items that carry on the sentence before them don't start sentences."""
        parsed = markdown_to_text(
            "Recall is predicted by\n- attention,\n- depth of processing, and\n- retrieval [12].\n"
        )

        assert parsed.sentence_starts == []

    @pytest.mark.parametrize(
        "lead",
        [
            "**Strengths**",
            "Results\n=======",
            "Key findings of the review\n==========",
            "Step 1: Data collection",
            "**Table 2.** Sample characteristics",
            "Three measures were used. Primary outcome measures",
            "Grades were lower. [12]",
            "Prior work agrees.[12]  ",
            "This is well documented.[^1]",
            'Some called it "a failure."',
        ],
    )
    def test_list_after_label_or_finished_sentence(self, lead):
        """A label or a finished sentence above a list is not a lead-in."""
        parsed = markdown_to_text(f"{lead}\n- first item\n- second item\n")

        assert len(parsed.sentence_starts) == 2

    @pytest.mark.parametrize(
        ("source", "starts"),
        [
            # A lead-in wrapped over two lines carries on into the list
            (
                "Prior work is extensive, and several\nstudies show that\n- a holds [12],\n"
                "- b holds [13], and\n- c holds [14].\n",
                0,
            ),
            # A short lead-in clause too; the next item starts a new sentence
            ("Research suggests that\n- a holds (Lee, 2021)\n- b holds (Kim, 2020)\n", 1),
            # A lead-in after a sentence on the same line, or after "et al."
            ("Sleep was tracked for two weeks. Lee [4] observed\n- that 40% slept less\n", 0),
            ("In a cohort of 2,000 adolescents,\nHale et al. [7] found\n- a 30% rise\n", 0),
            # A short one after a sentence on the same line
            (
                "It is common in adolescence. Studies show\n- shorter sleep [3],\n- later bedtimes [5].\n",
                0,
            ),
        ],
    )
    def test_list_after_lead_in_clause(self, source, starts):
        assert len(markdown_to_text(source).sentence_starts) == starts

    def test_loose_numbered_list(self):
        """An indented paragraph inside an item doesn't end the list."""
        parsed = markdown_to_text(
            "1. Recruitment\n\n   Schools were contacted.\n2. Consent was given\n"
        )
        lazy = markdown_to_text("1. item one that\nwraps here\n2. item two\n")
        year = markdown_to_text(
            "1. Approval was granted in\n   2019. Most parents agreed.\n2. Next\n"
        )

        assert len(parsed.sentence_starts) == 2
        assert "2." not in parsed.text
        assert len(lazy.sentence_starts) == 2
        assert "2019. Most parents agreed." in year.text

    def test_heading_closes_a_list(self):
        parsed = markdown_to_text(
            "1. A\n2. B\n\n## Methods\nRecruited in the autumn of\n2019. Each took part.\n"
        )

        assert "2019. Each took part." in parsed.text

    def test_year_starting_a_wrapped_line_is_not_a_list(self):
        """As in CommonMark, only "1." can start a list inside a paragraph."""
        parsed = markdown_to_text("It was first reported by Smith in\n2019. Many experts agree.\n")
        listed = markdown_to_text("Results:\n\n2. second\n3. third\n")

        assert "2019. Many experts agree." in parsed.text
        assert parsed.sentence_starts == []
        assert len(listed.sentence_starts) == 2

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

    def test_comment_inside_math(self):
        """A commented-out line inside wrapped math is not a paragraph break."""
        parsed = parse_latex(
            "We minimise $L(w) =\n% + \\lambda_1 R(w)\n+ w$ over all weights.\n"
            "Many experts agree that this works, and $w$ is unique."
        )

        assert "Many experts agree that this works, and  is unique." in parsed

    def test_html_comment_with_blank_line_ends_paragraph(self):
        """As in Markdown, a comment holding a blank line ends the block before it."""
        parsed = parse_markdown(
            "- Screen time causes insomnia\n<!-- check\n\nthis -->\nWalker (2017) reported it."
        )

        assert "\n\n" in parsed

    def test_escaped_percent_is_not_a_comment(self):
        """'\\%' is a percent sign: the line goes on, in math or out of it."""
        parsed = parse_latex(
            "The group improved by $12\\%$ more, and 92\\% of sessions ran.\n"
            "Many experts agree.\nThe slope $b$ was positive. % a comment"
        )

        assert parsed == (
            "The group improved by  more, and 92\\% of sessions ran.\n"
            "Many experts agree.\nThe slope  was positive."
        )

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
        run = parse_latex("It was a failure.\\cite{a}\\cite{b} Research shows more.")
        subject = parse_latex("It lasts.\\cite{a}\n\\citet{b} showed that it causes harm.")
        tied = parse_latex("It held on school nights.~\\cite{a}\nStudies show more.")

        assert parsed == f"It was a failure {CITATION_PLACEHOLDER}.\nResearch shows more."
        assert run == f"It was a failure {CITATION_PLACEHOLDER}. Research shows more."
        assert subject == (
            f"It lasts {CITATION_PLACEHOLDER}.\n{CITATION_PLACEHOLDER} showed that it causes harm."
        )
        assert tied == f"It held on school nights {CITATION_PLACEHOLDER}.\nStudies show more."

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
