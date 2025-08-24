"""
UnifiedKeywordParser - 統合キーワード解析エンジン

統合対象:
- kumihan_formatter/core/parsing/keyword/keyword_parser.py
- kumihan_formatter/core/parsing/specialized/keyword_parser.py
"""

from typing import Any, Dict
from ..core.parsing.specialized.keyword_parser import UnifiedKeywordParser as CoreKeywordParser
from ..core.utilities.logger import get_logger


class UnifiedKeywordParser:
    """統合キーワード解析エンジン"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.core_parser = CoreKeywordParser()
        self.logger.info("UnifiedKeywordParser initialized")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """キーワード解析"""
        try:
            return self.core_parser.parse(text)
        except Exception as e:
            self.logger.error(f"Keyword parsing error: {e}")
            return {"content": text, "error": str(e), "type": "keyword_error"}