"""
統合API v2 - Issue #1249 責任分離完了版
==========================================

新しい責任分離アーキテクチャによる
保守性・可読性・テスト容易性を向上させた統合APIです。

アーキテクチャ構成:
1. FormatterConfig - 設定管理専用
2. ManagerCoordinator - Manager間調整専用
3. FormatterCore - コアロジック専用
4. FormatterAPI - ユーザーインターフェース専用

使用例:
    from kumihan_formatter.unified_api import KumihanFormatter

    formatter = KumihanFormatter()
    result = formatter.convert("input.txt", "output.html")

旧KumihanFormatterとの完全互換性を保持:
    - 同じメソッド名・シグネチャ
    - 同じ戻り値構造
    - 同じエラーハンドリング
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# 新しい責任分離アーキテクチャ
from .core.api.formatter_api import FormatterAPI


# 後方互換性のためのメインクラス（KumihanFormatterという名前を維持）
class KumihanFormatter:
    """統合Kumihan-Formatterクラス - 責任分離リファクタリング完了版"""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        performance_mode: str = "standard",
    ):
        # 新しい責任分離アーキテクチャによる初期化
        self._api = FormatterAPI(config_path, performance_mode)

    # 公開APIメソッド群（完全後方互換）

    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """統合Managerシステムによる最適化変換"""
        return self._api.convert(input_file, output_file, template, options)

    def convert_text(self, text: str, template: str = "default") -> str:
        """テキスト→HTML変換（統合Managerシステム対応）"""
        return self._api.convert_text(text, template)

    def parse_text(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """テキスト解析（統合ParsingManager対応）"""
        return self._api.parse_text(text, parser_type)

    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証（統合ParsingManager対応）"""
        return self._api.validate_syntax(text)

    def parse_file(
        self, file_path: Union[str, Path], parser_type: str = "auto"
    ) -> Dict[str, Any]:
        """ファイル解析（統合Managerシステム対応）"""
        return self._api.parse_file(file_path, parser_type)

    def get_available_templates(self) -> List[str]:
        """利用可能テンプレート取得（CoreManager対応）"""
        return self._api.get_available_templates()

    def get_system_info(self) -> Dict[str, Any]:
        """統合システム情報取得"""
        system_info = self._api.get_system_info()
        # バージョン情報更新
        system_info["version"] = "5.0.0-refactored"
        system_info["refactoring_status"] = "responsibility_separation_completed"
        return system_info

    # リソース管理

    def close(self) -> None:
        """統合システムのリソース解放"""
        self._api.close()

    def __enter__(self) -> "KumihanFormatter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


# 後方互換性のためのダミークラス（廃止予定）
class DummyParser:
    """Dummy parser for compatibility"""

    def parse(self, text: str, parser_type: str = "auto") -> List[Any]:
        return []


class DummyRenderer:
    """Dummy renderer for compatibility"""

    def render(self, parsed_result: Any, context: Dict[str, Any]) -> str:
        return "<p>Rendering not available</p>"


# __all__でエクスポートを明示
__all__ = [
    "KumihanFormatter",
    "DummyParser",
    "DummyRenderer",
]
