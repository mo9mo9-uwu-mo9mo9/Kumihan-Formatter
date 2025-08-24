"""UnifiedContentParser - 統合コンテンツ解析エンジン"""

from typing import Any, Dict
from ..core.parsing.specialized.content_parser import UnifiedContentParser as CoreContentParser
from ..core.utilities.logger import get_logger

class UnifiedContentParser:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.core_parser = CoreContentParser()
    
    def parse(self, text: str) -> Dict[str, Any]:
        try:
            return self.core_parser.parse(text)
        except Exception as e:
            return {"content": text, "error": str(e), "type": "content_error"}