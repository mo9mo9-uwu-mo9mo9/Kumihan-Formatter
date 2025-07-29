#!/usr/bin/env python3
"""
Unified Security Scanner - Issue #643 Medium Priority Issue対応
重複スキャンロジック統合とメモリリーク対策

目的: 複数のセキュリティテストシステムで重複していたファイルスキャンロジックを統合
- 統一されたファイルスキャン機能
- メモリ効率的な脆弱性リスト管理
- セキュアなエラーメッセージ制御
"""

import ast
import gc
import weakref
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Iterator, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from collections import deque

from kumihan_formatter.core.utilities.logger import get_logger

# 統合システムからインポート
try:
    from kumihan_formatter.core.utilities.ast_performance_optimizer import (
        parse_file_fast,
        get_ast_optimizer,
    )
    from kumihan_formatter.core.utilities.secure_error_handler import (
        safe_handle_exception,
        ExposureRisk,
        ErrorSeverity,
    )
    from kumihan_formatter.core.utilities.config_lock_manager import safe_read_config

    USE_INTEGRATED_SYSTEMS = True
except ImportError:
    USE_INTEGRATED_SYSTEMS = False

logger = get_logger(__name__)


class ScannerType(Enum):
    """スキャナー種別"""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PLATFORM_COMPAT = "platform_compat"
    DEPENDENCY = "dependency"
    GENERIC = "generic"


class VulnerabilityLevel(Enum):
    """脆弱性レベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """統一セキュリティ検出結果"""

    scanner_type: ScannerType
    vulnerability_type: str
    level: VulnerabilityLevel
    file_path: Path
    line_number: Optional[int]
    function_name: Optional[str]
    code_snippet: Optional[str]
    description: str
    recommendation: str
    confidence_score: float  # 0.0-1.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScanResult:
    """スキャン結果サマリー"""

    scanner_type: ScannerType
    total_files_scanned: int
    total_functions_scanned: int
    findings: List[SecurityFinding]
    scan_duration: float
    memory_usage_mb: float
    timestamp: datetime


class MemoryEfficientFindingsList:
    """メモリ効率的な検出結果リスト（メモリリーク対策）"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._findings = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._weak_refs: Set[weakref.ref] = set()

    def add_finding(self, finding: SecurityFinding):
        """検出結果追加（メモリ制限付き）"""
        with self._lock:
            # 古い結果を自動削除
            if len(self._findings) >= self.max_size:
                removed = self._findings.popleft()
                logger.debug(f"古い検出結果を削除: {removed.vulnerability_type}")

            self._findings.append(finding)

            # 弱参照でメモリリーク監視
            def cleanup_callback(ref):
                self._weak_refs.discard(ref)

            ref = weakref.ref(finding, cleanup_callback)
            self._weak_refs.add(ref)

    def get_findings(self, limit: Optional[int] = None) -> List[SecurityFinding]:
        """検出結果取得"""
        with self._lock:
            if limit:
                return list(self._findings)[-limit:]
            return list(self._findings)

    def clear(self):
        """検出結果クリア"""
        with self._lock:
            self._findings.clear()
            self._weak_refs.clear()
            gc.collect()  # 強制ガベージコレクション

    def get_memory_info(self) -> Dict[str, Any]:
        """メモリ使用状況取得"""
        with self._lock:
            alive_refs = len([ref for ref in self._weak_refs if ref() is not None])
            return {
                "current_findings": len(self._findings),
                "max_size": self.max_size,
                "alive_references": alive_refs,
                "memory_pressure": len(self._findings) / self.max_size,
            }


class UnifiedSecurityScanner:
    """統一セキュリティスキャナー"""

    def __init__(self, project_root: Path, config_path: Optional[Path] = None):
        """初期化"""
        self.project_root = Path(project_root)
        self.config_path = (
            config_path or self.project_root / "config" / "unified_scanner.json"
        )
        self.config = self._load_config()

        # メモリ効率的な検出結果管理
        max_findings = self.config.get("memory_management", {}).get(
            "max_findings", 1000
        )
        self.findings_list = MemoryEfficientFindingsList(max_findings)

        # スキャンターゲット設定
        self.scan_patterns = self.config.get("scan_patterns", ["**/*.py"])
        self.exclude_patterns = self.config.get(
            "exclude_patterns",
            [
                "tests/",
                "venv/",
                ".venv/",
                "__pycache__/",
                ".git/",
                "build/",
                "dist/",
                ".tox/",
                "node_modules/",
            ],
        )

        # パフォーマンス追跡
        self.scan_metrics = {
            "files_scanned": 0,
            "functions_scanned": 0,
            "total_scan_time": 0.0,
            "memory_peak": 0,
        }

        logger.info(f"統一セキュリティスキャナー初期化完了: {self.project_root}")

    def _load_config(self) -> Dict[str, Any]:
        """設定読み込み"""
        if USE_INTEGRATED_SYSTEMS:
            try:
                return safe_read_config(self.config_path, default={}, timeout=3.0)
            except Exception:
                pass

        # デフォルト設定
        return {
            "scan_patterns": ["**/*.py"],
            "exclude_patterns": [
                "tests/",
                "venv/",
                ".venv/",
                "__pycache__/",
                ".git/",
                "build/",
                "dist/",
                ".tox/",
                "node_modules/",
            ],
            "memory_management": {
                "max_findings": 1000,
                "gc_interval": 100,
                "enable_memory_monitoring": True,
            },
            "error_handling": {
                "exposure_level": "internal",
                "log_detailed_errors": True,
                "sanitize_error_messages": True,
            },
            "performance": {
                "enable_parallel_scanning": True,
                "max_workers": "auto",
                "timeout_per_file": 30,
            },
        }

    def scan_files_for_vulnerabilities(
        self,
        scanner_type: ScannerType,
        vulnerability_patterns: Dict[str, str],
        custom_analyzer: Optional[
            Callable[[ast.AST, Path, str], List[SecurityFinding]]
        ] = None,
    ) -> ScanResult:
        """統一ファイルスキャン実行"""

        start_time = datetime.now()
        files_scanned = 0
        functions_scanned = 0

        try:
            # スキャン対象ファイル収集
            target_files = self._collect_target_files()

            if USE_INTEGRATED_SYSTEMS:
                # AST最適化システム使用
                optimizer = get_ast_optimizer()

                # 並列処理対応
                if self.config.get("performance", {}).get(
                    "enable_parallel_scanning", True
                ):
                    ast_results = optimizer.parse_files_parallel(target_files)
                else:
                    ast_results = {
                        f: optimizer.parse_file_optimized(f) for f in target_files
                    }
            else:
                # フォールバック: 従来のAST解析
                ast_results = {}
                for file_path in target_files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        ast_results[file_path] = ast.parse(content)
                    except Exception:
                        ast_results[file_path] = None

            # AST解析結果をスキャン
            for file_path, ast_tree in ast_results.items():
                files_scanned += 1

                if ast_tree is None:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # カスタムアナライザー使用
                    if custom_analyzer:
                        findings = custom_analyzer(ast_tree, file_path, content)
                        for finding in findings:
                            self.findings_list.add_finding(finding)
                    else:
                        # デフォルト解析
                        findings = self._analyze_ast_for_patterns(
                            ast_tree,
                            file_path,
                            content,
                            scanner_type,
                            vulnerability_patterns,
                        )
                        for finding in findings:
                            self.findings_list.add_finding(finding)

                    # 関数数をカウント
                    for node in ast.walk(ast_tree):
                        if isinstance(node, ast.FunctionDef):
                            functions_scanned += 1

                    # 定期的なガベージコレクション
                    if (
                        files_scanned
                        % self.config.get("memory_management", {}).get(
                            "gc_interval", 100
                        )
                        == 0
                    ):
                        gc.collect()

                except Exception as e:
                    if USE_INTEGRATED_SYSTEMS:
                        # セキュアエラーハンドリング
                        sanitized_error = safe_handle_exception(
                            e,
                            context={
                                "file_path": str(file_path),
                                "scanner_type": scanner_type.value,
                            },
                            user_exposure=ExposureRisk.INTERNAL,
                            severity=ErrorSeverity.LOW,
                        )
                        logger.debug(
                            f"ファイルスキャンエラー [{sanitized_error.trace_id}]: {sanitized_error.user_message}"
                        )
                    else:
                        logger.debug(f"ファイルスキャンエラー: {file_path} - {e}")

            # 結果作成
            end_time = datetime.now()
            scan_duration = (end_time - start_time).total_seconds()

            # メモリ使用量測定
            import psutil

            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            # メトリクス更新
            self.scan_metrics.update(
                {
                    "files_scanned": files_scanned,
                    "functions_scanned": functions_scanned,
                    "total_scan_time": scan_duration,
                    "memory_peak": max(self.scan_metrics["memory_peak"], memory_usage),
                }
            )

            result = ScanResult(
                scanner_type=scanner_type,
                total_files_scanned=files_scanned,
                total_functions_scanned=functions_scanned,
                findings=self.findings_list.get_findings(),
                scan_duration=scan_duration,
                memory_usage_mb=memory_usage,
                timestamp=end_time,
            )

            logger.info(
                f"統一スキャン完了 ({scanner_type.value}): {files_scanned}ファイル, {len(result.findings)}件検出"
            )
            return result

        except Exception as e:
            if USE_INTEGRATED_SYSTEMS:
                sanitized_error = safe_handle_exception(
                    e,
                    context={
                        "scanner_type": scanner_type.value,
                        "project_root": str(self.project_root),
                    },
                    user_exposure=ExposureRisk.INTERNAL,
                    severity=ErrorSeverity.HIGH,
                )
                logger.error(
                    f"統一スキャンエラー [{sanitized_error.trace_id}]: {sanitized_error.user_message}"
                )
                raise Exception(
                    f"スキャン実行失敗 [{sanitized_error.error_code}]: {sanitized_error.user_message}"
                )
            else:
                logger.error(f"統一スキャンエラー: {e}")
                raise

    def _collect_target_files(self) -> List[Path]:
        """スキャン対象ファイル収集"""
        target_files = []

        for pattern in self.scan_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._should_scan_file(file_path):
                    target_files.append(file_path)

        return target_files

    def _should_scan_file(self, file_path: Path) -> bool:
        """ファイルスキャン対象判定"""
        file_str = str(file_path.relative_to(self.project_root))

        for exclude_pattern in self.exclude_patterns:
            if exclude_pattern in file_str:
                return False

        return True

    def _analyze_ast_for_patterns(
        self,
        ast_tree: ast.AST,
        file_path: Path,
        content: str,
        scanner_type: ScannerType,
        patterns: Dict[str, str],
    ) -> List[SecurityFinding]:
        """AST解析によるパターン検出"""

        findings = []
        lines = content.split("\n")

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                # 関数レベルの解析
                func_start = getattr(node, "lineno", 1)
                func_end = getattr(node, "end_lineno", func_start)
                func_content = "\n".join(lines[func_start - 1 : func_end])

                # パターンマッチング
                for pattern, description in patterns.items():
                    import re

                    if re.search(pattern, func_content, re.IGNORECASE):
                        finding = SecurityFinding(
                            scanner_type=scanner_type,
                            vulnerability_type=description,
                            level=VulnerabilityLevel.MEDIUM,
                            file_path=file_path,
                            line_number=func_start,
                            function_name=node.name,
                            code_snippet=(
                                func_content[:200] + "..."
                                if len(func_content) > 200
                                else func_content
                            ),
                            description=f"潜在的脆弱性パターン検出: {description}",
                            recommendation="コードレビューと適切な対策の実装を推奨",
                            confidence_score=0.7,
                        )
                        findings.append(finding)

        return findings

    def get_scan_statistics(self) -> Dict[str, Any]:
        """スキャン統計情報取得"""
        memory_info = self.findings_list.get_memory_info()

        return {
            "scan_metrics": self.scan_metrics,
            "memory_info": memory_info,
            "config_loaded": self.config_path.exists() if self.config_path else False,
            "integrated_systems_available": USE_INTEGRATED_SYSTEMS,
            "current_findings_count": len(self.findings_list.get_findings()),
        }

    def clear_findings(self):
        """検出結果クリア"""
        self.findings_list.clear()
        logger.info("検出結果をクリアしました")


# グローバルインスタンス管理
_scanner_instances: Dict[Path, UnifiedSecurityScanner] = {}
_scanner_lock = threading.Lock()


def get_unified_scanner(project_root: Path) -> UnifiedSecurityScanner:
    """統一スキャナーインスタンス取得"""
    with _scanner_lock:
        if project_root not in _scanner_instances:
            _scanner_instances[project_root] = UnifiedSecurityScanner(project_root)
        return _scanner_instances[project_root]


# 便利な関数群
def scan_for_sql_injection(project_root: Path, patterns: Dict[str, str]) -> ScanResult:
    """SQLインジェクションスキャン（関数版）"""
    scanner = get_unified_scanner(project_root)
    return scanner.scan_files_for_vulnerabilities(ScannerType.SQL_INJECTION, patterns)


def scan_for_xss(project_root: Path, patterns: Dict[str, str]) -> ScanResult:
    """XSSスキャン（関数版）"""
    scanner = get_unified_scanner(project_root)
    return scanner.scan_files_for_vulnerabilities(ScannerType.XSS, patterns)


def scan_for_platform_issues(
    project_root: Path, patterns: Dict[str, str]
) -> ScanResult:
    """プラットフォーム互換性スキャン（関数版）"""
    scanner = get_unified_scanner(project_root)
    return scanner.scan_files_for_vulnerabilities(ScannerType.PLATFORM_COMPAT, patterns)
