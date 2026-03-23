from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Default limits; can be overridden via Settings / security config.
DEFAULT_CV_MAX_FILE_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MiB
ALLOWED_CV_EXTENSIONS: Final[frozenset[str]] = frozenset({".pdf", ".docx"})


@dataclass(frozen=True)
class CVLimits:
    """Resolved limits for CV uploads (file size and extracted text length)."""

    max_file_bytes: int
    max_text_chars: int
