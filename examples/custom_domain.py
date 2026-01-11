#!/usr/bin/env python3
"""Example of using custom domain terms with AcademicLint."""

from academiclint import Config, Linter

# Sample philosophy text
philosophy_text = """
The epistemological implications of Kant's phenomenology suggest
that our understanding of ontology must be reconsidered. Many scholars
believe that hermeneutics provides a framework for understanding
these complex issues.
"""

# Without domain terms - "epistemological", etc. might be flagged as jargon
print("=== Without Domain Terms ===")
linter = Linter()
result = linter.check(philosophy_text)
print(f"Density: {result.density:.2f}")
print(f"Flags: {len(result.flags)}")
for flag in result.flags:
    print(f"  [{flag.type.value}] {flag.term}")
print()

# With philosophy domain - technical terms are acceptable
print("=== With Philosophy Domain ===")
config = Config(
    domain="philosophy",
    # You can also add custom terms
    domain_terms=["hermeneutics", "phenomenology"],
)
linter = Linter(config)
result = linter.check(philosophy_text)
print(f"Density: {result.density:.2f}")
print(f"Flags: {len(result.flags)}")
for flag in result.flags:
    print(f"  [{flag.type.value}] {flag.term}")
print()

# Using a custom domain file
print("=== Using Custom Domain File ===")
print("Create a YAML file like this:")
print("""
# my-domain.yml
name: cognitive-science
parent: psychology
technical_terms:
  - affordance
  - embodied cognition
  - enactivism
domain_weasels:
  - "the brain wants"
density_baseline: 0.55
""")
print()
print("Then use:")
print('  config = Config(domain_file="my-domain.yml")')
