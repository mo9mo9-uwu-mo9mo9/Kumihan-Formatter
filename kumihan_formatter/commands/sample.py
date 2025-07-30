"""Sample command registration

This module provides command registration for sample commands.
"""

from .sample_command import SampleCommand, create_sample_command  # noqa: F401

# Re-export for backward compatibility
__all__ = ["create_sample_command", "SampleCommand"]
