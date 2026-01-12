"""Sample academic texts with known characteristics for testing.

Each sample has documented expected outcomes for verification.
"""

# =============================================================================
# HIGH QUALITY TEXTS (Should have high density, few flags)
# =============================================================================

GOOD_TEXT_PRECISE = """
Smartphone-based messaging reduced response latency in personal
communication from hours (email) to minutes (SMS/chat) between 2007
and 2015, while simultaneously decreasing average message length from
150+ words to under 20 words per message (Pew Research, 2023).

This compression correlates with a 23% decline in perceived
conversation depth among users aged 18-34 (Thompson et al., 2022),
though the causal mechanism remains unestablished. Three hypotheses
merit investigation: cognitive load reduction, social norm shifts,
and platform-induced behavior modification.
"""

GOOD_TEXT_PRECISE_EXPECTED = {
    "min_density": 0.5,
    "max_flag_count": 3,
    "density_grade_acceptable": ["adequate", "dense", "crystalline"],
}

GOOD_TEXT_SCIENTIFIC = """
The enzyme lactase hydrolyzes lactose into glucose and galactose
in the small intestine. Lactase persistence, the continued expression
of lactase into adulthood, occurs in approximately 35% of the global
population (Ingram et al., 2009).

The LCT gene on chromosome 2 encodes lactase-phlorizin hydrolase.
A single nucleotide polymorphism (C/T-13910) located 13,910 base
pairs upstream of the LCT gene correlates strongly with lactase
persistence in European populations (r² = 0.97, Enattah et al., 2002).
"""

GOOD_TEXT_SCIENTIFIC_EXPECTED = {
    "min_density": 0.5,
    "max_flag_count": 2,
    "density_grade_acceptable": ["adequate", "dense", "crystalline"],
}


# =============================================================================
# LOW QUALITY TEXTS (Should have low density, many flags)
# =============================================================================

BAD_TEXT_VAGUE = """
In today's society, technology has had a significant impact on
the way people communicate. Many experts believe this has led
to both positive and negative outcomes. It is clear that more
research is needed to fully understand these complex dynamics.

Society has changed dramatically in recent years. Some scholars
argue that these changes are important. Others disagree. The
implications are far-reaching and deserve further study.
"""

BAD_TEXT_VAGUE_EXPECTED = {
    "max_density": 0.5,
    "min_flag_count": 5,
    "expected_flag_types": ["UNDERSPECIFIED", "WEASEL", "FILLER"],
    "density_grade_acceptable": ["vapor", "thin"],
}

BAD_TEXT_WEASEL = """
Some researchers suggest that social media may have effects on
mental health. It is believed by many that these effects could
be significant. Experts have noted that studies indicate possible
correlations. Many scholars argue this warrants attention.

It is often said that technology changes society. Research has
shown that there may be impacts. Some argue these findings are
important, while others remain skeptical.
"""

BAD_TEXT_WEASEL_EXPECTED = {
    "max_density": 0.45,
    "min_flag_count": 6,
    "expected_flag_types": ["WEASEL"],
    "density_grade_acceptable": ["vapor", "thin"],
}


# =============================================================================
# TEXTS WITH SPECIFIC ISSUES (For targeted detector testing)
# =============================================================================

TEXT_CIRCULAR_DEFINITIONS = """
Freedom is fundamentally the state of being free from oppression
and constraints. Democracy can be defined as a democratic system
of governance. Intelligence is the quality of being intelligent.

A leader is someone who leads others. Creativity is the ability
to be creative. Justice means acting in a just manner.
"""

TEXT_CIRCULAR_EXPECTED = {
    "min_flag_count": 3,
    "required_flag_types": ["CIRCULAR"],
    "min_circular_flags": 3,
}

TEXT_CAUSAL_CLAIMS = """
Social media causes depression in teenagers. The policy led to
economic growth. Video games make children violent. Climate change
caused the hurricane.

Poverty leads to crime. Education causes success. The treatment
cured the disease. The new law reduced unemployment.
"""

TEXT_CAUSAL_EXPECTED = {
    "min_flag_count": 4,
    "required_flag_types": ["UNSUPPORTED_CAUSAL"],
    "min_causal_flags": 4,
}

TEXT_HEDGE_STACK = """
It could perhaps be argued that there may be some evidence that
possibly suggests the data might indicate a somewhat tentative
relationship that could potentially exist between the variables.

One might tentatively suggest that it is perhaps somewhat possible
that there could maybe be some indication of a potential trend.
"""

TEXT_HEDGE_EXPECTED = {
    "min_flag_count": 2,
    "required_flag_types": ["HEDGE_STACK"],
    "min_hedge_flags": 2,
}

TEXT_CITATION_NEEDED = """
Studies show that 73% of college students experience significant
anxiety. Research indicates teenagers spend 9 hours daily on screens.
Scientists have proven that meditation reduces cortisol levels by 40%.

According to recent findings, 85% of jobs require digital literacy.
Data reveals climate change will cost the global economy $23 trillion.
"""

TEXT_CITATION_EXPECTED = {
    "min_flag_count": 3,
    "required_flag_types": ["CITATION_NEEDED"],
    "min_citation_flags": 3,
}

TEXT_JARGON_DENSE = """
The hermeneutic phenomenology of Dasein's thrownness reveals the
ontic-ontological difference through existential analytic methodology.
Deconstructive logocentrism interrogates phallogocentric epistemology.

Hypostatic differentiation manifests through pneumatological
instantiation of periochoretic circumincession within trinitarian
oikonomia and theologia frameworks.
"""

TEXT_JARGON_EXPECTED = {
    "min_flag_count": 2,
    "required_flag_types": ["JARGON_DENSE"],
}

TEXT_FILLER_HEAVY = """
In today's modern society, as we all know, it goes without saying
that at the end of the day, when all is said and done, the fact
of the matter is that, needless to say, in this day and age, we
must consider the situation.

At this point in time, for all intents and purposes, it is what
it is, and at the end of the day, the bottom line is that we need
to think outside the box and move forward.
"""

TEXT_FILLER_EXPECTED = {
    "min_flag_count": 5,
    "required_flag_types": ["FILLER"],
    "min_filler_flags": 5,
}


# =============================================================================
# MIXED QUALITY TEXTS (For regression testing)
# =============================================================================

TEXT_MIXED_QUALITY = """
The 2008 financial crisis resulted from a combination of factors
including subprime mortgage lending, excessive leverage ratios
exceeding 30:1 at major investment banks (IMF, 2009), and failures
in credit rating agency oversight.

Many experts believe the regulatory response was significant.
In today's society, some argue that reforms were needed. The
implications remain complex and deserve further study by scholars.
"""

TEXT_MIXED_EXPECTED = {
    "min_density": 0.25,
    "max_density": 0.65,
    "paragraph_count": 2,
    "first_paragraph_min_density": 0.5,
    "second_paragraph_max_density": 0.45,
}


# =============================================================================
# EDGE CASES
# =============================================================================

TEXT_SINGLE_SENTENCE = "This is a single sentence for testing."

TEXT_SINGLE_EXPECTED = {
    "paragraph_count": 1,
    "sentence_count_min": 1,
}

TEXT_UNICODE = """
The café served crème brûlée with naïve résumé formatting.
Пример текста на русском языке для тестирования Unicode.
日本語のテキストサンプル。中文测试文本。
"""

TEXT_UNICODE_EXPECTED = {
    "should_not_error": True,
    "paragraph_count_min": 1,
}

TEXT_LATEX_STYLE = r"""
The equation $E = mc^2$ demonstrates mass-energy equivalence.
Consider the integral $\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$.

According to \cite{Einstein1905}, special relativity requires
that the speed of light $c$ remain constant in all reference frames.
"""

TEXT_LATEX_EXPECTED = {
    "should_not_error": True,
    "paragraph_count_min": 1,
}

TEXT_MARKDOWN = """
# Introduction

This is a **bold** statement with *italic* emphasis.

## Methods

We used the following approach:

1. First step
2. Second step
3. Third step

> This is a blockquote with some content.

The `code` samples demonstrate technical concepts.
"""

TEXT_MARKDOWN_EXPECTED = {
    "should_not_error": True,
    "paragraph_count_min": 1,
}
