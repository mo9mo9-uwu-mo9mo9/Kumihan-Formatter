"""Sample and test command registration

This module provides command registration for sample and test commands.
"""

from .sample_command import create_sample_command  # noqa: F401
from .test_file_command import create_test_command  # noqa: F401

# Re-export for backward compatibility
__all__ = ["create_sample_command", "create_test_command"]

