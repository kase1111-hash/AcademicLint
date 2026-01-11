"""HTML formatter for AcademicLint."""

from collections import Counter

from academiclint.core.result import AnalysisResult
from academiclint.formatters.base import Formatter


class HTMLFormatter(Formatter):
    """Formatter for HTML report output."""

    def __init__(self, **kwargs):
        pass

    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as HTML report."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AcademicLint Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .metric {{
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #666;
        }}
        .density-bar {{
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .density-fill {{
            height: 100%;
            background: linear-gradient(90deg, #dc3545, #ffc107, #28a745);
            background-size: 200% 100%;
        }}
        .paragraph {{
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .paragraph-header {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .flag {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
        .flag-high {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .flag-low {{
            background: #d1ecf1;
            border-left-color: #17a2b8;
        }}
        .flag-type {{
            font-weight: bold;
            color: #856404;
        }}
        .flag-high .flag-type {{ color: #721c24; }}
        .flag-low .flag-type {{ color: #0c5460; }}
        .suggestion {{
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>AcademicLint Report</h1>
    <p>Generated: {result.created_at}</p>

    {self._format_summary_html(result)}

    <h2>Detailed Findings</h2>
    {self._format_paragraphs_html(result)}

    {self._format_suggestions_html(result)}
</body>
</html>"""

    def _format_summary_html(self, result: AnalysisResult) -> str:
        """Format the summary section as HTML."""
        density_percent = result.density * 100

        return f"""
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="metric">
                <div class="metric-value">{result.density:.2f}</div>
                <div class="metric-label">Density ({result.summary.density_grade})</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.summary.flag_count}</div>
                <div class="metric-label">Flags</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.summary.word_count}</div>
                <div class="metric-label">Words</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.summary.paragraph_count}</div>
                <div class="metric-label">Paragraphs</div>
            </div>
        </div>
        <div class="density-bar">
            <div class="density-fill" style="width: {density_percent}%;"></div>
        </div>
    </div>"""

    def _format_paragraphs_html(self, result: AnalysisResult) -> str:
        """Format paragraphs as HTML."""
        paragraphs_html = []

        for para in result.paragraphs:
            if not para.flags:
                continue

            flags_html = []
            for flag in para.flags:
                severity_class = f"flag-{flag.severity.value}"
                flags_html.append(f"""
                <div class="flag {severity_class}">
                    <span class="flag-type">{flag.type.value}</span>: "{flag.term}"
                    <p>{flag.message}</p>
                    <p class="suggestion">Suggestion: {flag.suggestion}</p>
                </div>""")

            text_preview = para.text[:200] + "..." if len(para.text) > 200 else para.text

            paragraphs_html.append(f"""
            <div class="paragraph">
                <div class="paragraph-header">Paragraph {para.index + 1} (Density: {para.density:.2f})</div>
                <p>"{text_preview}"</p>
                {"".join(flags_html)}
            </div>""")

        return "".join(paragraphs_html) if paragraphs_html else "<p>No issues found.</p>"

    def _format_suggestions_html(self, result: AnalysisResult) -> str:
        """Format suggestions as HTML."""
        if not result.overall_suggestions:
            return ""

        items = "".join(f"<li>{s}</li>" for s in result.overall_suggestions)
        return f"""
    <h2>Overall Suggestions</h2>
    <ul>{items}</ul>"""
