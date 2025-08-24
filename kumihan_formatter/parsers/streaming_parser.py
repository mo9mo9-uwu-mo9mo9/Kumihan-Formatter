"""UnifiedStreamingParser - 統合ストリーミング解析エンジン"""

from typing import Any, Dict, Iterator
try:
    from ..core.utilities.streaming_parser import ParallelStreamingParser as CoreStreamingParser
except ImportError:
    CoreStreamingParser = None

try:
    from ..streaming_parser import StreamingParser as LegacyStreamingParser
except ImportError:
    LegacyStreamingParser = None
from ..core.utilities.logger import get_logger

class UnifiedStreamingParser:
    def __init__(self):
        self.logger = get_logger(__name__)
        
        self.core_parser = None
        if CoreStreamingParser:
            try:
                self.core_parser = CoreStreamingParser()
            except Exception:
                pass
        
        self.legacy_parser = None
        if LegacyStreamingParser:
            try:
                self.legacy_parser = LegacyStreamingParser()
            except Exception:
                pass
    
    def parse_stream(self, text_stream: Iterator[str]) -> Iterator[Dict[str, Any]]:
        # ストリーミング解析（簡略実装）
        for chunk in text_stream:
            yield {"chunk": chunk, "type": "stream_chunk"}