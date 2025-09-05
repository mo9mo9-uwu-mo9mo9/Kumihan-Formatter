"""Unified exception classes for Kumihan-Formatter (experimental).

These classes are currently introduced for future adoption and are not
raised by default in the codebase unless explicitly enabled via an
environment switch in specific modules.
"""

from __future__ import annotations


class KumihanError(Exception):
    """Base exception for all Kumihan-Formatter specific errors."""


class KumihanSyntaxError(KumihanError):
    """Errors related to syntax or input notation."""


class KumihanProcessingError(KumihanError):
    """Errors during parsing/processing/conversion pipeline."""


class KumihanFileError(KumihanError):
    """File I/O or filesystem related errors."""


class KumihanConfigError(KumihanError):
    """Configuration or environment related errors."""


__all__ = [
    "KumihanError",
    "KumihanSyntaxError",
    "KumihanProcessingError",
    "KumihanFileError",
    "KumihanConfigError",
]
