"""Load markdown prompt templates from ``prompts/templates/*.md``.

``prompt_strategies`` calls ``load_template_text`` with logical names (e.g.
``zero_shot``). Path traversal in template names is rejected.

Outputs: raw template strings for placeholder substitution in strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptTemplate:
    """Lightweight template container (name + text + optional description)."""

    name: str
    text: str
    description: str | None = None


_TEMPLATES_DIR = Path(__file__).parent / "templates"


def list_templates() -> list[str]:
    """Return available template names (without extension)."""
    if not _TEMPLATES_DIR.exists():
        return []
    return sorted(p.stem for p in _TEMPLATES_DIR.glob("*.md") if p.is_file())


def load_template_text(name: str) -> str:
    """
    Load a template by name (without extension) from `templates/`.

    Raises:
        FileNotFoundError: if the template does not exist.
        ValueError: if name looks like a path traversal.
    """
    normalized = name.strip().replace("\\", "/")
    if "/" in normalized or normalized in {"", ".", ".."}:
        raise ValueError("Template name must be a simple file stem (no paths).")

    path = _TEMPLATES_DIR / f"{normalized}.md"
    return path.read_text(encoding="utf-8")


def load_template(name: str) -> PromptTemplate:
    """
    Load a template and extract optional metadata from an HTML comment header.

    The templates in this project start with:
        <!--
        name: ...
        description: ...
        -->
    """
    text = load_template_text(name)
    description = _extract_description(text)
    return PromptTemplate(name=name, text=text, description=description)


def _extract_description(text: str) -> str | None:
    # Intentionally simple: avoid adding YAML deps for a scaffold.
    start = text.find("<!--")
    end = text.find("-->")
    if start == -1 or end == -1 or end < start:
        return None
    header = text[start + 4 : end]
    for line in header.splitlines():
        if line.strip().lower().startswith("description:"):
            return line.split(":", 1)[1].strip() or None
    return None

