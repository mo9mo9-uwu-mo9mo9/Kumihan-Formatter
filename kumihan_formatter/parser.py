"""Parser - 統合パーサーエントリーポイント

Issue #1252対応: パーサー統合最適化完了版
統合された5つのパーサーコンポーネントへの統一インターフェース

統合構成 (10個→5個):
1. main_parser.py - メインパーサー
2. core_parser.py - コアパーサー（legacy+parser_core統合）
3. specialized_parser.py - 特殊化パーサー（マーカー・フォーマット系統合）
4. parser_protocols.py - プロトコル定義
5. parser_utils.py - ユーティリティ統合

新しいコードでは各パーサーを直接使用するか、unified_api.pyを推奨
"""

import warnings
from typing import Any, Dict, Optional

from .core.ast_nodes import Node, error_node

# 統合パーサーコンポーネント（Issue #1252統合版）
from .parsers.core_parser import (
    ParallelProcessingError,
    ChunkProcessingError,
    MemoryMonitoringError,
    ParallelProcessingConfig,
    Parser as CoreParser,
    parse as core_parse,
    parse_with_error_config as _core_parse_with_error_config,
)
from .parsers.main_parser import MainParser
from .parsers.specialized_parser import SpecializedParser
from .parsers.parser_utils import ParserUtils


class Parser:
    """統合パーサーファサード

    Issue #1252対応: 10個→5個統合完了
    後方互換性を保ちつつ、統合されたパーサー機能を提供
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """統合Parser初期化"""
        self.config = config or {}

        # 統合パーサーコンポーネント
        self.main_parser = MainParser(config)
        self.core_parser = CoreParser(config)
        self.specialized_parser = SpecializedParser(config)
        self.utils = ParserUtils(config)

    def parse(self, content: str) -> Node:
        """統合パース処理

        Args:
            content: パース対象コンテンツ

        Returns:
            パース結果ノード
        """
        # メインパーサーが判定・振り分け
        try:
            result = self.main_parser.parse(content)
            if isinstance(result, Node):
                return result
            # 念のための防御: 期待しない戻りはエラーノードに変換
            return error_node("Parser returned unexpected result type")
        except Exception as e:
            return error_node(f"Parser facade error: {e}")

    def parse_file(self, file_path: str) -> Node:
        """ファイルパース処理"""
        try:
            result = self.main_parser.parse_file(file_path)
            if isinstance(result, Node):
                return result
            return error_node("Parser returned unexpected result type (file)")
        except Exception as e:
            return error_node(f"Parser facade file error: {e}")

    def validate(self, content: str) -> bool:
        """コンテンツ検証"""
        return self.specialized_parser.validate(content)


def parse_with_error_config(
    text: str,
    config: Optional[Dict[str, Any]] = None,
    use_streaming: bool | None = None,
) -> Any:
    """レガシー互換: エラー設定対応パース（ストリーミング対応）

    - `use_streaming` が True の場合、`StreamingParser`（モック想定）を利用
    - None の場合はテキストサイズで簡易判定（>1MB で True）
    - それ以外は通常の `Parser` を使用
    """
    if use_streaming is None:
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        use_streaming = size_mb > 1.0

    if use_streaming:
        sp = globals().get("StreamingParser")
        if sp is not None:
            try:
                parser = sp(json_path="")
                return list(parser.parse_streaming_from_text(text))
            except Exception:
                # フォールバックして通常パース
                pass

    parser = Parser(config)
    return parser.parse(text)


def parse(content: str, config: Optional[Dict[str, Any]] = None) -> Node:
    """統合パース関数（簡易インターフェース）

    Args:
        content: パース対象コンテンツ
        config: パーサー設定

    Returns:
        パース結果ノード

    Note:
        統合最適化済み - 新しいコードはunified_api.pyの使用を推奨
    """
    parser = Parser(config)
    return parser.parse(content)


# 統合完了の明示的エクスポート
__all__ = [
    # 統合エラークラス
    "ParallelProcessingError",
    "ChunkProcessingError",
    "MemoryMonitoringError",
    # 統合設定クラス
    "ParallelProcessingConfig",
    # 統合パーサークラス
    "Parser",
    "MainParser",
    "CoreParser",
    "SpecializedParser",
    "ParserUtils",
    # 統合関数
    "parse",
    "core_parse",
    "parse_with_error_config",
]

# Issue #1252統合完了の通知
warnings.warn(
    "Parser integration completed (Issue #1252). "
    "10 files → 5 files optimization finished. "
    "Consider using unified_api.KumihanFormatter for new code.",
    UserWarning,
    stacklevel=2,
)
