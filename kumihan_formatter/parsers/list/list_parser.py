"""List Parser - 統合リスト解析エンジン（メインクラス）

責任分離による構造:
- このファイル: メインクラス・パブリックインターフェース・プロトコル準拠
- list_handlers.py: 処理・分析ロジック
- list_utils.py: ユーティリティ関数群
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import ParseResult, ParseContext, ListParserProtocol
else:
    try:
        from ...core.parsing.base.parser_protocols import ParseResult, ParseContext, ListParserProtocol
    except ImportError:
        ListParserProtocol = object

from ...core.utilities.logger import get_logger
from .list_handlers import ListHandler, ListItemHandler
from .list_utils import (
    setup_list_patterns,
    setup_list_handlers,
    detect_list_type,
    get_list_nesting_level,
    extract_list_content,
    is_kumihan_list_block,
)


class UnifiedListParser(ListParserProtocol):
    """統合リスト解析エンジン - ListParserProtocol実装
    
    責任範囲:
    - プロトコル準拠インターフェース実装
    - リスト解析の統合管理
    - 外部依存関係の管理
    
    分離された処理:
    - 詳細な解析処理: ListHandler, ListItemHandler
    - ユーティリティ関数: list_utils モジュール
    """
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        
        # コア解析エンジンの初期化
        try:
            from ...core.parsing.get_global_coordinator import get_global_coordinator
            self.core_parser = get_global_coordinator()
        except ImportError:
            self.core_parser = None
        
        # 責任分離されたハンドラの初期化
        self.list_handler = ListHandler()
        self.item_handler = ListItemHandler()
        
        # 設定の初期化（ユーティリティ関数を使用）
        self.list_patterns = setup_list_patterns()
        self.list_handlers = setup_list_handlers()
    
    # === ListParserProtocol実装 ===
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一リスト解析 - ListParserProtocol準拠"""
        from ...core.parsing.base.parser_protocols import ParseResult
        
        try:
            self.logger.debug("統合リスト解析開始")
            
            # リストコンテンツの抽出と前処理
            list_content = extract_list_content(content)
            
            # コア解析の実行
            if self.core_parser:
                core_result = self.core_parser.parse_list(content)
                nodes = core_result.get("nodes", [])
            else:
                # フォールバック処理
                nodes = self._fallback_parse(content)
            
            # 詳細解析の実行（ハンドラに委譲）
            if is_kumihan_list_block(content):
                kumihan_analysis = self.list_handler.parse_kumihan_list_block(content)
            else:
                kumihan_analysis = {}
            
            regular_analysis = self.list_handler.parse_regular_lists(content)
            nested_analysis = self.list_handler.parse_nested_structure(content)
            
            # ParseResult作成
            return ParseResult(
                success=True,
                nodes=nodes,
                errors=[],
                warnings=[],
                metadata={
                    "parser_type": "UnifiedListParser",
                    "list_type": detect_list_type(content.split('\n')[0]) if content.strip() else "unknown",
                    "kumihan_analysis": kumihan_analysis,
                    "regular_analysis": regular_analysis,
                    "nested_analysis": nested_analysis,
                    "processing_time": 0.0,
                }
            )
        
        except Exception as e:
            self.logger.error(f"統合リスト解析エラー: {e}")
            return self._create_error_parse_result(str(e), content)
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """リストバリデーション - ListParserProtocol準拠"""
        try:
            # 基本的な構造検証（ハンドラに委譲）
            return self.list_handler.validate_list_structure(content)
        
        except Exception as e:
            self.logger.error(f"バリデーション処理エラー: {e}")
            return [f"バリデーション処理中にエラーが発生しました: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得 - BaseParserProtocol準拠"""
        return {
            "name": "UnifiedListParser",
            "version": "3.0.0",
            "description": "統合リスト解析エンジン",
            "supported_formats": [
                "unordered_list",
                "ordered_list",
                "checklist",
                "definition_list",
                "nested_list",
                "kumihan_list",
                "alpha_list",
                "roman_list"
            ],
            "capabilities": [
                "list_parsing",
                "nested_structure_analysis",
                "list_type_detection",
                "checklist_processing",
                "definition_list_processing",
                "kumihan_list_processing"
            ],
            "architecture": "responsibility_separated",
            "components": ["ListHandler", "ListItemHandler", "list_utils"]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認 - BaseParserProtocol準拠"""
        supported = ["list", "checklist", "definition", "nested", "kumihan", "ordered", "unordered"]
        return any(fmt in format_hint.lower() for fmt in supported)
    
    # === ListParserProtocol専用メソッド ===
    
    def parse_list_items(self, content: str, context: Optional["ParseContext"] = None) -> List[Any]:
        """リストアイテム解析 - ListParserProtocol準拠"""
        try:
            from ...core.ast_nodes.node import Node
            
            lines = content.split("\n")
            list_items = []
            
            for line in lines:
                if not line.strip():
                    continue
                
                list_type = detect_list_type(line)
                if list_type:
                    # 各種ハンドラを使用してアイテム処理
                    if list_type == "unordered":
                        item_data = self.item_handler.handle_unordered_item(line)
                    elif list_type == "ordered":
                        item_data = self.item_handler.handle_ordered_numeric_item(line)
                    elif list_type == "checklist":
                        item_data = self.item_handler.handle_checklist_item(line)
                    elif list_type == "definition":
                        item_data = self.item_handler.handle_definition_item(line)
                    elif list_type == "alpha":
                        item_data = self.item_handler.handle_alpha_item(line)
                    elif list_type == "roman":
                        item_data = self.item_handler.handle_roman_item(line)
                    else:
                        item_data = {"type": "unknown", "content": line}
                    
                    list_items.append(Node("list_item", **item_data))
            
            return list_items
        
        except ImportError:
            # フォールバック
            return [{"type": "list_item", "content": line} for line in content.split("\n") if line.strip()]
    
    def parse_nested_list(self, content: str, level: int = 0, context: Optional["ParseContext"] = None) -> List[Any]:
        """ネストリスト解析 - ListParserProtocol準拠"""
        # ハンドラに委譲
        nested_result = self.list_handler.parse_nested_structure(content)
        return nested_result.get("nested_items", [])
    
    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプ検出 - ListParserProtocol準拠（ユーティリティに委譲）"""
        return detect_list_type(line)
    
    def get_list_nesting_level(self, line: str) -> int:
        """ネストレベル取得 - ListParserProtocol準拠（ユーティリティに委譲）"""
        return get_list_nesting_level(line)
    
    # === プライベートメソッド ===
    
    def _fallback_parse(self, content: str) -> List[Any]:
        """フォールバック解析処理"""
        try:
            from ...core.ast_nodes.node import Node
            
            # 簡単なリストノード作成
            return [Node("list", content=content)]
        except ImportError:
            # 最終フォールバック
            return [{"type": "list", "content": content}]
    
    def _create_error_parse_result(self, error_msg: str, original_content: str) -> "ParseResult":
        """エラー時のParseResult作成"""
        from ...core.parsing.base.parser_protocols import ParseResult
        
        return ParseResult(
            success=False,
            nodes=[],
            errors=[error_msg],
            warnings=[],
            metadata={
                "parser_type": "UnifiedListParser",
                "original_content_length": len(original_content),
                "error_occurred": True,
            }
        )


# 後方互換性のためのエイリアス
ListParser = UnifiedListParser