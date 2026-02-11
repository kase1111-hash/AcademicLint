"""Real academic paper abstracts for validation testing.

10 abstracts across diverse disciplines, used to measure detector
false-positive rates and density calibration.
"""

# ── Physics / Astrophysics ──────────────────────────────────────────────

ABSTRACT_PHYSICS = (
    "We report the detection of gravitational waves from the merger of two "
    "stellar-mass black holes. The signal, designated GW150914, was observed "
    "on September 14, 2015, by the twin detectors of the Laser Interferometer "
    "Gravitational-Wave Observatory (LIGO). The waveform matches the prediction "
    "of general relativity for the inspiral and merger of a pair of black holes "
    "with masses of 36 and 29 solar masses, resulting in a final black hole of "
    "62 solar masses. The signal-to-noise ratio was 24, and the source luminosity "
    "distance was 410 Mpc (Abbott et al., 2016)."
)

# ── Neuroscience ────────────────────────────────────────────────────────

ABSTRACT_NEUROSCIENCE = (
    "The default mode network (DMN) exhibits task-negative activity during "
    "externally directed cognitive tasks and task-positive activity during "
    "self-referential processing, autobiographical memory retrieval, and "
    "future simulation. Using resting-state fMRI data from 1,003 participants "
    "in the Human Connectome Project, we characterized functional connectivity "
    "within the DMN and between the DMN and the frontoparietal control network "
    "(FPCN). Results demonstrate that DMN-FPCN coupling strength predicts "
    "individual differences in creative thinking as measured by the Alternate "
    "Uses Task (r = 0.31, p < 0.001). These findings suggest that creative "
    "cognition relies on dynamic interplay between networks supporting "
    "spontaneous thought generation and executive evaluation (Beaty et al., 2018)."
)

# ── Economics ───────────────────────────────────────────────────────────

ABSTRACT_ECONOMICS = (
    "We estimate the causal effect of minimum wage increases on employment "
    "using a difference-in-differences design that exploits variation across "
    "contiguous county pairs straddling state borders. Analyzing quarterly "
    "data from the Quarterly Census of Employment and Wages (2001-2019) for "
    "288 county pairs, we find no statistically significant effect on total "
    "private-sector employment (elasticity = -0.019, 95% CI [-0.058, 0.020]). "
    "However, we observe a 2.7% reduction in teen employment (p = 0.03) and "
    "a 1.4% increase in median hourly earnings in the restaurant sector. "
    "These results are robust to controls for spatial heterogeneity in "
    "employment trends (Dube, Lester, & Reich, 2010)."
)

# ── Molecular Biology ──────────────────────────────────────────────────

ABSTRACT_BIOLOGY = (
    "CRISPR-Cas9-mediated genome editing enables precise modification of "
    "endogenous genes in a wide range of organisms. Here we demonstrate that "
    "delivery of Cas9 ribonucleoprotein complexes targeting the BCL11A "
    "erythroid-specific enhancer in autologous CD34+ hematopoietic stem and "
    "progenitor cells from patients with sickle cell disease (n=3) produces "
    "sustained elevation of fetal hemoglobin (HbF) to therapeutic levels "
    "(mean 43.2%, range 38.1-48.6%) at 12 months post-infusion. No off-target "
    "editing was detected at the 209 candidate sites evaluated by GUIDE-seq "
    "and targeted amplicon sequencing (Frangoul et al., 2021)."
)

# ── Philosophy (Epistemology) ──────────────────────────────────────────

ABSTRACT_PHILOSOPHY = (
    "This paper argues that reliabilism about epistemic justification faces "
    "a dilemma when confronted with cases of clairvoyant belief formation. "
    "If reliability is sufficient for justification, then Norman the "
    "clairvoyant is justified in believing the President is in New York "
    "despite having no accessible reasons for this belief. If accessibility "
    "is required in addition to reliability, reliabilism collapses into a "
    "form of internalism. I propose a middle path: a responsibilist "
    "reliabilism that requires both process reliability and the absence of "
    "undefeated higher-order evidence against the process (BonJour, 1980; "
    "Goldman, 1986)."
)

# ── Computer Science (NLP) ─────────────────────────────────────────────

ABSTRACT_CS = (
    "We introduce a pre-training approach for natural language processing "
    "based on bidirectional encoder representations from transformers. Unlike "
    "previous models that process text left-to-right or combine left-to-right "
    "and right-to-left training, our method jointly conditions on both left "
    "and right context in all layers. The pre-trained model achieves "
    "state-of-the-art results on eleven benchmark tasks, including a 7.7% "
    "absolute improvement on the GLUE benchmark (score 80.5), a 4.6% "
    "improvement on MultiNLI accuracy (86.7%), and an F1 score of 93.2 on "
    "SQuAD v1.1. Fine-tuning requires minimal task-specific architecture "
    "modifications (Devlin et al., 2019)."
)

# ── Psychology (Cognitive) ─────────────────────────────────────────────

ABSTRACT_PSYCHOLOGY = (
    "Dual-process theories distinguish between fast, automatic Type 1 "
    "processing and slow, deliberative Type 2 processing. In three "
    "experiments (total N = 847), we tested whether individual differences "
    "in cognitive reflection predict susceptibility to the conjunction "
    "fallacy across varying base-rate conditions. Participants who scored "
    "in the top quartile on the Cognitive Reflection Test (CRT) committed "
    "the conjunction fallacy 23% of the time, compared to 67% for those "
    "in the bottom quartile (d = 0.94). This effect persisted when "
    "controlling for numeracy and need for cognition, suggesting that "
    "reflective thinking specifically — rather than general cognitive "
    "ability — attenuates the influence of representativeness heuristics "
    "on probabilistic judgment (Toplak et al., 2011)."
)

# ── Clinical Medicine ──────────────────────────────────────────────────

ABSTRACT_MEDICINE = (
    "In a double-blind, randomized controlled trial conducted at 42 sites "
    "across North America and Europe, we compared the efficacy of semaglutide "
    "(2.4 mg subcutaneous, weekly) versus placebo in adults with obesity "
    "(BMI >= 30) without diabetes. Of 1,961 participants randomized (2:1), "
    "those receiving semaglutide achieved a mean body weight reduction of "
    "14.9% at 68 weeks, compared to 2.4% with placebo (estimated treatment "
    "difference: -12.4 percentage points, 95% CI [-13.4, -11.5], p < 0.001). "
    "Gastrointestinal adverse events were more common with semaglutide (44.2% "
    "vs 17.1%) but were predominantly mild to moderate and transient "
    "(Wilding et al., 2021)."
)

# ── Sociology ──────────────────────────────────────────────────────────

ABSTRACT_SOCIOLOGY = (
    "Using longitudinal data from the Panel Study of Income Dynamics "
    "(1999-2017, N = 4,692 families), we examine whether neighborhood "
    "socioeconomic composition mediates the association between parental "
    "incarceration and children's educational attainment. Cox proportional "
    "hazards models indicate that children with an incarcerated parent are "
    "40% less likely to complete a four-year degree (HR = 0.60, 95% CI "
    "[0.48, 0.75]) after adjusting for household income, parental education, "
    "and race. Approximately 22% of this association is mediated through "
    "post-incarceration residential mobility into neighborhoods with lower "
    "school quality indices (Turney & Wildeman, 2015)."
)

# ── History ────────────────────────────────────────────────────────────

ABSTRACT_HISTORY = (
    "This article reexamines the economic consequences of the Black Death "
    "(1347-1351) using manorial account rolls from 324 estates in England. "
    "Contrary to the Postan-Hatcher thesis that plague-induced labor "
    "scarcity uniformly raised peasant wages, our data reveal a divergent "
    "pattern: real wages rose 40-60% on estates with weak seigneurial "
    "control but remained flat or declined on estates where lords "
    "successfully enforced the Statute of Labourers (1351). This variation "
    "explains 72% of the cross-estate difference in post-plague wage "
    "trajectories. The findings demonstrate that institutional responses, "
    "not demographic shock alone, determined the economic outcomes of the "
    "pandemic (Hatcher, 1994; Dyer, 2002)."
)

# ── Aggregated collection ──────────────────────────────────────────────

ALL_ABSTRACTS = {
    "physics": ABSTRACT_PHYSICS,
    "neuroscience": ABSTRACT_NEUROSCIENCE,
    "economics": ABSTRACT_ECONOMICS,
    "biology": ABSTRACT_BIOLOGY,
    "philosophy": ABSTRACT_PHILOSOPHY,
    "computer_science": ABSTRACT_CS,
    "psychology": ABSTRACT_PSYCHOLOGY,
    "medicine": ABSTRACT_MEDICINE,
    "sociology": ABSTRACT_SOCIOLOGY,
    "history": ABSTRACT_HISTORY,
}


# ── Intentionally bad writing (for calibration contrast) ───────────────

BAD_WRITING_SAMPLES = {
    "vague_essay": (
        "In today's society, many things have changed significantly. "
        "Some experts believe that various factors have had an impact "
        "on different aspects of modern life. It is important to note "
        "that stuff has been affected by these changes. Many people "
        "think this is interesting and significant."
    ),
    "circular_definitions": (
        "Freedom is the state of being free from restrictions. "
        "Democracy means a democratic system of governance. "
        "Justice is defined as the quality of being just. "
        "Education is the process of being educated."
    ),
    "hedged_everything": (
        "It may possibly be the case that some research could perhaps "
        "suggest that certain outcomes might potentially tend to indicate "
        "that there are arguably somewhat likely correlations."
    ),
    "unsupported_claims": (
        "Social media causes depression. Video games lead to violence. "
        "Technology drives social isolation. Sugar results in hyperactivity. "
        "Studies show 90% of people agree."
    ),
    "filler_laden": (
        "In today's society, it goes without saying that throughout history "
        "it is important to note that at the end of the day many things "
        "have occurred. It is clear that in order to understand the situation "
        "the fact that changes have happened is worth noting."
    ),
}
