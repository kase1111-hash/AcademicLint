"""Domain management for AcademicLint."""

from pathlib import Path
from typing import Optional

from academiclint.domains.loader import load_domain


class DomainManager:
    """Manages domain vocabularies and settings."""

    BUILTIN_DOMAINS = {
        "philosophy",
        "computer-science",
    }

    def __init__(self):
        self._loaded_domains: dict = {}
        self._builtin_path = Path(__file__).parent / "builtin"

    def get_domain(self, name: str) -> dict:
        """Get a domain by name.

        Args:
            name: Domain name (built-in or custom path)

        Returns:
            Domain definition dictionary
        """
        if name in self._loaded_domains:
            return self._loaded_domains[name]

        if name in self.BUILTIN_DOMAINS:
            domain = self._load_builtin(name)
        else:
            # Try loading as a file path
            domain = load_domain(name)

        self._loaded_domains[name] = domain
        return domain

    def _load_builtin(self, name: str) -> dict:
        """Load a built-in domain.

        Raises:
            FileNotFoundError: If the domain .yml file does not exist
        """
        path = self._builtin_path / f"{name}.yml"

        if not path.exists():
            raise FileNotFoundError(
                f"Built-in domain file not found: {path}. "
                f"Valid built-in domains: {', '.join(sorted(self.BUILTIN_DOMAINS))}"
            )

        return load_domain(path)

    def list_domains(self) -> list[dict]:
        """List available domains.

        Returns:
            List of domain info dictionaries
        """
        domains = []

        for name in self.BUILTIN_DOMAINS:
            domain = self.get_domain(name)
            domains.append(
                {
                    "name": name,
                    "term_count": len(domain.get("technical_terms", [])),
                }
            )

        return domains

    def get_terms(self, domain_name: Optional[str]) -> set[str]:
        """Get all technical terms for a domain.

        Args:
            domain_name: Name of the domain

        Returns:
            Set of technical terms
        """
        if not domain_name:
            return set()

        domain = self.get_domain(domain_name)
        terms = set(domain.get("technical_terms", []))

        # Include parent terms
        parent = domain.get("parent")
        if parent:
            terms.update(self.get_terms(parent))

        return terms
