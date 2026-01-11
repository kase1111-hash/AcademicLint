"""Document parsing utilities for AcademicLint."""

import re
from pathlib import Path


def parse_file(path: Path) -> str:
    """Parse a file and extract text content.

    Supports .md, .txt, and .tex files.

    Args:
        path: Path to the file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is unsupported
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    if suffix == ".md":
        return parse_markdown(content)
    elif suffix == ".txt":
        return content
    elif suffix == ".tex":
        return parse_latex(content)
    else:
        # Try to read as plain text
        return content


def parse_markdown(content: str) -> str:
    """Parse Markdown content and extract text.

    Removes Markdown formatting while preserving text structure.

    Args:
        content: Raw Markdown content

    Returns:
        Plain text with formatting removed
    """
    text = content

    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # Convert links to just text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove heading markers but keep text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove emphasis markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove blockquote markers
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    # Remove list markers
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_latex(content: str) -> str:
    """Parse LaTeX content and extract text.

    Removes LaTeX commands while preserving text content.

    Args:
        content: Raw LaTeX content

    Returns:
        Plain text with LaTeX commands removed
    """
    text = content

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
    text = re.sub(r"\\begin\{(figure|table)\}[\s\S]*?\\end\{\1\}", "", text)

    # Remove equations
    text = re.sub(r"\$\$[\s\S]*?\$\$", "", text)
    text = re.sub(r"\$[^$]+\$", "", text)
    text = re.sub(r"\\begin\{equation\}[\s\S]*?\\end\{equation\}", "", text)
    text = re.sub(r"\\begin\{align\}[\s\S]*?\\end\{align\}", "", text)

    # Convert section commands to text
    text = re.sub(r"\\(section|subsection|subsubsection|chapter)\*?\{([^}]+)\}", r"\2\n\n", text)

    # Remove formatting commands but keep content
    text = re.sub(r"\\(textbf|textit|emph|underline)\{([^}]+)\}", r"\2", text)

    # Remove citations (keep as placeholder)
    text = re.sub(r"\\cite\{[^}]+\}", "[citation]", text)

    # Remove references
    text = re.sub(r"\\ref\{[^}]+\}", "[ref]", text)

    # Remove labels
    text = re.sub(r"\\label\{[^}]+\}", "", text)

    # Remove other common commands
    text = re.sub(r"\\(newpage|clearpage|pagebreak)", "", text)
    text = re.sub(r"\\(small|large|Large|LARGE|huge|Huge)", "", text)

    # Remove remaining commands with braces
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)

    # Remove remaining simple commands
    text = re.sub(r"\\[a-zA-Z]+", "", text)

    # Clean up braces
    text = re.sub(r"[{}]", "", text)

    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
