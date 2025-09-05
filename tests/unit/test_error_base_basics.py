"""KumihanError 基本挙動テスト"""

from kumihan_formatter.core.common.error_base import (
    KumihanError,
    ErrorSeverity,
    ErrorCategory,
)


def test_kumihan_error_to_dict_contains_traceback():
    try:
        raise ValueError("boom")
    except Exception as e:
        err = KumihanError(
            "failed",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
            original_error=e,
        )
    d = err.to_dict()
    assert d["severity"] == "error"
    assert d["category"] == "system"
    assert "traceback" in d

