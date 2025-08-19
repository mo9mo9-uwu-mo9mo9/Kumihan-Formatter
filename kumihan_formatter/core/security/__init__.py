"""
Kumihan-Formatter セキュリティモジュール

外部ライブラリとしての安全性を確保するためのセキュリティ機能群
- 入力検証・サニタイズ
- セキュアエラーハンドリング
- セキュアログ出力
- 脆弱性スキャナー・セキュリティ監査
"""

from .input_validation import SecureConfigManager, SecureInputValidator
from .secure_error_handling import (
    SecureErrorHandler,
    create_api_error_response,
    handle_error_safely,
    set_debug_mode,
)
from .secure_logging import SecureLogFilter, SecureLogFormatter, setup_secure_logging
from .vulnerability_scanner import (
    CVEDatabase,
    CVERecord,
    CodePatternScanner,
    DependencyScanner,
    RiskLevel,
    RuntimeMonitor,
    ScanResult,
    ScannerConfig,
    SecurityReport,
    VulnerabilityScanner,
    VulnerabilityType,
    quick_scan,
    scan_project,
)

__all__ = [
    # 入力検証
    "SecureInputValidator",
    "SecureConfigManager",
    # エラーハンドリング
    "SecureErrorHandler",
    "set_debug_mode",
    "handle_error_safely",
    "create_api_error_response",
    # ログ出力
    "SecureLogFormatter",
    "SecureLogFilter",
    "setup_secure_logging",
    # 脆弱性スキャナー
    "VulnerabilityScanner",
    "ScannerConfig",
    "ScanResult",
    "SecurityReport",
    "RiskLevel",
    "VulnerabilityType",
    "CVERecord",
    "DependencyScanner",
    "CodePatternScanner",
    "RuntimeMonitor",
    "CVEDatabase",
    "scan_project",
    "quick_scan",
]
