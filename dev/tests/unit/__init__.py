"""Property-based testing for Kumihan-Formatter

This package contains property-based tests using hypothesis to find edge cases
and verify system properties across a wide range of inputs.

Note: These tests require the 'hypothesis' package to be installed.
If not available, the tests will be skipped gracefully.
"""

try:
    import hypothesis
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

__all__ = ['HAS_HYPOTHESIS']