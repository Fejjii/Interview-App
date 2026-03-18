"""
Language detection and response-language handling.

Used to detect language from user input (job description or first message)
and to enforce that all model outputs (questions, feedback, critique) are in that language.
Defaults to English when detection is uncertain.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"

# ISO 639-1 code -> display name for UI and prompts
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ar": "Arabic",
    "pt": "Portuguese",
    "it": "Italian",
    "zh-cn": "Chinese (Simplified)",
    "ja": "Japanese",
}

_LANGDETECT_AVAILABLE: bool | None = None


def langdetect_available() -> bool:
    """True if the langdetect package is installed (required for Auto language detection)."""
    global _LANGDETECT_AVAILABLE
    if _LANGDETECT_AVAILABLE is None:
        try:
            __import__("langdetect")
            _LANGDETECT_AVAILABLE = True
        except ImportError:
            _LANGDETECT_AVAILABLE = False
    return _LANGDETECT_AVAILABLE


def detect_language(text: str) -> str:
    """
    Detect the language of the given text. Returns ISO 639-1 code.
    Falls back to DEFAULT_LANGUAGE if detection fails or text is too short.
    """
    text = (text or "").strip()
    if len(text) < 10:
        return DEFAULT_LANGUAGE
    try:
        import langdetect

        lang = langdetect.detect(text)
        if lang and lang in SUPPORTED_LANGUAGES:
            return lang
        if lang:
            return lang
        return DEFAULT_LANGUAGE
    except Exception:
        return DEFAULT_LANGUAGE


def get_language_name(code: str) -> str:
    """Return display name for prompt instructions; falls back to English for unknown codes."""
    return SUPPORTED_LANGUAGES.get((code or "").strip().lower(), "English")


def language_instruction(response_language: str) -> str:
    """One-line instruction to prepend to system prompts so all output is in the chosen language."""
    name = get_language_name(response_language)
    return f"You must respond only in {name}. All questions, follow-ups, grading, and critique must be in {name}."
