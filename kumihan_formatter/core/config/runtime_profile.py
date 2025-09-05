"""Runtime Profile configuration helpers.

Adds an opt-in environment-driven profile to tweak non-functional
behavior (chunk size, monitoring) without changing public APIs.

Profiles:
- conservative: prefer stability and smaller chunks.
- aggressive: prefer throughput with larger chunks and monitoring on.

This module is intentionally tiny and side-effect free so it can be
imported from configuration layers without heavy imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import os


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    overrides: Dict[str, object]


def _detect_profile_name() -> str | None:
    value = os.getenv("KUMIHAN_PROFILE")
    if not value:
        return None
    name = value.strip().lower()
    if name in {"conservative", "aggressive"}:
        return name
    return None


def get_runtime_profile() -> RuntimeProfile | None:
    name = _detect_profile_name()
    if not name:
        return None

    if name == "conservative":
        return RuntimeProfile(
            name=name,
            overrides={
                # Smaller chunks for lower memory usage
                "large_parse_chunk_size": 600,
                # Reduce overhead/noise
                "performance_monitoring": False,
            },
        )

    # aggressive
    return RuntimeProfile(
        name=name,
        overrides={
            # Larger chunks for throughput on big inputs
            "large_parse_chunk_size": 2000,
            # Keep monitoring enabled for tuning
            "performance_monitoring": True,
        },
    )


def get_profile_overrides() -> Dict[str, object]:
    profile = get_runtime_profile()
    return profile.overrides if profile else {}


__all__ = ["RuntimeProfile", "get_runtime_profile", "get_profile_overrides"]
