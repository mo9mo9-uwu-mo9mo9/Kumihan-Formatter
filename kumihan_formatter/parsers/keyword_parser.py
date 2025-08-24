"""
UnifiedKeywordParser - 統合キーワード解析エンジン

統合対象:
- kumihan_formatter/core/parsing/keyword/keyword_parser.py
- kumihan_formatter/core/parsing/specialized/keyword_parser.py
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from ..core.parsing.specialized.keyword_parser import UnifiedKeywordParser as CoreKeywordParser
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import ParseResult, ParseContext, KeywordParserProtocol
else:
    KeywordParserProtocol = object


class UnifiedKeywordParser(KeywordParserProtocol):
    """統合キーワード解析エンジン - KeywordParserProtocol実装"""
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.core_parser = CoreKeywordParser()
        self.logger.info("UnifiedKeywordParser initialized")
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一キーワード解析 - KeywordParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        try:
            legacy_result = self.core_parser.parse(content)
            return self._convert_to_parse_result(legacy_result)
        except Exception as e:
            self.logger.error(f"Keyword parsing error: {e}")
            return self._create_error_parse_result(str(e), content)
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            errors = []
            keywords = self.parse_keywords(content, context)
            
            for keyword in keywords:
                if not self.validate_keyword(keyword, context):
                    errors.append(f"Invalid keyword: {keyword}")
            
            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedKeywordParser",
            "version": "2.0.0",
            "supported_formats": ["kumihan", "keyword"],
            "capabilities": [
                "keyword_parsing",
                "marker_parsing",
                "compound_keyword_splitting",
                "keyword_validation",
                "new_format_support"
            ]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported
    
    def parse_keywords(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """コンテンツからキーワードを抽出"""
        try:
            # CoreKeywordParserからキーワード抽出
            if hasattr(self.core_parser, 'parse_keywords'):
                result = self.core_parser.parse_keywords(content)
                if isinstance(result, list):
                    return result
            
            # フォールバック: 基本的なキーワード抽出
            return self._extract_basic_keywords(content)
        except Exception as e:
            self.logger.error(f"Keyword extraction error: {e}")
            return []
    
    def parse_marker_keywords(self, marker_content: str, context: Optional["ParseContext"] = None) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """マーカーからキーワードと属性を解析"""
        try:
            # マーカー解析: # 装飾名 #内容## 形式
            keywords = []
            attributes = {}
            errors = []
            
            stripped = marker_content.strip()
            if stripped.startswith('#') and ' #' in stripped and stripped.endswith('##'):
                parts = stripped.split(' #', 1)
                decoration = parts[0][1:].strip()  # # を除去
                content_part = parts[1][:-2].strip()  # ## を除去
                
                keywords.append(decoration)
                
                # 属性解析（装飾名がkeyword形式の場合）
                if '=' in decoration:
                    try:
                        key, value = decoration.split('=', 1)
                        attributes[key.strip()] = value.strip()
                    except Exception:
                        errors.append(f"Invalid attribute format: {decoration}")
                
                attributes["content"] = content_part
            else:
                errors.append(f"Invalid marker format: {marker_content}")
            
            return keywords, attributes, errors
        except Exception as e:
            self.logger.error(f"Marker parsing error: {e}")
            return [], {}, [str(e)]
    
    def validate_keyword(self, keyword: str, context: Optional["ParseContext"] = None) -> bool:
        """キーワードの妥当性を検証"""
        try:
            # 基本的なキーワード検証
            if not keyword or not isinstance(keyword, str):
                return False
            
            # 予約語や特殊文字のチェック
            invalid_chars = ['<', '>', '&', '"', "'", '\n', '\r', '\t']
            if any(char in keyword for char in invalid_chars):
                return False
            
            # 長さ制限
            if len(keyword) > 100:
                return False
            
            return True
        except Exception:
            return False
    
    def parse_new_format(self, content: str) -> Any:
        """新フォーマット解析（marker_parser.py/content_parser.py用）"""
        try:
            if hasattr(self.core_parser, 'parse_new_format'):
                return self.core_parser.parse_new_format(content)
            else:
                # フォールバック: 基本解析
                return self.parse_keywords(content)
        except Exception as e:
            self.logger.error(f"New format parsing error: {e}")
            return None
    
    def get_node_factory(self) -> Any:
        """ノードファクトリー取得（marker_parser.py/content_parser.py用）"""
        try:
            if hasattr(self.core_parser, 'get_node_factory'):
                return self.core_parser.get_node_factory()
            else:
                # フォールバック: デフォルトファクトリー
                from ..core.ast_nodes.factories import create_node
                return create_node
        except Exception as e:
            self.logger.error(f"Node factory error: {e}")
            return None
    
    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを個別キーワードに分割"""
        try:
            # 基本的な分割ロジック
            if ',' in keyword_content:
                return [k.strip() for k in keyword_content.split(',') if k.strip()]
            elif ';' in keyword_content:
                return [k.strip() for k in keyword_content.split(';') if k.strip()]
            elif '|' in keyword_content:
                return [k.strip() for k in keyword_content.split('|') if k.strip()]
            else:
                return [keyword_content.strip()] if keyword_content.strip() else []
        except Exception as e:
            self.logger.error(f"Compound keyword splitting error: {e}")
            return [keyword_content] if keyword_content else []
    
    def _extract_basic_keywords(self, content: str) -> List[str]:
        """基本的なキーワード抽出"""
        import re
        
        keywords = []
        
        # Kumihanマーカーパターン: # 装飾名 #内容##
        marker_pattern = r'#\s*([^#\s]+)\s*#[^#]*##'
        matches = re.findall(marker_pattern, content)
        keywords.extend(matches)
        
        return list(set(keywords))  # 重複除去
    
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
                "parser_type": "keyword"
            }
        )