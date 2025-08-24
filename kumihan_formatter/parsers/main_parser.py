"""
UnifiedMainParser - 統合メイン解析エンジン

統合対象:
- kumihan_formatter/core/parsing/main_parser.py
- kumihan_formatter/parser.py  
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..core.parsing.main_parser import MainParser as CoreMainParser
from ..parser import Parser as LegacyParser
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import ParseResult, ParseContext, BaseParserProtocol
else:
    BaseParserProtocol = object


class UnifiedMainParser(BaseParserProtocol):
    """統合メイン解析エンジン - 全解析機能のエントリーポイント
    
    BaseParserProtocol実装によりアーキテクチャ統一を実現
    """
    
    def __init__(self, graceful_errors: bool = False):
        self.logger = get_logger(__name__)
        self.core_parser: Optional[CoreMainParser] = None
        self.legacy_parser: Optional[LegacyParser] = None
        self.use_legacy: bool = False
        self.graceful_errors: bool = graceful_errors
        
        # メイン解析エンジン統合
        try:
            self.core_parser = CoreMainParser()
            self.legacy_parser = LegacyParser(graceful_errors=graceful_errors)
            self.use_legacy = False
        except Exception as e:
            self.logger.warning(f"Core parser initialization failed: {e}, using legacy parser")
            self.legacy_parser = LegacyParser(graceful_errors=graceful_errors)
            self.core_parser = None
            self.use_legacy = True
        
        self.graceful_errors = graceful_errors
        
        self.logger.info("UnifiedMainParser initialized")
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一テキスト解析 - BaseParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult, ParseContext
        
        try:
            if self.use_legacy or not self.core_parser:
                legacy_result = self._parse_legacy(content)
            else:
                legacy_result = self._parse_core(content)
            
            # Dict結果をParseResultに変換
            return self._convert_to_parse_result(legacy_result)
            
        except Exception as e:
            self.logger.error(f"Parsing error: {e}")
            if self.graceful_errors:
                return self._create_error_parse_result(str(e), content)
            raise
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            result = self.validate_syntax(content)
            if result.get("valid", False):
                return []
            else:
                errors = result.get("errors", ["Unknown validation error"])
                return errors if isinstance(errors, list) else [str(errors)]
        except Exception as e:
            return [f"Validation failed: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedMainParser",
            "version": "2.0.0",
            "supported_formats": ["kumihan", "markdown", "html"],
            "capabilities": [
                "keyword_parsing",
                "block_parsing", 
                "list_parsing",
                "streaming_parsing",
                "graceful_error_handling"
            ]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported
    
    def _parse_core(self, text: str) -> Dict[str, Any]:
        """コアパーサーでの解析"""
        if self.core_parser is None:
            raise RuntimeError("Core parser not initialized")
        result = self.core_parser.parse(text)
        return self._normalize_result(result)
    
    def _parse_legacy(self, text: str) -> Dict[str, Any]:
        """レガシーパーサーでの解析"""  
        if self.legacy_parser is None:
            raise RuntimeError("Legacy parser not initialized")
        result = self.legacy_parser.parse(text)
        return self._normalize_result(result)
    
    def _normalize_result(self, result: Any) -> Dict[str, Any]:
        """解析結果の正規化"""
        if isinstance(result, dict):
            return result
        elif isinstance(result, list):
            return {"content": result, "type": "list"}
        elif isinstance(result, str):
            return {"content": result, "type": "string"}
        else:
            return {"content": str(result), "type": "unknown"}
    
    def _convert_to_parse_result(self, legacy_result: Dict[str, Any]) -> "ParseResult":
        """Dict結果をParseResultに変換"""
        from ..core.parsing.base.parser_protocols import ParseResult
        from ..core.ast_nodes.node import Node
        
        # ノード変換 - legacyフォーマットからNodeオブジェクトへ
        nodes: List[Node] = []
        content = legacy_result.get("content", [])
        if isinstance(content, list):
            # TODO: 適切なNode変換ロジックの実装
            pass
        
        return ParseResult(
            success=not legacy_result.get("error"),
            nodes=nodes,
            errors=[legacy_result["error"]] if legacy_result.get("error") else [],
            warnings=[],
            metadata=legacy_result
        )
    
    def _create_error_parse_result(self, error_msg: str, original_text: str) -> "ParseResult":
        """エラー結果作成"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        return ParseResult(
            success=False,
            nodes=[],
            errors=[error_msg],
            warnings=[],
            metadata={
                "original_content": original_text,
                "graceful_error": True
            }
        )
    
    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証"""
        try:
            if self.core_parser and hasattr(self.core_parser, 'validate_syntax'):
                result = self.core_parser.validate_syntax(text)
                return result if isinstance(result, dict) else {"valid": False, "errors": ["Invalid result type"]}
            else:
                # フォールバック: 解析試行で検証
                try:
                    self.parse(text)
                    return {"valid": True, "errors": []}
                except Exception as e:
                    return {"valid": False, "errors": [str(e)]}
        except Exception as e:
            self.logger.error(f"Syntax validation error: {e}")
            return {"valid": False, "errors": [str(e)]}
    
    def get_statistics(self) -> Dict[str, Any]:
        """解析統計情報"""
        stats: Dict[str, Any] = {
            "parser_type": "legacy" if self.use_legacy else "core",
            "graceful_errors": self.graceful_errors,
        }
        
        try:
            if self.core_parser and hasattr(self.core_parser, 'get_statistics'):
                core_stats = self.core_parser.get_statistics()
                if isinstance(core_stats, dict):
                    stats["core_stats"] = core_stats
            if self.legacy_parser and hasattr(self.legacy_parser, 'get_statistics'):
                legacy_stats = self.legacy_parser.get_statistics()  
                if isinstance(legacy_stats, dict):
                    stats["legacy_stats"] = legacy_stats
        except Exception as e:
            self.logger.warning(f"Statistics collection error: {e}")
            
        return stats