"""Domain file loading for AcademicLint."""

from pathlib import Path
from typing import Any

import yaml


def load_domain(path: Path | str) -> dict[str, Any]:
    """Load a domain definition from a YAML file.

    Args:
        path: Path to the domain YAML file

    Returns:
        Domain definition dictionary
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Domain file not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f)

    return validate_domain(data)


def validate_domain(data: dict) -> dict:
    """Validate domain definition structure.

    Args:
        data: Raw domain data from YAML

    Returns:
        Validated domain dictionary
    """
    if not isinstance(data, dict):
        raise ValueError("Domain file must contain a YAML dictionary")

    # Set defaults
    domain = {
        "name": data.get("name", "custom"),
        "description": data.get("description", ""),
        "parent": data.get("parent"),
        "technical_terms": data.get("technical_terms", []),
        "domain_weasels": data.get("domain_weasels", []),
        "permitted_hedges": data.get("permitted_hedges", []),
        "accepted_causal_patterns": data.get("accepted_causal_patterns", []),
        "density_baseline": data.get("density_baseline", 0.50),
        "density_strict": data.get("density_strict", 0.65),
        "domain_fillers": data.get("domain_fillers", []),
    }

    return domain
