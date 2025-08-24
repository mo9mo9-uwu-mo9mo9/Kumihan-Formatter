"""Block Handlers - ブロック処理ハンドラー群

責任分離による構造:
- KumihanBlockHandler: Kumihanブロック記法処理
- TextBlockHandler: テキスト・段落ブロック処理
- ImageBlockHandler: 画像・メディアブロック処理
- SpecialBlockHandler: 特殊ブロック（コード・引用等）処理
- MarkerBlockHandler: マーカーブロック処理
- ContentBlockHandler: 汎用コンテンツブロック処理
- ListBlockHandler: リストブロック処理
"""

import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.ast_nodes import Node
else:
    try:
        from ...core.ast_nodes import Node, create_node
    except ImportError:
        Node = None
        create_node = None

from ...core.utilities.logger import get_logger


class KumihanBlockHandler:
    """Kumihanブロック記法処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._setup_patterns()
    
    def _setup_patterns(self) -> None:
        """Kumihanパターンの設定"""
        self.kumihan_pattern = re.compile(r"^#\s*([^#]+)\s*#([^#]*)##$")
        self.kumihan_opening_pattern = re.compile(r"^#\s*([^#]+)\s*#")
    
    def handle_kumihan_block(self, block: str) -> "Node":
        """Kumihanブロック処理"""
        lines = block.split("\n")
        first_line = lines[0].strip()

        # 単行形式: # keyword #content##
        match = self.kumihan_pattern.match(first_line)
        if match:
            keyword, content = match.groups()
            return create_node(
                "kumihan_block",
                content=content.strip(),
                attributes={"keyword": keyword.strip(), "format": "inline"},
            )

        # 複数行形式: # keyword # ... ##
        match = self.kumihan_opening_pattern.match(first_line)
        if match:
            keyword = match.group(1).strip()
            content_lines = []

            for line in lines[1:]:
                if line.strip() == "##":
                    break
                content_lines.append(line)

            return create_node(
                "kumihan_block",
                content="\n".join(content_lines).strip(),
                attributes={"keyword": keyword, "format": "multiline"},
            )

        # フォールバック
        return create_node("text", content=block)
    
    def is_kumihan_opening(self, line: str) -> bool:
        """Kumihan開始行かチェック"""
        return bool(self.kumihan_opening_pattern.match(line))
    
    def validate_kumihan_syntax(self, line: str) -> bool:
        """Kumihan記法の構文チェック"""
        return bool(self.kumihan_pattern.match(line.strip()))
    
    def validate_kumihan_block_syntax(self, block: str) -> bool:
        """Kumihanブロック構文の詳細検証"""
        lines = block.split("\n")
        first_line = lines[0].strip()

        # 単行形式チェック
        if self.kumihan_pattern.match(first_line):
            return True

        # 複数行形式チェック
        if self.kumihan_opening_pattern.match(first_line):
            # 終了マーカー確認
            for line in lines[1:]:
                if line.strip() == "##":
                    return True

        return False


class TextBlockHandler:
    """テキスト・段落ブロック処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def handle_text_block(self, block: str) -> "Node":
        """テキストブロック処理"""
        return create_node(
            "text_block", content=block.strip(), attributes={"type": "paragraph"}
        )


class ImageBlockHandler:
    """画像・メディアブロック処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    
    def handle_image_block(self, block: str) -> "Node":
        """画像ブロック処理"""
        match = self.image_pattern.search(block)
        if match:
            alt_text, url = match.groups()
            return create_node(
                "image_block",
                content=url,
                attributes={"alt_text": alt_text, "type": "image"},
            )

        return create_node("text", content=block)


class SpecialBlockHandler:
    """特殊ブロック（コード・引用等）処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._setup_patterns()
    
    def _setup_patterns(self) -> None:
        """特殊ブロックパターンの設定"""
        self.code_block_pattern = re.compile(r"^```(\w+)?")
        self.quote_block_pattern = re.compile(r"^>\s+")
    
    def handle_special_block(self, block: str) -> "Node":
        """特殊ブロック処理"""
        lines = block.split("\n")
        first_line = lines[0].strip()

        # コードブロック
        code_match = self.code_block_pattern.match(first_line)
        if code_match:
            language = code_match.group(1) or "text"
            content = "\n".join(lines[1:]).rstrip().rstrip("```")
            return create_node(
                "code_block", content=content, attributes={"language": language}
            )

        # 引用ブロック
        if self.quote_block_pattern.match(first_line):
            content = "\n".join(line.lstrip("> ") for line in lines)
            return create_node(
                "quote_block",
                content=content.strip(),
                attributes={"type": "blockquote"},
            )

        # その他の特殊ブロック
        return create_node(
            "special_block", content=block.strip(), attributes={"type": "unknown"}
        )


class MarkerBlockHandler:
    """マーカーブロック処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.marker_pattern = re.compile(r"^#\s*[^#]+\s*#[^#]*##")
    
    def handle_marker_block(self, block: str) -> "Node":
        """マーカーブロック処理"""
        return create_node(
            "marker_block", content=block.strip(), attributes={"type": "marker"}
        )
    
    def is_marker_line(self, line: str) -> bool:
        """マーカー行かチェック"""
        return bool(self.marker_pattern.match(line))


class ContentBlockHandler:
    """汎用コンテンツブロック処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def handle_content_block(self, block: str) -> "Node":
        """コンテンツブロック処理"""
        return create_node(
            "content_block", content=block.strip(), attributes={"type": "generic"}
        )


class ListBlockHandler:
    """リストブロック処理ハンドラー"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.list_pattern = re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+")
    
    def handle_list_block(self, block: str) -> "Node":
        """リストブロック処理"""
        return create_node(
            "list_block", content=block.strip(), attributes={"type": "list"}
        )


class BlockValidatorCollection:
    """ブロックバリデーター集合"""
    
    def __init__(self, kumihan_handler: KumihanBlockHandler):
        self.logger = get_logger(__name__)
        self.kumihan_handler = kumihan_handler
        
        self.validators = {
            "syntax": self._validate_block_syntax,
            "structure": self._validate_block_structure,
            "content": self._validate_block_content,
        }
    
    def _validate_block_syntax(self, block: str) -> List[str]:
        """ブロック構文検証"""
        errors = []

        block_type = self._detect_block_type(block)
        if block_type == "kumihan":
            if not self.kumihan_handler.validate_kumihan_block_syntax(block):
                errors.append("Invalid Kumihan block syntax")

        return errors

    def _validate_block_structure(self, block: str) -> List[str]:
        """ブロック構造検証"""
        errors = []

        lines = block.split("\n")
        if not lines:
            errors.append("Empty block")

        return errors

    def _validate_block_content(self, block: str) -> List[str]:
        """ブロックコンテンツ検証"""
        errors = []

        if len(block.strip()) == 0:
            errors.append("Empty content")

        return errors
    
    def _detect_block_type(self, block: str) -> Optional[str]:
        """簡易ブロックタイプ検出（バリデーション用）"""
        if not block.strip():
            return None

        first_line = block.split("\n")[0].strip()
        
        if self.kumihan_handler.kumihan_pattern.match(first_line) or self.kumihan_handler.is_kumihan_opening(first_line):
            return "kumihan"
        
        return "text"


class BlockHandlerCollection:
    """ブロックハンドラー集合クラス - 全ハンドラーの統合管理"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 各種ハンドラー初期化
        self.kumihan_handler = KumihanBlockHandler()
        self.text_handler = TextBlockHandler()
        self.image_handler = ImageBlockHandler()
        self.special_handler = SpecialBlockHandler()
        self.marker_handler = MarkerBlockHandler()
        self.content_handler = ContentBlockHandler()
        self.list_handler = ListBlockHandler()
        
        # バリデーター
        self.validator_collection = BlockValidatorCollection(self.kumihan_handler)
        
        # 統合ハンドラー辞書
        self.handlers = {
            "kumihan": self.kumihan_handler.handle_kumihan_block,
            "text": self.text_handler.handle_text_block,
            "image": self.image_handler.handle_image_block,
            "special": self.special_handler.handle_special_block,
            "marker": self.marker_handler.handle_marker_block,
            "content": self.content_handler.handle_content_block,
            "list": self.list_handler.handle_list_block,
        }
    
    def get_handler(self, block_type: str):
        """指定されたブロックタイプのハンドラーを取得"""
        return self.handlers.get(block_type, self.text_handler.handle_text_block)
    
    def validate_line(self, line: str, line_number: int) -> List[str]:
        """行レベルの検証"""
        errors = []

        # Kumihanブロック記法の検証
        if line.strip().startswith("#") and "##" in line:
            if not self.kumihan_handler.validate_kumihan_syntax(line):
                errors.append(f"Line {line_number}: Invalid Kumihan block syntax")

        return errors
    
    def validate_block(self, block: str, block_number: int) -> List[str]:
        """ブロックレベルの検証"""
        errors = []

        # ブロック構造検証を各バリデーターで実行
        for validator_name, validator in self.validator_collection.validators.items():
            try:
                validator_errors = validator(block)
                for error in validator_errors:
                    errors.append(f"Block {block_number} ({validator_name}): {error}")
            except Exception as e:
                errors.append(
                    f"Block {block_number} validation error ({validator_name}): {e}"
                )

        return errors