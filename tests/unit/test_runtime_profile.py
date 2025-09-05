import os
from typing import Dict

from kumihan_formatter.core.api.formatter_api import FormatterAPI


def _build_with_env(env: Dict[str, str]) -> FormatterAPI:
    old = {k: os.environ.get(k) for k in env}
    try:
        os.environ.update(env)
        return FormatterAPI()
    finally:
        # restore
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_runtime_profile_conservative_applies_overrides():
    api = _build_with_env({"KUMIHAN_PROFILE": "conservative"})
    pm = api.coordinator.processing_manager
    # Overrides should be visible in the instance config
    assert pm.config.get("large_parse_chunk_size") == 600
    assert pm.config.get("performance_monitoring") is False


def test_runtime_profile_aggressive_applies_overrides():
    api = _build_with_env({"KUMIHAN_PROFILE": "aggressive"})
    pm = api.coordinator.processing_manager
    assert pm.config.get("large_parse_chunk_size") == 2000
    assert pm.config.get("performance_monitoring") is True

