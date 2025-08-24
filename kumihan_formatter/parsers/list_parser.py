"""
UnifiedListParser - 統合リスト解析エンジン

統合対象:
- kumihan_formatter/core/parsing/list/list_parser.py
- kumihan_formatter/core/parsing/specialized/list_parser.py  
- kumihan_formatter/core/list_parser.py
"""

from typing import Any, Dict
from ..core.parsing.specialized.list_parser import UnifiedListParser as CoreListParser
from ..core.utilities.logger import get_logger


class UnifiedListParser:
    """統合リスト解析エンジン"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.core_parser = CoreListParser()
        self.logger.info("UnifiedListParser initialized")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """リスト解析"""
        try:
            return self.core_parser.parse(text)
        except Exception as e:
            self.logger.error(f"List parsing error: {e}")
            return {"content": text, "error": str(e), "type": "list_error"}