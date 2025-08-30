"""
統合API ユーティリティ関数モジュール
======================================

KumihanFormatterクラスの便利関数とラッパー関数を提供します。
unified_api.pyから分離してファイルサイズ最適化に貢献します。
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path


def quick_convert(
    input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """クイック変換関数（統合システム）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.convert(input_file, output_file)


def quick_parse(text: str) -> Dict[str, Any]:
    """クイック解析関数（統合ParsingManager）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.parse_text(text)


def unified_parse(text: str, parser_type: str = "auto") -> Dict[str, Any]:
    """統合パーサーシステムによる最適化解析"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.parse_text(text, parser_type)


def validate_kumihan_syntax(text: str) -> Dict[str, Any]:
    """Kumihan記法構文の詳細検証（統合検証システム）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.validate_syntax(text)


def get_parser_system_info() -> Dict[str, Any]:
    """統合Managerシステムの詳細情報取得"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.get_system_info()


# パフォーマンス最適化版関数（Issue #1229対応）
def optimized_quick_convert(
    input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """最適化クイック変換関数（高性能版）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter(performance_mode="optimized") as formatter:
        return formatter.convert(input_file, output_file)


def optimized_quick_parse(text: str) -> Dict[str, Any]:
    """最適化クイック解析関数（高性能版）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter(performance_mode="optimized") as formatter:
        return formatter.parse_text(text)


def optimized_convert_text(text: str, template: str = "default") -> str:
    """最適化テキスト変換関数（高性能版）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter(performance_mode="optimized") as formatter:
        return formatter.convert_text(text, template)


# 後方互換性のためのエイリアス
parse = unified_parse
validate = validate_kumihan_syntax


def main() -> None:
    """CLI エントリーポイント - シンプル実装"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法: kumihan <入力ファイル> [出力ファイル]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        result = quick_convert(input_file, output_file)
        if result["status"] == "success":
            print(f"変換完了: {result['output_file']}")
        else:
            print(f"変換エラー: {result['error']}")
            sys.exit(1)
    except Exception as e:
        print(f"実行エラー: {e}")
        sys.exit(1)

