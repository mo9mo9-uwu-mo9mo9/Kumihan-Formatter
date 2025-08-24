"""
Automatic fixer module for lint command - Unified Interface.

Issue #778: flake8自動修正ツール - 分割されたコンポーネントの統合
Technical Debt Reduction: auto_fixer.py分割による可読性向上
"""

from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

# 分割されたコンポーネントをインポート
from .auto_fixer_core import Flake8AutoFixerCore
from .fix_strategies import Flake8FixStrategies


class Flake8AutoFixer:
    """
    Flake8エラーの自動修正を行う統合クラス

    Issue #778: flake8自動修正ツール
    Phase 3.1: E501, E226, F401エラーの自動修正
    Phase 3.2: E704, 複合エラー処理, HTML レポート
    Phase 3.3: 品質監視機能, リアルタイム統計
    """

    def __init__(
        self, config_path: Optional[str] = None, error_types: Optional[List[str]] = None
    ):
        self.logger = get_logger(__name__)

        # 分割されたコンポーネントを初期化
        self.core = Flake8AutoFixerCore(config_path, error_types)
        self.strategies = Flake8FixStrategies(self.core.max_line_length)

        # 後方互換性のためのプロパティ委譲
        self.config_path = self.core.config_path
        self.max_line_length = self.core.max_line_length
        self.error_types = self.core.error_types
        self.fixes_applied = self.core.fixes_applied
        self.quality_metrics = self.core.quality_metrics

        self.logger.info("Flake8AutoFixer (unified) initialized")

    # ================================
    # コア機能への委譲
    # ================================

    def get_flake8_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """指定ファイルのflake8エラー一覧を取得"""
        return self.core.get_flake8_errors(file_path)

    def analyze_error_dependencies(
        self, errors: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """エラー間の依存関係を分析"""
        return self.core.analyze_error_dependencies(errors)

    def get_optimized_fix_order(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """最適な修正順序を計算"""
        return self.core.get_optimized_fix_order(errors)

    def sync_with_flake8_config(self, config_path: str) -> Dict[str, Any]:
        """flake8設定ファイルとの同期"""
        return self.core.sync_with_flake8_config(config_path)

    def should_fix_error(
        self, error_code: str, config_settings: Dict[str, Any]
    ) -> bool:
        """設定に基づいてエラーを修正すべきかチェック"""
        return self.core.should_fix_error(error_code, config_settings)

    def update_quality_metrics(
        self, errors_detected: int, errors_fixed: int, processing_time: float
    ) -> None:
        """Phase 3.3: Quality monitoring metrics update"""
        self.core.update_quality_metrics(errors_detected, errors_fixed, processing_time)

    def get_quality_report(self) -> Dict[str, Any]:
        """Phase 3.3: Generate quality monitoring report"""
        return self.core.get_quality_report()

    def fix_file(self, file_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """Fix flake8 errors in file (Phase 3.3 quality monitoring)"""
        return self.core.fix_file(file_path, dry_run)

    # ================================
    # 修正戦略への委譲
    # ================================

    def fix_e501_line_too_long(self, content: str, line_num: int) -> str:
        """E501: 行が長すぎる場合の自動修正"""
        result = self.strategies.fix_e501_line_too_long(content, line_num)
        self.fixes_applied["E501"] += self.strategies.get_last_fix_count()
        return result

    def fix_e226_missing_whitespace(self, content: str, line_num: int, col: int) -> str:
        """E226: 演算子周辺の空白不足を修正"""
        result = self.strategies.fix_e226_missing_whitespace(content, line_num, col)
        self.fixes_applied["E226"] += self.strategies.get_last_fix_count()
        return result

    def fix_f401_unused_import(self, content: str, line_num: int) -> str:
        """F401: 未使用importを削除"""
        result = self.strategies.fix_f401_unused_import(content, line_num)
        self.fixes_applied["F401"] += self.strategies.get_last_fix_count()
        return result

    def fix_e704_multiple_statements(self, content: str, line_num: int) -> str:
        """E704: 複数文を複数行に分割"""
        result = self.strategies.fix_e704_multiple_statements(content, line_num)
        self.fixes_applied["E704"] += self.strategies.get_last_fix_count()
        return result

    def generate_fix_report(
        self, fixes_applied: Dict[str, int], file_path: str
    ) -> Dict[str, Any]:
        """修正レポートを生成"""
        return self.strategies.generate_fix_report(fixes_applied, file_path)

    def generate_html_report(
        self, reports: List[Dict[str, Any]], output_path: str
    ) -> None:
        """HTML形式の修正レポートを生成"""
        self.strategies.generate_html_report(reports, output_path)

    # ================================
    # 下位互換性メソッド (テスト用)
    # ================================

    def _get_max_line_length(self) -> int:
        """行長制限を取得（下位互換性のため）"""
        return self.max_line_length

    def _split_function_call(self, line: str) -> str:
        """関数呼び出し分割（下位互換性のため）"""
        # 基本的な関数呼び出し分割ロジック
        if len(line) <= self.max_line_length:
            return line

        # 関数呼び出しパターンを検出
        import re

        func_call_pattern = r"(\w+)\s*\((.*)\)"
        match = re.search(func_call_pattern, line)

        if not match:
            return line

        func_name = match.group(1)
        args = match.group(2)

        # 簡単な分割: 引数を改行で分割
        if "," in args:
            split_args = [arg.strip() for arg in args.split(",")]
            formatted_args = ",\n    ".join(split_args)
            return f"{func_name}(\n    {formatted_args}\n)"

        return line

    def _extract_import_names(self, import_line: str) -> List[str]:
        """import名抽出（下位互換性のため）"""
        import re

        names = []

        # import module
        if import_line.strip().startswith("import "):
            # 'import os, sys' -> ['os', 'sys']
            modules = import_line.replace("import ", "").strip()
            names.extend([mod.strip() for mod in modules.split(",")])

        # from module import name
        elif import_line.strip().startswith("from ") and " import " in import_line:
            # 'from pathlib import Path, os' -> ['Path', 'os']
            import_part = import_line.split(" import ")[1].strip()
            names.extend([name.strip() for name in import_part.split(",")])

        return names


# 後方互換性のため、元のクラス名もエクスポート
__all__ = ["Flake8AutoFixer"]
