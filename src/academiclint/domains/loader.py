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

    with path.open(encoding="utf-8") as f:
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

    parent = data.get("parent")
    if parent is not None and not isinstance(parent, str):
        raise ValueError(f"'parent' must be a domain name, got {type(parent).__name__}")

    # Set defaults
    domain = {
        "name": data.get("name", "custom"),
        "description": data.get("description", ""),
        "parent": parent,
        "density_baseline": data.get("density_baseline", 0.50),
        "density_strict": data.get("density_strict", 0.65),
    }
    for key in (
        "technical_terms",
        "domain_weasels",
        "permitted_hedges",
        "accepted_causal_patterns",
        "domain_fillers",
    ):
        # An empty YAML key (`technical_terms:`) loads as None
        value = data.get(key) or []
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ValueError(f"'{key}' must be a list of strings")
        domain[key] = value

    return domain
