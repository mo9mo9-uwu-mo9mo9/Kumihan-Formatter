"""統一ブロックパーサー

Issue #880 Phase 2B: 既存のBlockParser系統を統合
- core/block_parser/block_parser.py
- core/block_parser/special_block_parser.py
- core/block_parser/*_parser.py
の機能を統合・整理
"""

import re
from typing import Any, Callable, Dict, List, Optional, Union

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..base.parser_protocols import (
    BlockParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..protocols import ParserType


class UnifiedBlockParser(UnifiedParserBase, CompositeMixin, BlockParserProtocol):
    """統一ブロックパーサー

    Kumihan記法のブロック構文を解析:
    - インラインブロック: #キーワード#内容##
    - 複数行ブロック: #キーワード# ... ##
    - 特殊ブロック: 画像、コード、引用など
    - 属性付きブロック: [color:red]などの装飾
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.BLOCK)

        # ブロック解析の設定
        self._setup_block_patterns()
        self._setup_special_handlers()

    def _setup_block_patterns(self) -> None:
        """ブロック解析パターンの設定"""
        # 基本ブロックパターン
        self.block_patterns = {
            # インラインブロック: #キーワード#内容##
            "inline": re.compile(r"^#\s*([^#]+?)\s*#([^#]*?)##\s*$"),
            # ブロック開始: #キーワード# (属性対応)
            "start": re.compile(r"^#\s*([^#]+?)\s*#\s*(.*)$"),
            # ブロック終了: ##
            "end": re.compile(r"^##\s*$"),
            # 属性パターン: [key:value] [color:red] など
            "attributes": re.compile(r"\[([^\]]+)\]"),
            # 特殊ブロックパターン
            "image": re.compile(r"^#画像#\s*(.+?)##\s*$"),
            "code": re.compile(r"^#コード#\s*(.+?)##\s*$"),
            "quote": re.compile(r"^#引用#\s*(.+?)##\s*$"),
        }

    def _setup_special_handlers(self) -> None:
        """特殊ブロックハンドラーの設定"""
        self.special_handlers = {
            "画像": self._handle_image_block,
            "イメージ": self._handle_image_block,
            "image": self._handle_image_block,
            "コード": self._handle_code_block,
            "code": self._handle_code_block,
            "引用": self._handle_quote_block,
            "quote": self._handle_quote_block,
            "重要": self._handle_important_block,
            "important": self._handle_important_block,
            "注意": self._handle_warning_block,
            "warning": self._handle_warning_block,
        }

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """ブロック記法の解析可能性を判定"""
        if not super().can_parse(content):
            return False

        text = content if isinstance(content, str) else "\n".join(content)

        # Kumihanブロック記法の特徴を検出
        return bool(
            self.block_patterns["inline"].search(text)
            or self.block_patterns["start"].search(text)
            or self._contains_block_markers(text)
        )

    def _contains_block_markers(self, text: str) -> bool:
        """ブロックマーカーが含まれているかチェック"""
        lines = text.split("\n")
        has_start = False
        has_end = False

        for line in lines:
            line = line.strip()
            if line.startswith("#") and not line.startswith("##"):
                has_start = True
            elif line == "##":
                has_end = True

            # インラインブロックの場合
            if self.block_patterns["inline"].match(line):
                return True

        return has_start or has_end

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """ブロック解析の実装"""
        self._start_timer("block_parsing")

        try:
            if isinstance(content, str):
                lines = content.split("\n")
            else:
                lines = content

            # 解析結果を格納するノード
            root_node = create_node("document", content="")

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                if not line:
                    i += 1
                    continue

                # インラインブロックの処理
                inline_match = self.block_patterns["inline"].match(line)
                if inline_match:
                    block_node = self._parse_inline_block(line, inline_match)
                    if block_node and root_node.children is not None:
                        root_node.children.append(block_node)
                    i += 1
                    continue

                # 複数行ブロックの処理
                start_match = self.block_patterns["start"].match(line)
                if start_match:
                    block_node, consumed_lines = self._parse_multiline_block(lines[i:])
                    if block_node and root_node.children is not None:
                        root_node.children.append(block_node)
                    i += consumed_lines
                    continue

                # 通常のテキスト行として処理
                text_node = create_node("text", content=line)
                if root_node.children is not None:
                    root_node.children.append(text_node)
                i += 1

            self._end_timer("block_parsing")
            return root_node

        except Exception as e:
            self.add_error(f"ブロック解析エラー: {str(e)}")
            return create_node("error", content=f"Parse error: {e}")

    def _parse_inline_block(self, line: str, match: re.Match) -> Optional[Node]:
        """インラインブロックの解析"""
        keyword = match.group(1).strip()
        content = match.group(2).strip()

        # 属性の抽出
        clean_keyword, attributes = self._extract_attributes(keyword)

        # 特殊ブロックハンドラーの適用
        if clean_keyword.lower() in self.special_handlers:
            handler = self.special_handlers[clean_keyword.lower()]
            return handler(clean_keyword, content, attributes, inline=True)

        # 通常のブロックノード作成
        block_node = create_node("block", content=content)
        block_node.metadata.update(
            {"keyword": clean_keyword, "type": "inline", "attributes": attributes}
        )

        return block_node

    def _parse_multiline_block(self, lines: List[str]) -> tuple[Optional[Node], int]:
        """複数行ブロックの解析"""
        if not lines:
            return None, 0

        start_line = lines[0].strip()
        start_match = self.block_patterns["start"].match(start_line)

        if not start_match:
            return None, 0

        keyword = start_match.group(1).strip()
        start_attributes = start_match.group(2).strip()

        # 属性の抽出
        clean_keyword, attributes = self._extract_attributes(keyword)
        if start_attributes:
            _, start_attrs = self._extract_attributes(start_attributes)
            attributes.update(start_attrs)

        # ブロック終了を探す
        content_lines = []
        i = 1

        while i < len(lines):
            line = lines[i].strip()

            if self.block_patterns["end"].match(line):
                # ブロック終了
                break

            content_lines.append(lines[i])
            i += 1

        # ブロック内容の処理
        content = "\n".join(content_lines).strip()

        # 特殊ブロックハンドラーの適用
        if clean_keyword.lower() in self.special_handlers:
            handler = self.special_handlers[clean_keyword.lower()]
            block_node = handler(clean_keyword, content, attributes, inline=False)
        else:
            # 通常のブロックノード作成
            block_node = create_node("block", content=content)
            block_node.metadata.update(
                {
                    "keyword": clean_keyword,
                    "type": "multiline",
                    "attributes": attributes,
                }
            )

        return block_node, i + 1

    def _handle_image_block(
        self,
        keyword: str,
        content: str,
        attributes: Dict[str, str],
        inline: bool = True,
    ) -> Node:
        """画像ブロックの処理"""
        node = create_node("image", content=content)
        node.metadata.update(
            {
                "keyword": keyword,
                "type": "image",
                "inline": inline,
                "attributes": attributes,
            }
        )

        # 画像固有の属性処理
        if "alt" not in attributes and content:
            # コンテンツから代替テキストを抽出
            parts = content.split("|")
            if len(parts) > 1:
                node.metadata["src"] = parts[0].strip()
                node.metadata["alt"] = parts[1].strip()
            else:
                node.metadata["src"] = content.strip()

        return node

    def _handle_code_block(
        self,
        keyword: str,
        content: str,
        attributes: Dict[str, str],
        inline: bool = True,
    ) -> Node:
        """コードブロックの処理"""
        node = create_node("code", content=content)
        node.metadata.update(
            {
                "keyword": keyword,
                "type": "code",
                "inline": inline,
                "attributes": attributes,
            }
        )

        # 言語指定の処理
        if "lang" in attributes:
            node.metadata["language"] = attributes["lang"]
        elif "language" in attributes:
            node.metadata["language"] = attributes["language"]

        return node

    def _handle_quote_block(
        self,
        keyword: str,
        content: str,
        attributes: Dict[str, str],
        inline: bool = True,
    ) -> Node:
        """引用ブロックの処理"""
        node = create_node("quote", content=content)
        node.metadata.update(
            {
                "keyword": keyword,
                "type": "quote",
                "inline": inline,
                "attributes": attributes,
            }
        )

        # 引用元の処理
        if "author" in attributes:
            node.metadata["author"] = attributes["author"]
        if "source" in attributes:
            node.metadata["source"] = attributes["source"]

        return node

    def _handle_important_block(
        self,
        keyword: str,
        content: str,
        attributes: Dict[str, str],
        inline: bool = True,
    ) -> Node:
        """重要ブロックの処理"""
        node = create_node("important", content=content)
        node.metadata.update(
            {
                "keyword": keyword,
                "type": "important",
                "inline": inline,
                "attributes": attributes,
                "priority": "high",
            }
        )

        return node

    def _handle_warning_block(
        self,
        keyword: str,
        content: str,
        attributes: Dict[str, str],
        inline: bool = True,
    ) -> Node:
        """注意ブロックの処理"""
        node = create_node("warning", content=content)
        node.metadata.update(
            {
                "keyword": keyword,
                "type": "warning",
                "inline": inline,
                "attributes": attributes,
                "level": attributes.get("level", "medium"),
            }
        )

        return node

    def parse_block_content(self, content: str, keyword: str) -> Node:
        """外部API: 指定キーワードでブロック内容を解析"""
        if keyword.lower() in self.special_handlers:
            handler = self.special_handlers[keyword.lower()]
            return handler(keyword, content, {}, inline=False)
        else:
            node = create_node("block", content=content)
            node.metadata.update({"keyword": keyword, "type": "custom"})
            return node

    def get_supported_keywords(self) -> List[str]:
        """サポートされているキーワード一覧を取得"""
        return list(self.special_handlers.keys())

    def register_special_handler(
        self, keyword: str, handler: Callable[..., Any]
    ) -> None:
        """カスタム特殊ブロックハンドラーを登録"""
        self.special_handlers[keyword.lower()] = handler
        self.logger.info(f"Registered special handler for keyword: {keyword}")

    def get_block_statistics(self) -> Dict[str, Any]:
        """ブロック解析統計を取得"""
        stats = self._get_performance_stats()
        stats.update(
            {
                "supported_keywords": len(self.special_handlers),
                "parser_type": self.parser_type,
            }
        )
        return stats

    # ==========================================
    # プロトコル準拠メソッド（BlockParserProtocol実装）
    # ==========================================

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース（プロトコル準拠）"""
        try:
            result = self._parse_implementation(content)
            nodes = [result] if isinstance(result, Node) else result
            return create_parse_result(nodes=nodes, success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"ブロックパース失敗: {e}")
            return result

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            # ブロック構文の基本チェック
            lines = content.split("\n")
            open_blocks = 0
            for i, line in enumerate(lines):
                if self.block_patterns["start"].match(line):
                    open_blocks += 1
                elif self.block_patterns["end"].match(line):
                    open_blocks -= 1
                    if open_blocks < 0:
                        errors.append(
                            f"行{i+1}: 対応するブロック開始がない終了マーカー"
                        )

            if open_blocks > 0:
                errors.append(f"未閉じのブロックが{open_blocks}個あります")

        except Exception as e:
            errors.append(f"バリデーションエラー: {e}")
        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedBlockParser",
            "version": "2.0.0",
            "supported_formats": ["kumihan", "block"],
            "capabilities": [
                "inline_blocks",
                "multiline_blocks",
                "special_blocks",
                "attributes",
            ],
            "parser_type": self.parser_type,
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["kumihan", "block", "text"]

    def parse_block(self, content: str, keyword: Optional[str] = None) -> Node:
        """ブロック固有パースメソッド（プロトコル準拠）"""
        if keyword:
            return self.parse_block_content(content, keyword)
        else:
            return self._parse_implementation(content)
