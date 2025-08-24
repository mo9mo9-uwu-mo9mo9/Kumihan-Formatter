"""
UnifiedMainParser - 統合メイン解析エンジン

統合対象:
- kumihan_formatter/core/parsing/main_parser.py
- kumihan_formatter/parser.py  
"""

from typing import Any, Dict, List, Optional
from ..core.parsing.main_parser import MainParser as CoreMainParser
from ..parser import Parser as LegacyParser
from ..core.utilities.logger import get_logger


class UnifiedMainParser:
    """統合メイン解析エンジン - 全解析機能のエントリーポイント"""
    
    def __init__(self, graceful_errors: bool = False):
        self.logger = get_logger(__name__)
        
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
    
    def parse(self, text: str) -> Dict[str, Any]:
        """統合テキスト解析"""
        try:
            if self.use_legacy or not self.core_parser:
                return self._parse_legacy(text)
            else:
                return self._parse_core(text)
        except Exception as e:
            self.logger.error(f"Parsing error: {e}")
            if self.graceful_errors:
                return self._create_error_result(str(e), text)
            raise
    
    def _parse_core(self, text: str) -> Dict[str, Any]:
        """コアパーサーでの解析"""
        result = self.core_parser.parse(text)
        return self._normalize_result(result)
    
    def _parse_legacy(self, text: str) -> Dict[str, Any]:
        """レガシーパーサーでの解析"""  
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
    
    def _create_error_result(self, error_msg: str, original_text: str) -> Dict[str, Any]:
        """エラー結果作成"""
        return {
            "content": original_text,
            "error": error_msg,
            "type": "error",
            "graceful_error": True
        }
    
    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証"""
        try:
            if hasattr(self.core_parser, 'validate_syntax'):
                return self.core_parser.validate_syntax(text)
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
        stats = {
            "parser_type": "legacy" if self.use_legacy else "core",
            "graceful_errors": self.graceful_errors,
        }
        
        try:
            if hasattr(self.core_parser, 'get_statistics'):
                stats["core_stats"] = self.core_parser.get_statistics()
            if hasattr(self.legacy_parser, 'get_statistics'):
                stats["legacy_stats"] = self.legacy_parser.get_statistics()
        except Exception as e:
            self.logger.warning(f"Statistics collection error: {e}")
            
        return stats