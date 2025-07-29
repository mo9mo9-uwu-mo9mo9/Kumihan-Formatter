#!/usr/bin/env python3
"""
TDD Automation System - Issue #640 Phase 1
テスト自動化システム

目的: Test-Driven Development完全自動化
- ファイル変更監視 → 自動テスト実行
- テスト結果リアルタイム表示
- 品質ゲート自動チェック
- CI/CD統合
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import threading
from queue import Queue
import signal

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AutoTestConfig:
    """自動テスト設定"""

    watch_patterns: List[str]
    test_patterns: List[str]
    quality_gate_enabled: bool = True
    continuous_integration: bool = True
    notification_enabled: bool = True
    debounce_seconds: float = 2.0


@dataclass
class TestEvent:
    """テストイベント"""

    event_type: str  # "file_change", "test_run", "quality_gate"
    file_path: Optional[Path] = None
    timestamp: datetime = None
    details: Dict = None


class TDDAutomation:
    """TDD自動化システム"""

    def __init__(self, config: AutoTestConfig, project_root: Path):
        self.config = config
        self.project_root = project_root
        self.event_queue = Queue()
        self.running = False
        self.last_run_time = 0
        self.test_history = []

        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def start_automation(self):
        """自動化システム開始"""
        logger.info("🤖 TDD自動化システムを開始...")
        self.running = True

        # ファイル監視スレッド開始
        watch_thread = threading.Thread(target=self._file_watcher, daemon=True)
        watch_thread.start()

        # イベント処理スレッド開始
        event_thread = threading.Thread(target=self._event_processor, daemon=True)
        event_thread.start()

        logger.info("✅ TDD自動化システム開始完了")
        logger.info("📂 監視対象: " + ", ".join(self.config.watch_patterns))

        try:
            # メインループ
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            self._shutdown()

    def _file_watcher(self):
        """ファイル変更監視"""
        logger.info("👀 ファイル監視を開始...")

        watched_files = self._get_watched_files()
        file_timestamps = {f: f.stat().st_mtime for f in watched_files if f.exists()}

        while self.running:
            try:
                current_watched = self._get_watched_files()
                current_timestamps = {
                    f: f.stat().st_mtime for f in current_watched if f.exists()
                }

                # 変更検出
                changed_files = []

                # 新規ファイル検出
                new_files = set(current_timestamps.keys()) - set(file_timestamps.keys())
                changed_files.extend(new_files)

                # 変更ファイル検出
                for file_path, current_time in current_timestamps.items():
                    if file_path in file_timestamps:
                        if current_time > file_timestamps[file_path]:
                            changed_files.append(file_path)

                # 変更があった場合イベント送出
                if changed_files:
                    for file_path in changed_files:
                        event = TestEvent(
                            event_type="file_change",
                            file_path=file_path,
                            timestamp=datetime.now(),
                            details={"change_type": "modified"},
                        )
                        self.event_queue.put(event)
                        logger.info(f"📝 ファイル変更検出: {file_path.name}")

                file_timestamps = current_timestamps
                time.sleep(1)  # 1秒間隔で監視

            except Exception as e:
                logger.error(f"ファイル監視エラー: {e}")
                time.sleep(5)

    def _get_watched_files(self) -> Set[Path]:
        """監視対象ファイル取得"""
        watched_files = set()

        for pattern in self.config.watch_patterns:
            matched_files = self.project_root.glob(pattern)
            watched_files.update(matched_files)

        return watched_files

    def _event_processor(self):
        """イベント処理"""
        logger.info("⚡ イベント処理を開始...")

        while self.running:
            try:
                if not self.event_queue.empty():
                    event = self.event_queue.get(timeout=1)
                    self._handle_event(event)
                else:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"イベント処理エラー: {e}")
                time.sleep(1)

    def _handle_event(self, event: TestEvent):
        """個別イベント処理"""
        current_time = time.time()

        # デバウンス処理
        if current_time - self.last_run_time < self.config.debounce_seconds:
            logger.debug(f"デバウンス中: {event.event_type}")
            return

        if event.event_type == "file_change":
            self._handle_file_change(event)

        self.last_run_time = current_time

    def _handle_file_change(self, event: TestEvent):
        """ファイル変更処理"""
        logger.info(f"🔄 ファイル変更対応: {event.file_path.name}")

        # 1. 関連テスト特定
        related_tests = self._find_related_tests(event.file_path)

        if related_tests:
            # 2. 関連テストのみ実行
            self._run_targeted_tests(related_tests)
        else:
            # 3. 関連テストがない場合は全テスト実行
            logger.warning(f"関連テストが見つかりません: {event.file_path}")
            if self._should_run_full_tests(event.file_path):
                self._run_full_tests()

    def _find_related_tests(self, file_path: Path) -> List[Path]:
        """関連テスト特定"""
        related_tests = []

        # 1. 直接対応するテストファイル
        module_name = file_path.stem
        for test_pattern in self.config.test_patterns:
            test_files = self.project_root.glob(test_pattern.format(module=module_name))
            related_tests.extend(test_files)

        # 2. パッケージレベルのテスト
        if file_path.parent.name != "kumihan_formatter":
            package_tests = self.project_root.glob(
                f"tests/**/test_{file_path.parent.name}*.py"
            )
            related_tests.extend(package_tests)

        # 3. 統合テスト（重要ファイルの場合）
        if self._is_critical_file(file_path):
            integration_tests = self.project_root.glob("tests/integration/**/*.py")
            related_tests.extend(integration_tests)

        return list(set(related_tests))

    def _is_critical_file(self, file_path: Path) -> bool:
        """重要ファイル判定"""
        critical_patterns = [
            "kumihan_formatter/core/parser/**",
            "kumihan_formatter/core/renderer/**",
            "kumihan_formatter/commands/**",
        ]

        for pattern in critical_patterns:
            if file_path.match(pattern):
                return True
        return False

    def _should_run_full_tests(self, file_path: Path) -> bool:
        """全テスト実行判定"""
        # 設定ファイルや重要なファイルの場合
        important_files = [
            "pyproject.toml",
            "CLAUDE.md",
            "__init__.py",
        ]

        return file_path.name in important_files or self._is_critical_file(file_path)

    def _run_targeted_tests(self, test_files: List[Path]):
        """対象テスト実行"""
        logger.info(f"🎯 対象テスト実行: {len(test_files)}ファイル")

        test_paths = [str(test_file) for test_file in test_files]

        start_time = datetime.now()

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            *test_paths,
            "--tb=short",
            "-v",
            "--no-header",
        ]

        if self.config.quality_gate_enabled:
            cmd.extend(
                [
                    "--cov=kumihan_formatter",
                    "--cov-report=term-missing:skip-covered",
                ]
            )

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = (datetime.now() - start_time).total_seconds()

        self._process_test_result(result, duration, "targeted")

    def _run_full_tests(self):
        """全テスト実行"""
        logger.info("🔄 全テスト実行開始...")

        start_time = datetime.now()

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--tb=short",
            "-v",
            "--maxfail=5",
        ]

        if self.config.quality_gate_enabled:
            cmd.extend(
                [
                    "--cov=kumihan_formatter",
                    "--cov-report=term-missing:skip-covered",
                    "--cov-fail-under=70",
                ]
            )

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = (datetime.now() - start_time).total_seconds()

        self._process_test_result(result, duration, "full")

    def _process_test_result(
        self, result: subprocess.CompletedProcess, duration: float, test_type: str
    ):
        """テスト結果処理"""
        success = result.returncode == 0

        # 結果解析
        output_lines = result.stdout.split("\n")
        summary_line = [
            line for line in output_lines if "passed" in line and "failed" in line
        ]

        test_summary = summary_line[0] if summary_line else "結果不明"

        # ログ出力
        if success:
            logger.info(f"✅ {test_type}テスト成功 ({duration:.1f}s): {test_summary}")
        else:
            logger.error(f"❌ {test_type}テスト失敗 ({duration:.1f}s): {test_summary}")

            # 失敗詳細をログ出力
            error_lines = result.stdout.split("\n")[-10:]  # 最後の10行
            for line in error_lines:
                if line.strip():
                    logger.error(f"  {line}")

        # 品質ゲートチェック
        if self.config.quality_gate_enabled and success:
            self._run_quality_gate_check()

        # 通知送信
        if self.config.notification_enabled:
            self._send_notification(success, test_type, test_summary, duration)

        # 履歴記録
        self.test_history.append(
            {
                "timestamp": datetime.now(),
                "test_type": test_type,
                "success": success,
                "duration": duration,
                "summary": test_summary,
            }
        )

    def _run_quality_gate_check(self):
        """品質ゲートチェック実行"""
        logger.info("🚦 品質ゲートチェック実行...")

        try:
            cmd = [sys.executable, "scripts/quality_gate_checker.py"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode == 0:
                logger.info("✅ 品質ゲート通過")
            else:
                logger.warning("⚠️ 品質ゲート警告あり")

        except Exception as e:
            logger.error(f"品質ゲートチェックエラー: {e}")

    def _send_notification(
        self, success: bool, test_type: str, summary: str, duration: float
    ):
        """通知送信"""
        status = "✅成功" if success else "❌失敗"
        message = f"TDD自動テスト {status}\n種類: {test_type}\n結果: {summary}\n時間: {duration:.1f}s"

        # デスクトップ通知（macOS）
        try:
            if sys.platform == "darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{summary}" with title "TDD自動テスト {status}" sound name "Glass"',
                    ],
                    check=False,
                )
        except:
            pass

        logger.info(f"📬 通知送信: {message.replace(chr(10), ' ')}")

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"シグナル {signum} 受信。シャットダウン中...")
        self._shutdown()

    def _shutdown(self):
        """システムシャットダウン"""
        logger.info("🛑 TDD自動化システム停止中...")
        self.running = False

        # 履歴保存
        history_file = self.project_root / "tdd_automation_history.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self.test_history, f, indent=2, default=str, ensure_ascii=False)

        logger.info("💾 実行履歴を保存しました")
        logger.info("👋 TDD自動化システム停止完了")


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    config = AutoTestConfig(
        watch_patterns=[
            "kumihan_formatter/**/*.py",
            "tests/**/*.py",
            "pyproject.toml",
            "CLAUDE.md",
        ],
        test_patterns=[
            "tests/**/test_{module}*.py",
            "tests/test_{module}.py",
        ],
        quality_gate_enabled=True,
        continuous_integration=True,
        notification_enabled=True,
        debounce_seconds=2.0,
    )

    automation = TDDAutomation(config, project_root)

    logger.info("🚀 TDD自動化システム起動 - Issue #640 Phase 1")

    # システム開始
    automation.start_automation()


if __name__ == "__main__":
    main()
