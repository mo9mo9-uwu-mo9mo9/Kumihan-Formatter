"""UnifiedMarkdownParser - 統合Markdown解析エンジン"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..core.parsing.specialized.markdown_parser import UnifiedMarkdownParser as CoreMarkdownParser
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import ParseResult, ParseContext, MarkdownParserProtocol
    from ..core.ast_nodes.node import Node
else:
    MarkdownParserProtocol = object

class UnifiedMarkdownParser(MarkdownParserProtocol):
    """統合Markdown解析エンジン - MarkdownParserProtocol実装"""
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.core_parser = CoreMarkdownParser()
        self.logger.info("UnifiedMarkdownParser initialized")
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一Markdown解析 - MarkdownParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        try:
            legacy_result = self.core_parser.parse(content)
            return self._convert_to_parse_result(legacy_result)
        except Exception as e:
            self.logger.error(f"Markdown parsing error: {e}")
            return self._create_error_parse_result(str(e), content)
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            errors = []
            elements = self.detect_markdown_elements(content)
            
            # 基本的なMarkdown構文チェック
            lines = content.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # 見出しの検証
                if stripped.startswith('#'):
                    if not self._validate_heading(stripped):
                        errors.append(f"Invalid heading syntax at line {i+1}: {line}")
                
                # リンクの検証
                if '[' in stripped and ']' in stripped and '(' in stripped and ')' in stripped:
                    if not self._validate_link(stripped):
                        errors.append(f"Invalid link syntax at line {i+1}: {line}")
            
            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedMarkdownParser",
            "version": "2.0.0",
            "supported_formats": ["markdown", "md", "kumihan"],
            "capabilities": [
                "markdown_parsing",
                "heading_parsing",
                "link_parsing",
                "list_parsing",
                "code_block_parsing",
                "kumihan_conversion",
                "element_detection"
            ]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported
    
    def parse_markdown_elements(self, text: str, context: Optional["ParseContext"] = None) -> List["Node"]:
        """Markdown要素をパース"""
        from ..core.ast_nodes.node import Node
        
        try:
            nodes = []
            lines = text.split('\n')
            current_element = None
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                
                # 見出し
                if stripped.startswith('#'):
                    level = len(stripped) - len(stripped.lstrip('#'))
                    content_text = stripped[level:].strip()
                    node = Node(
                        type="heading",
                        content=content_text,
                        attributes={
                            "level": level,
                            "original_line": line
                        }
                    )
                    nodes.append(node)
                
                # リスト（基本的な処理）
                elif stripped.startswith(('- ', '* ', '+ ')) or (len(stripped) > 1 and stripped[0].isdigit() and stripped[1] == '.'):
                    list_type = "unordered" if stripped.startswith(('- ', '* ', '+ ')) else "ordered"
                    content_text = self._extract_markdown_list_content(stripped)
                    node = Node(
                        type=f"{list_type}_list_item",
                        content=content_text,
                        attributes={
                            "original_line": line
                        }
                    )
                    nodes.append(node)
                
                # 段落
                else:
                    node = Node(
                        type="paragraph",
                        content=stripped,
                        attributes={
                            "original_line": line
                        }
                    )
                    nodes.append(node)
            
            return nodes
        except Exception as e:
            self.logger.error(f"Markdown element parsing error: {e}")
            return []
    
    def convert_to_kumihan(self, markdown_text: str, context: Optional["ParseContext"] = None) -> str:
        """MarkdownをKumihan記法に変換"""
        try:
            lines = markdown_text.split('\n')
            kumihan_lines = []
            
            for line in lines:
                stripped = line.strip()
                
                # 見出し変換
                if stripped.startswith('#'):
                    level = len(stripped) - len(stripped.lstrip('#'))
                    content_text = stripped[level:].strip()
                    # Kumihan見出し: # 見出し1 #内容##
                    kumihan_lines.append(f"# 見出し{level} #{content_text}##")
                
                # 強調変換
                elif '**' in stripped:
                    # **text** → # 太字 #text##
                    import re
                    converted = re.sub(r'\*\*([^*]+)\*\*', r'# 太字 #\1##', stripped)
                    kumihan_lines.append(converted)
                
                elif '*' in stripped and '**' not in stripped:
                    # *text* → # イタリック #text##
                    import re
                    converted = re.sub(r'\*([^*]+)\*', r'# イタリック #\1##', stripped)
                    kumihan_lines.append(converted)
                
                # その他はそのまま
                else:
                    kumihan_lines.append(line)
            
            return '\n'.join(kumihan_lines)
        except Exception as e:
            self.logger.error(f"Markdown to Kumihan conversion error: {e}")
            return markdown_text
    
    def detect_markdown_elements(self, text: str) -> List[str]:
        """Markdown要素を検出"""
        elements = []
        lines = text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # 見出し
            if stripped.startswith('#'):
                level = len(stripped) - len(stripped.lstrip('#'))
                elements.append(f"heading_level_{level}")
            
            # リスト
            elif stripped.startswith(('- ', '* ', '+ ')):
                elements.append("unordered_list")
            elif len(stripped) > 1 and stripped[0].isdigit() and stripped[1] == '.':
                elements.append("ordered_list")
            
            # 強調
            elif '**' in stripped:
                elements.append("bold")
            elif '*' in stripped:
                elements.append("italic")
            
            # リンク
            elif '[' in stripped and ']' in stripped and '(' in stripped and ')' in stripped:
                elements.append("link")
            
            # コードブロック
            elif stripped.startswith('```'):
                elements.append("code_block")
            elif stripped.startswith('`') and stripped.endswith('`'):
                elements.append("inline_code")
            
            # 段落
            else:
                elements.append("paragraph")
        
        return list(set(elements))  # 重複除去
    
    def _validate_heading(self, heading_line: str) -> bool:
        """見出し行の妥当性検証"""
        stripped = heading_line.strip()
        
        # 基本的な見出し形式チェック
        if not stripped.startswith('#'):
            return False
        
        # レベル数制限（通常は1-6）
        level = len(stripped) - len(stripped.lstrip('#'))
        if level > 6 or level < 1:
            return False
        
        # 見出し内容の存在チェック
        content = stripped[level:].strip()
        if not content:
            return False
        
        return True
    
    def _validate_link(self, line: str) -> bool:
        """リンク構文の妥当性検証"""
        import re
        
        # 基本的なMarkdownリンク形式: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, line)
        
        return len(matches) > 0
    
    def _extract_markdown_list_content(self, list_line: str) -> str:
        """Markdownリスト行からコンテンツ抽出"""
        stripped = list_line.strip()
        
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
                "parser_type": "markdown"
            }
        )