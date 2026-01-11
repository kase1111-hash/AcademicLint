#!/usr/bin/env python3
"""Basic usage example for AcademicLint."""

from academiclint import Config, Linter

# Sample text to analyze
sample_text = """
In today's society, technology has had a significant impact on
the way people communicate. Many experts believe this has led
to both positive and negative outcomes. It is clear that more
research is needed to fully understand these complex dynamics.
"""

# Initialize linter with default configuration
linter = Linter()

# Analyze the text
result = linter.check(sample_text)

# Print basic results
print(f"Analysis ID: {result.id}")
print(f"Processing time: {result.processing_time_ms}ms")
print()

# Print summary
print("=== Summary ===")
print(f"Overall Density: {result.density:.2f} ({result.summary.density_grade})")
print(f"Total Flags: {result.summary.flag_count}")
print(f"Word Count: {result.summary.word_count}")
print()

# Print each flag
print("=== Flags ===")
for flag in result.flags:
    print(f"[{flag.type.value}] '{flag.term}'")
    print(f"  Line {flag.line}: {flag.message}")
    print(f"  Suggestion: {flag.suggestion}")
    print()

# Print overall suggestions
if result.overall_suggestions:
    print("=== Overall Suggestions ===")
    for suggestion in result.overall_suggestions:
        print(f"  - {suggestion}")
