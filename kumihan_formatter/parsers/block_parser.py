"""
UnifiedBlockParser - 統合ブロック解析エンジン

統合対象:
- kumihan_formatter/core/parsing/block/block_parser.py  
- kumihan_formatter/core/parsing/specialized/block_parser.py
"""

from typing import Any, Dict
from ..core.parsing.specialized.block_parser import UnifiedBlockParser as CoreBlockParser
from ..core.utilities.logger import get_logger


class UnifiedBlockParser:
    """統合ブロック解析エンジン"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.core_parser = CoreBlockParser()
        self.logger.info("UnifiedBlockParser initialized")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """ブロック解析"""
        try:
            return self.core_parser.parse(text)
        except Exception as e:
            self.logger.error(f"Block parsing error: {e}")
            return {"content": text, "error": str(e), "type": "block_error"}