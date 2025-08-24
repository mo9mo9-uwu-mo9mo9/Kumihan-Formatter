"""UnifiedMarkdownParser - 統合Markdown解析エンジン"""

from typing import Any, Dict
from ..core.parsing.specialized.markdown_parser import UnifiedMarkdownParser as CoreMarkdownParser
from ..core.utilities.logger import get_logger

class UnifiedMarkdownParser:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.core_parser = CoreMarkdownParser()
    
    def parse(self, text: str) -> Dict[str, Any]:
        try:
            return self.core_parser.parse(text)
        except Exception as e:
            return {"content": text, "error": str(e), "type": "markdown_error"}