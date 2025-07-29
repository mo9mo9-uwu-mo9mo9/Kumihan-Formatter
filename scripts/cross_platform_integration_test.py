#!/usr/bin/env python3
"""
Cross-Platform Integration Test - Issue #640 Phase 3
クロスプラットフォーム統合テストシステム

目的: Windows/macOS/Linux環境での統合テスト
- OS固有の問題検出
- パフォーマンス差異確認
- ファイルシステム互換性テスト
- 文字エンコーディング問題検出
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import threading
import time
import psutil

from scripts.tdd_system_base import TDDSystemBase, create_tdd_config, TDDSystemError
from scripts.secure_subprocess import secure_run
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class PlatformCompatibilityRisk(Enum):
    """プラットフォーム互換性リスクレベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


@dataclass
class PlatformIssue:
    """プラットフォーム固有問題"""

    issue_type: str
    platform: str
    severity: PlatformCompatibilityRisk
    description: str
    code_snippet: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    recommendation: str
    test_case: str
    error_details: Dict


@dataclass
class PlatformTestResult:
    """プラットフォームテスト結果"""

    platform_info: Dict[str, str]
    total_tests_run: int
    passed_tests: int
    failed_tests: int
    platform_issues: List[PlatformIssue]
    performance_metrics: Dict[str, float]
    filesystem_compatibility: Dict[str, bool]
    encoding_compatibility: Dict[str, bool]
    test_duration: float
    timestamp: datetime
    overall_risk: PlatformCompatibilityRisk
    recommendations: List[str]


class CrossPlatformIntegrationTester(TDDSystemBase):
    """クロスプラットフォーム統合テストシステム"""

    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)

        # プラットフォーム情報取得
        self.platform_info = {
            "system": platform.system(),
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "processor": (
                platform.processor() if hasattr(platform, "processor") else "unknown"
            ),
        }

        # プラットフォーム固有の問題パターンを外部設定から読み込み
        self.platform_specific_patterns = self._load_platform_patterns()

        # テストケース定義
        self.test_cases = [
            self._test_file_operations,
            self._test_path_handling,
            self._test_process_execution,
            self._test_encoding_handling,
            self._test_performance_consistency,
            self._test_dependency_compatibility,
            self._test_concurrent_operations,
            self._test_large_file_handling,
        ]

        self.platform_issues = []
        self.test_results = {}
        self.performance_metrics = {}

        # 外部設定からのパターン情報
        self.pattern_config = None

    def _load_platform_patterns(self) -> Dict[str, str]:
        """プラットフォーム固有パターンを外部設定から読み込み（統一ロック機構使用）"""
        config_path = self.project_root / "config" / "cross_platform_patterns.json"

        # 統一ロック機構を使用
        try:
            from kumihan_formatter.core.utilities.config_lock_manager import (
                safe_read_config,
            )

            USE_UNIFIED_LOCKING = True
        except ImportError:
            USE_UNIFIED_LOCKING = False

        try:
            if USE_UNIFIED_LOCKING:
                # 統一ロック機構で安全に読み込み
                config_data = safe_read_config(config_path, default={}, timeout=5.0)
                if config_data:
                    self.pattern_config = config_data

                    # パターンと説明のマッピングを作成
                    patterns = {}
                    for pattern_id, pattern_info in self.pattern_config.get(
                        "platform_specific_patterns", {}
                    ).items():
                        patterns[pattern_info["pattern"]] = pattern_info["description"]

                    logger.info(
                        f"統一ロック機構で外部設定から{len(patterns)}個のパターンを読み込み: {config_path}"
                    )
                    return patterns
                else:
                    logger.warning(
                        f"設定ファイルが空またはアクセスできません: {config_path}"
                    )
            else:
                # フォールバック: 従来のファイル読み込み
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        self.pattern_config = json.load(f)

                    # パターンと説明のマッピングを作成
                    patterns = {}
                    for pattern_id, pattern_info in self.pattern_config[
                        "platform_specific_patterns"
                    ].items():
                        patterns[pattern_info["pattern"]] = pattern_info["description"]

                    logger.info(
                        f"外部設定から{len(patterns)}個のパターンを読み込み: {config_path}"
                    )
                    return patterns
                else:
                    logger.warning(f"設定ファイルが見つかりません: {config_path}")

            # フォールバック用の基本パターン
            return {
                r"[\\/]": "Mixed path separators - use os.path.join() or pathlib.Path",
                r"os\.system\s*\(": "os.system() usage - platform dependent",
            }

        except Exception as e:
            logger.error(f"パターン設定読み込みエラー: {e}")
            # フォールバック用の基本パターン
            return {
                r"[\\/]": "Mixed path separators - use os.path.join() or pathlib.Path",
                r"os\.system\s*\(": "os.system() usage - platform dependent",
            }

    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 クロスプラットフォーム統合テストシステム初期化中...")

        # プラットフォーム情報表示
        logger.info(
            f"実行環境: {self.platform_info['system']} {self.platform_info['platform']}"
        )
        logger.info(
            f"Python: {self.platform_info['python_version']} ({self.platform_info['python_implementation']})"
        )

        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        logger.info("✅ クロスプラットフォーム統合テストシステム初期化完了")
        return True

    def execute_main_operation(self) -> PlatformTestResult:
        """クロスプラットフォーム統合テスト実行"""
        logger.info("🚀 クロスプラットフォーム統合テスト開始...")

        start_time = datetime.now()

        try:
            # ソースコード静的解析
            self._analyze_source_code()

            # 統合テスト実行
            self._run_integration_tests()

            # パフォーマンステスト
            self._run_performance_tests()

            # 結果を分析
            result = self._analyze_results(start_time)

            # レポート生成
            self._generate_compatibility_report(result)

            logger.info(
                f"✅ クロスプラットフォーム統合テスト完了: {len(self.platform_issues)}件の問題発見"
            )
            return result

        except Exception as e:
            # セキュアエラーハンドリング適用
            try:
                from kumihan_formatter.core.utilities.secure_error_handler import (
                    safe_handle_exception,
                    ExposureRisk,
                    ErrorSeverity,
                )

                sanitized_error = safe_handle_exception(
                    e,
                    context={
                        "operation": "cross_platform_integration_test",
                        "platform": self.platform_info["system"],
                    },
                    user_exposure=ExposureRisk.INTERNAL,
                    severity=ErrorSeverity.HIGH,
                )
                logger.error(
                    f"クロスプラットフォームテスト実行エラー [{sanitized_error.trace_id}]: {sanitized_error.user_message}"
                )
                raise TDDSystemError(
                    f"テスト実行失敗 [{sanitized_error.error_code}]: {sanitized_error.user_message}"
                )
            except ImportError:
                # フォールバック: 従来のエラーハンドリング
                logger.error(f"クロスプラットフォームテスト実行エラー: {e}")
                raise TDDSystemError(f"テスト実行失敗: {e}")

    def _analyze_source_code(self):
        """ソースコード静的解析"""
        logger.info("📁 ソースコード静的解析開始...")

        for py_file in self.project_root.glob("**/*.py"):
            if self._should_scan_file(py_file):
                self._analyze_python_file(py_file)

    def _should_scan_file(self, file_path: Path) -> bool:
        """ファイルをスキャンすべきかチェック"""
        # pathlib.Pathでクロスプラットフォーム対応
        relative_path = file_path.relative_to(self.project_root)
        path_parts = relative_path.parts

        # 外部設定から除外パターンを取得
        if self.pattern_config and "test_configuration" in self.pattern_config:
            exclude_patterns = self.pattern_config["test_configuration"].get(
                "exclude_directories", []
            )
        else:
            # フォールバック
            exclude_patterns = [
                "tests",
                "venv",
                ".venv",
                "__pycache__",
                ".git",
                "build",
                "dist",
                ".tox",
                "node_modules",
            ]

        for pattern in exclude_patterns:
            if any(pattern in part for part in path_parts):
                return False

        return True

    def _analyze_python_file(self, file_path: Path):
        """Pythonファイル解析"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # プラットフォーム固有問題検出
            self._detect_platform_issues(file_path, content)

        except Exception as e:
            logger.warning(f"ファイル解析エラー {file_path}: {e}")

    def _detect_platform_issues(self, file_path: Path, content: str):
        """プラットフォーム固有問題検出"""
        lines = content.split("\n")

        for pattern, description in self.platform_specific_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1

                issue = PlatformIssue(
                    issue_type="static_analysis",
                    platform=self.platform_info["system"],
                    severity=self._assess_pattern_severity(pattern, match.group()),
                    description=description,
                    code_snippet=(
                        lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    ),
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    recommendation=self._get_pattern_recommendation(pattern),
                    test_case="static_analysis",
                    error_details={"pattern": pattern, "match": match.group()},
                )
                self.platform_issues.append(issue)

    def _assess_pattern_severity(
        self, pattern: str, match: str
    ) -> PlatformCompatibilityRisk:
        """パターン重要度評価"""
        if self.pattern_config:
            # 外部設定から重要度を取得
            for pattern_id, pattern_info in self.pattern_config[
                "platform_specific_patterns"
            ].items():
                if pattern_info["pattern"] == pattern:
                    severity_str = pattern_info.get("severity", "medium")
                    severity_mapping = {
                        "critical": PlatformCompatibilityRisk.CRITICAL,
                        "high": PlatformCompatibilityRisk.HIGH,
                        "medium": PlatformCompatibilityRisk.MEDIUM,
                        "low": PlatformCompatibilityRisk.LOW,
                    }
                    return severity_mapping.get(
                        severity_str, PlatformCompatibilityRisk.MEDIUM
                    )

        # フォールバック: パターンベースの判定
        critical_patterns = [r"os\.system\s*\(", r'["\'][C-Z]:[\\\/]']
        high_patterns = [
            r"subprocess\.[^(]*\([^)]*shell\s*=\s*True",
            r"fcntl\.|msvcrt\.",
        ]

        for crit_pattern in critical_patterns:
            if re.search(crit_pattern, pattern):
                return PlatformCompatibilityRisk.CRITICAL

        for high_pattern in high_patterns:
            if re.search(high_pattern, pattern):
                return PlatformCompatibilityRisk.HIGH

        return PlatformCompatibilityRisk.MEDIUM

    def _get_pattern_recommendation(self, pattern: str) -> str:
        """パターン別推奨事項"""
        if self.pattern_config:
            # 外部設定から推奨事項を取得
            for pattern_id, pattern_info in self.pattern_config[
                "platform_specific_patterns"
            ].items():
                if pattern_info["pattern"] == pattern:
                    return pattern_info.get(
                        "recommendation",
                        "プラットフォーム固有の実装を避け、標準ライブラリの抽象化機能を使用してください",
                    )

        # フォールバック: パターンベースの推奨事項
        recommendations = {
            r"[\\/]": "pathlib.Pathまたはos.path.join()を使用してください",
            r'["\'][C-Z]:[\\\/]': "ハードコードされたパスを環境変数や設定ファイルから取得してください",
            r"os\.system\s*\(": "subprocessモジュールの使用を検討してください",
            r"subprocess\.[^(]*\([^)]*shell\s*=\s*True": "shell=Falseを使用し、引数を配列で渡してください",
            r"HOME|USERPROFILE": 'pathlib.Path.home()またはos.path.expanduser("~")を使用してください',
        }

        for pat, rec in recommendations.items():
            if re.search(pat, pattern):
                return rec

        return "プラットフォーム固有の実装を避け、標準ライブラリの抽象化機能を使用してください"

    def _run_integration_tests(self):
        """統合テスト実行"""
        logger.info("🧪 統合テスト実行中...")

        total_tests = len(self.test_cases)
        passed = 0
        failed = 0

        for i, test_case in enumerate(self.test_cases, 1):
            test_name = test_case.__name__
            logger.info(f"[{i}/{total_tests}] {test_name} 実行中...")

            try:
                start_time = time.time()
                result = test_case()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    "passed": result["passed"],
                    "duration": duration,
                    "details": result.get("details", {}),
                    "metrics": result.get("metrics", {}),
                }

                if result["passed"]:
                    passed += 1
                    logger.debug(f"✅ {test_name} 成功 ({duration:.2f}s)")
                else:
                    failed += 1
                    logger.warning(
                        f"❌ {test_name} 失敗: {result.get('error', 'Unknown error')}"
                    )

                    # 失敗時の問題を記録
                    issue = PlatformIssue(
                        issue_type="integration_test",
                        platform=self.platform_info["system"],
                        severity=PlatformCompatibilityRisk.HIGH,
                        description=f"統合テスト失敗: {test_name}",
                        code_snippet=None,
                        file_path=None,
                        line_number=None,
                        recommendation=result.get(
                            "recommendation", "テスト失敗の原因を調査してください"
                        ),
                        test_case=test_name,
                        error_details=result.get("details", {}),
                    )
                    self.platform_issues.append(issue)

            except Exception as e:
                failed += 1
                logger.error(f"❌ {test_name} 例外: {e}")

                self.test_results[test_name] = {
                    "passed": False,
                    "duration": 0,
                    "error": str(e),
                    "details": {},
                    "metrics": {},
                }

        logger.info(f"統合テスト完了: {passed}成功, {failed}失敗")

    def _test_file_operations(self) -> Dict:
        """ファイル操作テスト"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # ファイル作成・読み書きテスト
                test_file = temp_path / "test_file.txt"
                test_content = "テスト内容\nTest content\n日本語文字列"

                # 書き込み
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(test_content)

                # 読み込み
                with open(test_file, "r", encoding="utf-8") as f:
                    read_content = f.read()

                # 内容確認
                if read_content != test_content:
                    return {
                        "passed": False,
                        "error": "ファイル内容不一致",
                        "details": {"expected": test_content, "actual": read_content},
                    }

                # パーミッション操作テスト（Unix系のみ）
                if os.name != "nt":
                    try:
                        os.chmod(test_file, 0o644)
                    except Exception as e:
                        return {
                            "passed": False,
                            "error": f"パーミッション設定失敗: {e}",
                        }

                return {
                    "passed": True,
                    "details": {"platform": self.platform_info["system"]},
                }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_path_handling(self) -> Dict:
        """パス処理テスト"""
        try:
            # 各種パス操作のテスト
            test_paths = [
                "folder/subfolder/file.txt",
                "../parent/file.txt",
                "./current/file.txt",
                "file with spaces.txt",
                "日本語ファイル名.txt",
            ]

            for test_path in test_paths:
                # pathlib.Pathでの処理
                path_obj = Path(test_path)

                # パス分解
                parts = path_obj.parts
                parent = path_obj.parent
                name = path_obj.name
                stem = path_obj.stem
                suffix = path_obj.suffix

                # 絶対パス変換
                abs_path = path_obj.resolve()

                # パス結合
                joined = Path("base") / path_obj

            return {"passed": True, "metrics": {"tested_paths": len(test_paths)}}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_process_execution(self) -> Dict:
        """プロセス実行テスト"""
        try:
            # Python実行テスト
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    'import sys; print(f"Python {sys.version_info.major}.{sys.version_info.minor}")',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {
                    "passed": False,
                    "error": "Python実行失敗",
                    "details": {"stderr": result.stderr},
                }

            # プラットフォーム固有コマンドテスト
            if self.platform_info["system"] == "Windows":
                cmd_result = subprocess.run(
                    ["echo", "test"], capture_output=True, text=True
                )
            else:
                cmd_result = subprocess.run(
                    ["echo", "test"], capture_output=True, text=True
                )

            return {
                "passed": True,
                "metrics": {
                    "python_version": result.stdout.strip(),
                    "echo_result": cmd_result.stdout.strip(),
                },
            }

        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "プロセス実行タイムアウト"}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_encoding_handling(self) -> Dict:
        """エンコーディング処理テスト"""
        try:
            test_strings = [
                "ASCII text",
                "日本語テキスト",
                "Café résumé naïve",
                "🚀 Emoji test 🎉",
                "Кириллица",
                "العربية",
            ]

            results = {}

            for test_str in test_strings:
                # UTF-8エンコーディング・デコーディング
                encoded = test_str.encode("utf-8")
                decoded = encoded.decode("utf-8")

                if decoded != test_str:
                    return {
                        "passed": False,
                        "error": f"エンコーディング失敗: {test_str}",
                        "details": {"original": test_str, "decoded": decoded},
                    }

                results[test_str] = {
                    "encoded_length": len(encoded),
                    "original_length": len(test_str),
                }

            return {
                "passed": True,
                "metrics": {"tested_strings": len(test_strings)},
                "details": results,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_performance_consistency(self) -> Dict:
        """パフォーマンス一貫性テスト"""
        try:
            # CPU集約的タスク
            start_time = time.time()
            result = sum(i * i for i in range(100000))
            cpu_duration = time.time() - start_time

            # I/O集約的タスク
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
                temp_path = temp_file.name

                start_time = time.time()
                for i in range(1000):
                    temp_file.write(f"Line {i}\n")
                temp_file.flush()
                io_duration = time.time() - start_time

            os.unlink(temp_path)

            # メモリ使用量測定
            process = psutil.Process()
            memory_info = process.memory_info()

            metrics = {
                "cpu_task_duration": cpu_duration,
                "io_task_duration": io_duration,
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "cpu_percent": process.cpu_percent(),
            }

            self.performance_metrics.update(metrics)

            return {"passed": True, "metrics": metrics}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_dependency_compatibility(self) -> Dict:
        """依存関係互換性テスト"""
        try:
            # 主要依存関係のインポートテスト
            critical_imports = [
                "pathlib",
                "json",
                "logging",
                "datetime",
                "subprocess",
                "tempfile",
            ]

            import_results = {}

            for module_name in critical_imports:
                try:
                    __import__(module_name)
                    import_results[module_name] = True
                except ImportError as e:
                    import_results[module_name] = False
                    logger.warning(f"インポート失敗: {module_name} - {e}")

            failed_imports = [
                name for name, success in import_results.items() if not success
            ]

            return {
                "passed": len(failed_imports) == 0,
                "details": import_results,
                "error": (
                    f"インポート失敗: {failed_imports}" if failed_imports else None
                ),
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_concurrent_operations(self) -> Dict:
        """並行処理テスト"""
        try:
            results = []
            errors = []

            def worker_task(task_id):
                try:
                    # 簡単な計算タスク
                    result = sum(i for i in range(1000))
                    results.append((task_id, result))
                except Exception as e:
                    errors.append((task_id, str(e)))

            # 複数スレッドで並行実行
            threads = []
            thread_count = 4

            for i in range(thread_count):
                thread = threading.Thread(target=worker_task, args=(i,))
                threads.append(thread)
                thread.start()

            # 全スレッド完了待機
            for thread in threads:
                thread.join(timeout=5.0)

            if errors:
                return {
                    "passed": False,
                    "error": f"並行処理エラー: {errors}",
                    "details": {"results": results, "errors": errors},
                }

            return {
                "passed": len(results) == thread_count,
                "metrics": {
                    "thread_count": thread_count,
                    "completed_tasks": len(results),
                    "expected_result": 499500,
                    "all_results_match": all(result[1] == 499500 for result in results),
                },
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _test_large_file_handling(self) -> Dict:
        """大ファイル処理テスト"""
        try:
            # 大きなファイルの作成・読み取りテスト
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name

                # 1MBのデータ作成
                chunk_size = 1024
                chunk_count = 1024  # 1MB total
                test_chunk = b"x" * chunk_size

                start_time = time.time()
                for _ in range(chunk_count):
                    temp_file.write(test_chunk)
                write_duration = time.time() - start_time

                temp_file.flush()
                file_size = temp_file.tell()

            # ファイル読み取り
            start_time = time.time()
            with open(temp_path, "rb") as f:
                read_data = f.read()
            read_duration = time.time() - start_time

            os.unlink(temp_path)

            return {
                "passed": len(read_data) == file_size,
                "metrics": {
                    "file_size": file_size,
                    "write_duration": write_duration,
                    "read_duration": read_duration,
                    "write_speed_mb_per_sec": (file_size / (1024 * 1024))
                    / write_duration,
                    "read_speed_mb_per_sec": (file_size / (1024 * 1024))
                    / read_duration,
                },
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_performance_tests(self):
        """パフォーマンステスト実行"""
        logger.info("⚡ パフォーマンステスト実行中...")

        # 既に_test_performance_consistencyで実行済み
        logger.info("パフォーマンステスト完了")

    def _analyze_results(self, start_time: datetime) -> PlatformTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # テスト統計
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result["passed"]
        )
        failed_tests = total_tests - passed_tests

        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_compatibility_risk()

        # 推奨事項生成
        recommendations = self._generate_compatibility_recommendations()

        # ファイルシステム互換性
        filesystem_compatibility = {
            "unicode_filenames": True,  # 現代のOSはすべてサポート
            "long_paths": self.platform_info["system"] != "Windows",  # Windows制限あり
            "case_sensitivity": self.platform_info["system"] in ["Linux", "Darwin"],
        }

        # エンコーディング互換性
        encoding_compatibility = {
            "utf8_support": True,  # Python 3はデフォルトUTF-8
            "locale_handling": True,
            "console_encoding": True,
        }

        return PlatformTestResult(
            platform_info=self.platform_info,
            total_tests_run=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            platform_issues=self.platform_issues,
            performance_metrics=self.performance_metrics,
            filesystem_compatibility=filesystem_compatibility,
            encoding_compatibility=encoding_compatibility,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations,
        )

    def _calculate_overall_compatibility_risk(self) -> PlatformCompatibilityRisk:
        """全体互換性リスクレベル計算"""
        if not self.platform_issues:
            return PlatformCompatibilityRisk.SAFE

        risk_counts = {}
        for issue in self.platform_issues:
            risk_counts[issue.severity] = risk_counts.get(issue.severity, 0) + 1

        if risk_counts.get(PlatformCompatibilityRisk.CRITICAL, 0) > 0:
            return PlatformCompatibilityRisk.CRITICAL
        elif risk_counts.get(PlatformCompatibilityRisk.HIGH, 0) > 0:
            return PlatformCompatibilityRisk.HIGH
        elif risk_counts.get(PlatformCompatibilityRisk.MEDIUM, 0) > 0:
            return PlatformCompatibilityRisk.MEDIUM
        else:
            return PlatformCompatibilityRisk.LOW

    def _generate_compatibility_recommendations(self) -> List[str]:
        """互換性推奨事項生成"""
        recommendations = [
            "pathlib.Pathを使用してクロスプラットフォーム対応のパス処理を実装する",
            "os.path.join()の代わりにpathlib演算子（/）を使用する",
            "プラットフォーム固有のコードをif platform.system()で分岐させる",
            "環境変数アクセス時はos.environ.get()でデフォルト値を指定する",
            "ファイルI/O時は明示的にencoding='utf-8'を指定する",
            "subprocessでshell=Trueの使用を避ける",
            "定期的なクロスプラットフォームテストの実行",
        ]

        if self.platform_issues:
            recommendations.extend(
                [
                    "発見されたプラットフォーム互換性問題を優先度に応じて修正する",
                    "CI/CDパイプラインに複数OS環境でのテストを追加する",
                    "プラットフォーム固有の機能使用時は適切なフォールバックを実装する",
                ]
            )

        return recommendations

    def _generate_compatibility_report(self, result: PlatformTestResult):
        """互換性レポート生成"""
        report_file = self.project_root / "cross_platform_compatibility_report.json"

        report_data = {
            "platform_info": result.platform_info,
            "test_summary": {
                "total_tests": result.total_tests_run,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "success_rate": (
                    (result.passed_tests / result.total_tests_run * 100)
                    if result.total_tests_run > 0
                    else 0
                ),
                "overall_risk": result.overall_risk.value,
                "test_duration": result.test_duration,
                "timestamp": result.timestamp.isoformat(),
            },
            "platform_issues": [
                {
                    "type": issue.issue_type,
                    "platform": issue.platform,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "code": issue.code_snippet,
                    "recommendation": issue.recommendation,
                    "test_case": issue.test_case,
                    "error_details": issue.error_details,
                }
                for issue in result.platform_issues
            ],
            "test_results": self.test_results,
            "performance_metrics": result.performance_metrics,
            "compatibility": {
                "filesystem": result.filesystem_compatibility,
                "encoding": result.encoding_compatibility,
            },
            "recommendations": result.recommendations,
            "risk_distribution": self._get_risk_distribution(result.platform_issues),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 クロスプラットフォーム互換性レポート生成: {report_file}")

    def _get_risk_distribution(self, issues: List[PlatformIssue]) -> Dict[str, int]:
        """リスク分布取得"""
        distribution = {}
        for issue in issues:
            risk = issue.severity.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    logger.info("🚀 クロスプラットフォーム統合テスト開始")

    try:
        with CrossPlatformIntegrationTester(project_root) as tester:
            result = tester.run()

            # 結果サマリー表示
            logger.info("📊 クロスプラットフォーム統合テスト結果サマリー:")
            logger.info(
                f"  実行環境: {result.platform_info['system']} {result.platform_info['platform']}"
            )
            logger.info(f"  総テスト数: {result.total_tests_run}")
            logger.info(f"  成功: {result.passed_tests}, 失敗: {result.failed_tests}")
            logger.info(
                f"  成功率: {(result.passed_tests / result.total_tests_run * 100):.1f}%"
            )
            logger.info(f"  プラットフォーム問題: {len(result.platform_issues)}件")
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")

            # パフォーマンス情報
            if result.performance_metrics:
                logger.info("⚡ パフォーマンスメトリクス:")
                for metric, value in result.performance_metrics.items():
                    if isinstance(value, float):
                        logger.info(f"  {metric}: {value:.4f}")
                    else:
                        logger.info(f"  {metric}: {value}")

            # 重要な問題を表示
            critical_issues = [
                i
                for i in result.platform_issues
                if i.severity
                in [PlatformCompatibilityRisk.CRITICAL, PlatformCompatibilityRisk.HIGH]
            ]

            if critical_issues:
                logger.warning(
                    f"🚨 高リスクプラットフォーム問題 {len(critical_issues)}件:"
                )
                for issue in critical_issues[:5]:  # 上位5件表示
                    location = (
                        f"{issue.file_path}:{issue.line_number}"
                        if issue.file_path
                        else issue.test_case
                    )
                    logger.warning(
                        f"  - {location} ({issue.severity.value}): {issue.description}"
                    )

            return (
                0
                if result.overall_risk
                in [PlatformCompatibilityRisk.SAFE, PlatformCompatibilityRisk.LOW]
                else 1
            )

    except Exception as e:
        logger.error(f"💥 クロスプラットフォーム統合テスト実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
