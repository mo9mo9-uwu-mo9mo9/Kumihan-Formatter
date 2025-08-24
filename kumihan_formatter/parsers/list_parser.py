"""
UnifiedListParser - 統合リスト解析エンジン

統合対象:
- kumihan_formatter/core/parsing/list/list_parser.py
- kumihan_formatter/core/parsing/specialized/list_parser.py  
- kumihan_formatter/core/list_parser.py
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..core.parsing.specialized.list_parser import UnifiedListParser as CoreListParser
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import ParseResult, ParseContext, ListParserProtocol
    from ..core.ast_nodes.node import Node
else:
    ListParserProtocol = object


class UnifiedListParser(ListParserProtocol):
    """統合リスト解析エンジン - ListParserProtocol実装"""
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.core_parser = CoreListParser()
        self.logger.info("UnifiedListParser initialized")
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一リスト解析 - ListParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        try:
            legacy_result = self.core_parser.parse(content)
            return self._convert_to_parse_result(legacy_result)
        except Exception as e:
            self.logger.error(f"List parsing error: {e}")
            return self._create_error_parse_result(str(e), content)
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            errors = []
            lines = content.strip().split('\n')
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and (stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('+ ')):
                    # 順序なしリストの基本チェック
                    if len(stripped) < 3:  # 最低限の長さ
                        errors.append(f"Invalid unordered list item at line {i+1}: {line}")
                elif stripped and (len(stripped) > 1 and stripped[0].isdigit() and stripped[1] == '.'):
                    # 順序ありリストの基本チェック
                    if len(stripped) < 4:  # 最低限の長さ
                        errors.append(f"Invalid ordered list item at line {i+1}: {line}")
            
            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedListParser",
            "version": "2.0.0",
            "supported_formats": ["kumihan", "list", "markdown"],
            "capabilities": [
                "list_parsing",
                "nested_list_support",
                "ordered_list_parsing",
                "unordered_list_parsing",
                "list_type_detection",
                "nesting_level_detection"
            ]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported
    
    def parse_list_items(self, content: str, context: Optional["ParseContext"] = None) -> List["Node"]:
        """リストアイテムをパース"""
        from ..core.ast_nodes.node import Node
        
        try:
            nodes = []
            lines = content.strip().split('\n')
            
            for line in lines:
                stripped = line.strip()
                if stripped:
                    list_type = self.detect_list_type(line)
                    if list_type:
                        # リストアイテムとしてノード作成
                        content_text = self._extract_list_content(line)
                        node = Node(
                            type=f"{list_type}_item",
                            content=content_text,
                            attributes={
                                "nesting_level": self.get_list_nesting_level(line),
                                "original_line": line
                            }
                        )
                        nodes.append(node)
            
            return nodes
        except Exception as e:
            self.logger.error(f"List item parsing error: {e}")
            return []
    
    def parse_nested_list(self, content: str, level: int = 0, context: Optional["ParseContext"] = None) -> List["Node"]:
        """ネストリストをパース"""
        from ..core.ast_nodes.node import Node
        
        try:
            nodes = []
            lines = content.strip().split('\n')
            current_item = None
            child_lines = []
            
            for line in lines:
                nesting_level = self.get_list_nesting_level(line)
                
                if nesting_level == level:
                    # 現在のレベルのアイテム
                    if current_item and child_lines:
                        # 子要素を処理
                        child_nodes = self.parse_nested_list('\n'.join(child_lines), level + 1, context)
                        if current_item.children is None:
                            current_item.children = []
                        current_item.children.extend(child_nodes)
                        child_lines = []
                    
                    # 新しいアイテム作成
                    list_type = self.detect_list_type(line)
                    content_text = self._extract_list_content(line)
                    current_item = Node(
                        type=f"{list_type}_item" if list_type else "list_item",
                        content=content_text,
                        attributes={
                            "nesting_level": nesting_level,
                            "original_line": line
                        }
                    )
                    nodes.append(current_item)
                elif nesting_level > level:
                    # 子要素
                    child_lines.append(line)
            
            # 最後のアイテムの子要素処理
            if current_item and child_lines:
                child_nodes = self.parse_nested_list('\n'.join(child_lines), level + 1, context)
                if current_item.children is None:
                    current_item.children = []
                current_item.children.extend(child_nodes)
            
            return nodes
        except Exception as e:
            self.logger.error(f"Nested list parsing error: {e}")
            return []
    
    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプを検出"""
        stripped = line.strip()
        if not stripped:
            return None
        
        # インデントを除去した実際のコンテンツ部分
        content_start = len(line) - len(line.lstrip())
        actual_content = line[content_start:]
        
        # 順序なしリスト
        if actual_content.startswith('- ') or actual_content.startswith('* ') or actual_content.startswith('+ '):
            return "unordered"
        
        # 順序ありリスト
        if len(actual_content) > 1 and actual_content[0].isdigit():
            for i, char in enumerate(actual_content[1:], 1):
                if char == '.':
                    if i < len(actual_content) - 1 and actual_content[i + 1] == ' ':
                        return "ordered"
                    break
                elif not char.isdigit():
                    break
        
        return None
    
    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得"""
        # インデント数でネストレベルを判定
        content_start = len(line) - len(line.lstrip())
        
        # 通常は4スペースまたは1タブで1レベル
        if '\t' in line[:content_start]:
            return line[:content_start].count('\t')
        else:
            return content_start // 4
    
    def _extract_list_content(self, line: str) -> str:
        """リスト行からコンテンツ部分を抽出"""
        stripped = line.strip()
        
        # 順序なしリスト
        if stripped.startswith('- '):
            return stripped[2:].strip()
        elif stripped.startswith('* '):
            return stripped[2:].strip()
        elif stripped.startswith('+ '):
            return stripped[2:].strip()
        
        # 順序ありリスト
        if len(stripped) > 1 and stripped[0].isdigit():
            for i, char in enumerate(stripped[1:], 1):
                if char == '.':
                    if i < len(stripped) - 1 and stripped[i + 1] == ' ':
                        return stripped[i + 2:].strip()
                    break
                elif not char.isdigit():
                    break
        
        return stripped
    
    def _convert_to_parse_result(self, legacy_result: Any) -> "ParseResult":
        """Dict結果をParseResultに変換"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        if isinstance(legacy_result, dict):
            return ParseResult(
                success=not legacy_result.get("error"),
                nodes=[],  # TODO: 適切なNode変換
                errors=[legacy_result["error"]] if legacy_result.get("error") else [],
                warnings=[],
                metadata=legacy_result
            )
        else:
            return ParseResult(
                success=True,
                nodes=[],
                errors=[],
                warnings=[],
                metadata={"raw_result": legacy_result}
            )
    
    def _create_error_parse_result(self, error_msg: str, original_content: str) -> "ParseResult":
        """エラー結果作成"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        return ParseResult(
            success=False,
            nodes=[],
            errors=[error_msg],
            warnings=[],
            metadata={
                "original_content": original_content,
                "parser_type": "list"
            }
        )