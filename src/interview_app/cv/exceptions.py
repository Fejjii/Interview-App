"""Domain-specific errors for CV upload and analysis."""


class CVProcessingError(Exception):
    """Base class for CV pipeline failures (user-safe messages)."""


class CVFileValidationError(CVProcessingError):
    """Unsupported type, too large, or empty file."""


class CVExtractionError(CVProcessingError):
    """Text could not be extracted or document is unreadable."""


class CVAnalysisError(CVProcessingError):
    """LLM or parsing step failed after extraction."""
