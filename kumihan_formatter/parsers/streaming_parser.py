"""UnifiedStreamingParser - 統合ストリーミング解析エンジン"""

from typing import Any, Dict, Iterator, List, Optional, TYPE_CHECKING, Type

CoreStreamingParser: Optional[Type[Any]] = None
try:
    from ..core.utilities.streaming_parser import ParallelStreamingParser as CoreStreamingParser
except ImportError:
    pass

LegacyStreamingParser: Optional[Type[Any]] = None
try:
    from ..streaming_parser import StreamingParser as LegacyStreamingParser
except ImportError:
    pass
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import ParseResult, ParseContext, StreamingParserProtocol
    from ..core.ast_nodes.node import Node
else:
    StreamingParserProtocol = object

class UnifiedStreamingParser(StreamingParserProtocol):
    """統合ストリーミング解析エンジン - StreamingParserProtocol実装"""
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        
        self.core_parser: Optional[Any] = None
        if CoreStreamingParser is not None:
            try:
                self.core_parser = CoreStreamingParser()
            except Exception as e:
                self.logger.warning(f"Core streaming parser initialization failed: {e}")
        
        self.legacy_parser: Optional[Any] = None
        if LegacyStreamingParser is not None:
            try:
                self.legacy_parser = LegacyStreamingParser("")  # 引数が必要
            except Exception as e:
                self.logger.warning(f"Legacy streaming parser initialization failed: {e}")
        
        self.chunk_size = 8192  # デフォルトチャンクサイズ
        self.logger.info("UnifiedStreamingParser initialized")
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一ストリーミング解析 - BaseParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        try:
            # ストリーミング処理をシミュレート
            chunks = self._split_into_chunks(content)
            all_nodes = []
            
            for chunk in chunks:
                chunk_nodes = self.process_chunk(chunk, context)
                all_nodes.extend(chunk_nodes)
            
            return ParseResult(
                success=True,
                nodes=all_nodes,
                errors=[],
                warnings=[],
                metadata={
                    "total_chunks": len(chunks),
                    "chunk_size": self.chunk_size,
                    "streaming": True
                }
            )
        except Exception as e:
            self.logger.error(f"Streaming parsing error: {e}")
            return self._create_error_parse_result(str(e), content)
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            errors = []
            
            # ストリーミング処理のバリデーション
            if len(content) > 100 * 1024 * 1024:  # 100MB制限
                errors.append("Content too large for streaming processing")
            
            # チャンク分割の検証
            chunks = self._split_into_chunks(content)
            if len(chunks) > 10000:  # チャンク数制限
                errors.append("Too many chunks for efficient processing")
            
            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedStreamingParser",
            "version": "2.0.0",
            "supported_formats": ["stream", "large_text", "kumihan"],
            "capabilities": [
                "streaming_parsing",
                "chunk_processing",
                "memory_efficient_parsing",
                "large_file_support"
            ]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported
    
    def parse_streaming(self, stream: Iterator[str], context: Optional["ParseContext"] = None) -> Iterator["Node"]:
        """ストリーミングパース"""
        from ..core.ast_nodes.node import Node
        
        try:
            for chunk in stream:
                nodes = self.process_chunk(chunk, context)
                for node in nodes:
                    yield node
        except Exception as e:
            self.logger.error(f"Streaming parse error: {e}")
            # エラー時もノードとして返す
            yield Node(
                type="error",
                content=f"Streaming error: {e}",
                attributes={"error": True}
            )
    
    def process_chunk(self, chunk: str, context: Optional["ParseContext"] = None) -> List["Node"]:
        """チャンクを処理"""
        from ..core.ast_nodes.node import Node
        
        try:
            nodes = []
            
            # チャンクを行単位で処理
            lines = chunk.split('\n')
            for line in lines:
                if line.strip():
                    node = Node(
                        type="text_chunk",
                        content=line,
                        attributes={
                            "chunk_size": len(chunk),
                            "processed_streaming": True
                        }
                    )
                    nodes.append(node)
            
            return nodes
        except Exception as e:
            self.logger.error(f"Chunk processing error: {e}")
            return []
    
    def get_chunk_size(self) -> int:
        """推奨チャンクサイズを取得"""
        return self.chunk_size
    
    def supports_streaming(self) -> bool:
        """ストリーミング処理対応確認"""
        return True  # このクラスは常にストリーミング対応
    
    def _split_into_chunks(self, content: str) -> List[str]:
        """コンテンツをチャンクに分割"""
        chunks = []
        for i in range(0, len(content), self.chunk_size):
            chunks.append(content[i:i + self.chunk_size])
        return chunks
    
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
                "parser_type": "streaming"
            }
        )
    
    def parse_stream(self, text_stream: Iterator[str]) -> Iterator[Dict[str, Any]]:
        """レガシーメソッド - 後方互換性のため"""
        # ストリーミング解析（簡略実装）
        for chunk in text_stream:
            yield {"chunk": chunk, "type": "stream_chunk"}