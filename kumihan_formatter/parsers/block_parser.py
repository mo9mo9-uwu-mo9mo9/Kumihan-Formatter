"""
UnifiedBlockParser - 統合ブロック解析エンジン

統合対象:
- kumihan_formatter/core/parsing/block/block_parser.py  
- kumihan_formatter/core/parsing/specialized/block_parser.py
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..core.parsing.specialized.block_parser import UnifiedBlockParser as CoreBlockParser
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import ParseResult, ParseContext, BlockParserProtocol
    from ..core.ast_nodes.node import Node
else:
    BlockParserProtocol = object


class UnifiedBlockParser(BlockParserProtocol):
    """統合ブロック解析エンジン - BlockParserProtocol実装"""
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.core_parser = CoreBlockParser()
        self.logger.info("UnifiedBlockParser initialized")
    
    def parse(self, content: str, context: Optional["ParseContext"] = None) -> "ParseResult":
        """統一ブロック解析 - BlockParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        
        try:
            # CoreBlockParserの結果をParseResultに変換
            legacy_result = self.core_parser.parse(content)
            return self._convert_to_parse_result(legacy_result)
        except Exception as e:
            self.logger.error(f"Block parsing error: {e}")
            return self._create_error_parse_result(str(e), content)
    
    def validate(self, content: str, context: Optional["ParseContext"] = None) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            # ブロック構文の基本検証
            errors = []
            lines = content.strip().split('\n')
            
            for i, line in enumerate(lines):
                if line.strip().startswith('#') and line.strip().endswith('##'):
                    # Kumihanブロック記法の基本チェック
                    if not self._validate_kumihan_block(line):
                        errors.append(f"Invalid Kumihan block syntax at line {i+1}: {line}")
            
            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]
    
    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedBlockParser",
            "version": "2.0.0", 
            "supported_formats": ["kumihan", "block"],
            "capabilities": [
                "block_parsing",
                "kumihan_block_detection",
                "block_type_detection",
                "nested_block_support"
            ]
        }
    
    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported
    
    def parse_block(self, block: str, context: Optional["ParseContext"] = None) -> "Node":
        """単一ブロックをパース"""
        from ..core.ast_nodes.node import Node
        
        try:
            # TODO: CoreBlockParserから単一ブロック解析結果を取得
            result = self.core_parser.parse(block)
            # 結果をNodeオブジェクトに変換
            return self._convert_to_node(result, block)
        except Exception as e:
            self.logger.error(f"Single block parsing error: {e}")
            # エラー時はテキストノードとして返す
            return Node(type="text", content=block, attributes={"error": str(e)})
    
    def extract_blocks(self, text: str, context: Optional["ParseContext"] = None) -> List[str]:
        """テキストからブロックを抽出"""
        blocks = []
        lines = text.split('\n')
        current_block: List[str] = []
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') and '##' in stripped:
                if in_block:
                    # 前のブロック終了
                    if current_block:
                        blocks.append('\n'.join(current_block))
                        current_block = []
                # 新しいブロック開始
                current_block.append(line)
                in_block = True
            elif in_block:
                current_block.append(line)
                # ブロック終了条件チェック
                if stripped.endswith('##'):
                    blocks.append('\n'.join(current_block))
                    current_block = []
                    in_block = False
        
        # 最後のブロック処理
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出"""
        stripped = block.strip()
        if not stripped:
            return None
            
        # Kumihanブロック記法パターン検出
        if stripped.startswith('#') and '##' in stripped:
            # # 装飾名 #内容## の形式
            if ' #' in stripped and stripped.endswith('##'):
                decoration_part = stripped.split(' #')[0][1:].strip()
                return f"kumihan_{decoration_part}" if decoration_part else "kumihan_basic"
        
        return None
    
    def _validate_kumihan_block(self, line: str) -> bool:
        """Kumihanブロック記法の構文検証"""
        stripped = line.strip()
        if not stripped.startswith('#'):
            return True  # Kumihanブロックでない場合はOK
        
        # # 装飾名 #内容## の基本パターン
        if ' #' in stripped and stripped.endswith('##'):
            parts = stripped.split(' #', 1)
            decoration = parts[0][1:].strip()  # # を除去
            content_with_end = parts[1]
            
            # 装飾名の妥当性
            if not decoration:
                return False
            
            # 内容部分の妥当性（##で終わる）
            if not content_with_end.endswith('##'):
                return False
                
            return True
        
        return False
    
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
    
    def _convert_to_node(self, result: Any, block: str) -> "Node":
        """結果をNodeオブジェクトに変換"""
        from ..core.ast_nodes.node import Node
        
        block_type = self.detect_block_type(block)
        return Node(
            type=block_type or "block",
            content=str(result) if result else block,
            attributes={"original_block": block}
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
                "parser_type": "block"
            }
        )