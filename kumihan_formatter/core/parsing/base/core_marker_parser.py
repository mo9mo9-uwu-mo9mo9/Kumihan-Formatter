"""統合マーカーパーサー

Phase2統合: MarkerParser + MarkerBlockParser の統合実装
- keyword/marker_parser.py の MarkerParser
- block/marker_parser.py の MarkerBlockParser
を統合し、機能別責任分離を実現
"""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

from ...ast_nodes import Node, error_node
from ...utilities.logger import get_logger
from .parser_protocols import ParseResult, ParseContext

if TYPE_CHECKING:
    from ..base.parser_protocols import KeywordParserProtocol
    from ..keyword.attribute_parser import AttributeParser
    from ..keyword.content_parser import ContentParser


class CoreMarkerParser:
    """統合マーカーパーサー - Phase2統合版
    
    機能統合:
    - インライン・ブロック形式マーカー解析
    - 新記法パーシング・ルビ記法処理
    - 色属性・キーワード分離・エラーハンドリング
    
    統合元:
    - MarkerParser (keyword/marker_parser.py) - 395行
    - MarkerBlockParser (block/marker_parser.py) - 287行
    → 統合後: 機能別責任分離実現
    """

    def __init__(
        self, 
        definitions: Any = None,
        keyword_parser: Optional["KeywordParserProtocol"] = None
    ) -> None:
        """統合マーカーパーサーを初期化

        Args:
            definitions: キーワード定義（レガシー互換性用）
            keyword_parser: キーワードパーサー（プロトコル基準）
        """
        self.definitions = definitions
        self.keyword_parser = keyword_parser
        self.logger = get_logger(__name__)

        # 初期化処理: コンポーネントパーサー
        self._initialize_components()
        
        # 初期化処理: パターンマッチング
        self._initialize_patterns()

    def _initialize_components(self) -> None:
        """コンポーネントパーサーの初期化"""
        try:
            # 分割されたパーサーを使用 - Issue #1168 Parser Responsibility Separation
            from ..specialized.keyword_parser import UnifiedKeywordParser as KeywordParser

            if not self.keyword_parser:
                self.keyword_parser = KeywordParser()

            # AttributeParser, ContentParser の遅延ロード
            self._attribute_parser: Optional["AttributeParser"] = None
            self._content_parser: Optional["ContentParser"] = None
        except Exception as e:
            self.logger.warning(f"コンポーネントパーサー初期化警告: {e}")
            self.keyword_parser = None
            self._attribute_parser = None
            self._content_parser = None

    def _initialize_patterns(self) -> None:
        """パターンマッチングの初期化"""
        # マーカー文字の定義
        self.HASH_MARKERS = ["#", "＃"]  # 半角・全角両対応
        self.BLOCK_END_MARKERS = ["##", "＃＃"]  # ブロック終了マーカー

        # レガシーパターン（後方互換性用）
        self._NEW_FORMAT_PATTERN = re.compile(r"^([#＃])\s*(.+)\s*([#＃])\s*(.*)")
        self._INLINE_CONTENT_PATTERN = re.compile(r"^([#＃])\s*(.+?)\s*([#＃])\s*(.*)")
        self._FORMAT_CHECK_PATTERN = re.compile(r"^[#＃]\s*.+\s*[#＃]")
        self._COLOR_ATTRIBUTE_PATTERN = re.compile(
            r"\s*color=(#?[a-fA-F0-9]{3,6}|[a-zA-Z]+)"
        )
        self._KEYWORD_SPLIT_PATTERN = re.compile(r"[+＋]")

        # パフォーマンス改善のため正規表現を事前コンパイル
        self._inline_pattern_1 = re.compile(r"^[#＃]\s*([^#＃]+)\s*[#＃]\s+(.+)$")
        self._inline_pattern_2 = re.compile(r"^[#＃]\s*([^#＃]+)\s+([^#＃]+)\s*[#＃]$")
        self._inline_pattern_3 = re.compile(
            r"^[#＃]\s+([^#＃]+)\s+[#＃]([^#＃]+)[#＃][#＃]$"
        )

        # ブロック記法パターン
        self._basic_pattern = re.compile(r"^[#＃]\s*[^#＃]+\s*[#＃]$")
        self._attribute_pattern = re.compile(r"^[#＃]\s*[^#＃]+\s+[^#＃]+=\S+\s*[#＃]$")
        self._compound_pattern = re.compile(r"^[#＃]\s*[^#＃]+[+＋][^#＃]+\s*[#＃]$")

        # リストアイテムパターン
        self._list_item_pattern = re.compile(r"^\d+\.\s")

    @property
    def attribute_parser(self) -> Optional["AttributeParser"]:
        """AttributeParserの遅延ロード"""
        if self._attribute_parser is None:
            try:
                from ..keyword.attribute_parser import AttributeParser
                self._attribute_parser = AttributeParser()
            except ImportError:
                pass
        return self._attribute_parser

    @property
    def content_parser(self) -> Optional["ContentParser"]:
        """ContentParserの遅延ロード"""
        if self._content_parser is None:
            try:
                from ..keyword.content_parser import ContentParser
                self._content_parser = ContentParser()
            except ImportError:
                pass
        return self._content_parser

    # ===== インライン形式解析 =====

    def parse(self, text: str) -> ParseResult | None:
        """テキストを解析してマーカー情報を抽出（新記法のみ対応）
        
        主要機能:
        - インライン形式の解析
        - ルビ記法の特殊処理  
        - 属性解析（color=, alt= など）
        - ブロック形式のフォールバック

        Args:
            text: 解析対象のテキスト

        Returns:
            ParseResult: 解析結果、解析対象がない場合はNone
        """
        text = text.strip()
        if not text:
            return None

        # インライン形式の解析
        all_keywords = []
        all_content = []
        all_attributes = {}
        i = 0

        while i < len(text):
            if text[i] in self.HASH_MARKERS:
                start_pos = i
                start_marker = text[i]
                i += 1

                # 有効なマーカーペアを探す
                end_pos = self._find_matching_marker(text, start_pos, start_marker)

                if end_pos > start_pos:
                    # マーカー内容を抽出
                    full_content = text[start_pos + 1 : end_pos].strip()

                    if full_content:
                        # キーワードとコンテンツを分離
                        parts = full_content.split(None, 1)

                        if parts:
                            keyword = parts[0]
                            content = parts[1] if len(parts) > 1 else ""

                            # ルビ記法の特殊処理
                            ruby_result = None
                            if keyword == "ルビ":
                                ruby_result = self._parse_ruby_content(content)
                            if ruby_result:
                                all_attributes.update(ruby_result)
                                all_keywords.append(keyword)
                                if content:
                                    all_content.append(content.strip())
                                continue

                        # 属性解析（color=, alt= など）
                        if "color=" in keyword:
                            # color属性の処理
                            _, attrs, _ = self.parse_marker_keywords(full_content)
                            all_attributes.update(attrs)
                            # color属性を除いたキーワードを抽出
                            keyword = self._COLOR_ATTRIBUTE_PATTERN.sub(
                                "", keyword
                            ).strip()

                        all_keywords.append(keyword)
                        if content:
                            all_content.append(content.strip())

                    # 処理した部分をスキップ
                    i = end_pos + 1
                else:
                    # 対応する終了マーカーがない場合は次の文字へ
                    i += 1
            else:
                i += 1

        # ブロック形式もチェック（インライン形式が見つからない場合）
        if not all_keywords:
            block_pattern = r"^[#＃]([^#＃]+?)$"
            block_match = re.match(block_pattern, text)
            if block_match:
                keyword_part = block_match.group(1).strip()
                keyword = keyword_part.split()[0] if keyword_part.split() else ""
                return ParseResult(
                    markers=[(0, len(keyword), keyword)] if keyword else [],
                    content="",
                    keywords=[keyword] if keyword else [],
                    attributes={},
                    errors=[],
                )
            return None

        # 結果をまとめる
        if all_keywords:
            combined_content = " ".join(all_content) if all_content else ""
            return ParseResult(
                markers=[(i, len(kw), kw) for i, kw in enumerate(all_keywords)],
                content=combined_content,
                keywords=all_keywords,
                attributes=all_attributes,
                errors=[],
            )

        return None

    def _find_matching_marker(
        self, text: str, start_pos: int, start_marker: str
    ) -> int:
        """開始マーカーに対応する終了マーカーを見つける"""
        remaining_text = text[start_pos + 1 :]
        marker_positions = []

        # すべてのマーカー位置を収集
        for i, char in enumerate(remaining_text):
            if char == start_marker:
                abs_pos = start_pos + 1 + i
                marker_positions.append(abs_pos)

        if not marker_positions:
            return -1

        # 最も近い有効なマーカーを探す
        for pos in marker_positions:
            content_to_pos = text[start_pos + 1 : pos]
            if self._is_valid_marker_content(content_to_pos):
                return pos

        return -1

    def _is_valid_marker_content(self, content: str) -> bool:
        """マーカー内容が有効かどうかをチェック（簡素化版）"""
        content = content.strip()
        if not content:
            return False
        return True

    def _parse_ruby_content(self, content: str) -> dict[str, Any] | None:
        """ルビ記法のコンテンツを解析"""
        if not content:
            return None

        # 簡略化されたルビ解析
        ruby_pattern = r"([^()（）]+)[()（]([^()（）]+)[)）]"
        match = re.search(ruby_pattern, content)

        if match:
            base_text = match.group(1).strip()
            ruby_text = match.group(2).strip()

            # 混在チェック
            if "(" in content and "（" in content:
                return None  # 混在は無効

            return {"ruby_base": base_text, "ruby_text": ruby_text}

        return None

    # ===== ブロック形式解析 =====

    def parse_new_format_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple[Node, int]:
        """新形式マーカーを解析（ブロック形式対応）

        Args:
            lines: 入力行のリスト
            start_index: 解析開始インデックス

        Returns:
            解析結果ノードと次のインデックスのタプル
        """
        if start_index >= len(lines):
            return (
                error_node(
                    f"マーカー解析エラー: 開始インデックス {start_index} が行数 {len(lines)} を超えています",
                    start_index,
                ),
                start_index + 1,
            )

        try:
            # 開始行を取得して解析
            opening_line = lines[start_index]

            # キーワードパーサーを使用してマーカーを解析
            if not self.keyword_parser:
                return (
                    error_node(
                        "パーサーエラー: キーワードパーサーが利用できません",
                        start_index,
                    ),
                    start_index + 1,
                )

            parse_result = self.keyword_parser.parse_new_format(opening_line)
            if not parse_result:
                return (
                    error_node(
                        f"マーカー解析エラー: 新形式マーカーの解析に失敗しました: {opening_line}",
                        start_index,
                    ),
                    start_index + 1,
                )

            # 解析結果を抽出
            keywords, attributes, parse_errors = parse_result

            if parse_errors:
                self.logger.warning(f"Parse errors in marker: {parse_errors}")

            # インライン内容をチェック
            inline_content = self._extract_inline_content(
                opening_line, [keywords] if isinstance(keywords, str) else keywords
            )
            if inline_content:
                # インライン形式として処理
                return self._parse_inline_format(
                    [keywords] if isinstance(keywords, str) else keywords,
                    (
                        {"content": attributes}
                        if isinstance(attributes, str)
                        else attributes
                    ),
                    inline_content,
                    start_index,
                )

            # デフォルトフォールバック（非インラインマーカー用）
            return (
                error_node(
                    "マーカー解析エラー: ブロック形式のマーカー処理が未実装です",
                    start_index,
                ),
                start_index + 1,
            )
        except Exception as e:
            return (
                error_node(
                    f"マーカー解析エラー: 解析中にエラーが発生しました: {e}",
                    start_index,
                ),
                start_index + 1,
            )

    def _extract_inline_content(self, line: str, keywords: List[str]) -> str:
        """マーカー行からインライン内容を抽出

        Args:
            line: マーカー行
            keywords: 解析されたキーワード

        Returns:
            インライン内容（存在する場合）、なければ空文字列
        """
        # シンプルなインライン内容検出
        # これは簡略化された実装 - 実際のロジックはより複雑かもしれません
        if " #" in line and line.strip().endswith("#"):
            # キーワードと終了 # の間のコンテンツを探す
            parts = line.split("#")
            if len(parts) >= 3:
                return parts[-2].strip()

        return ""

    def _parse_inline_format(
        self,
        keywords: List[str],
        attributes: Dict[str, Any],
        content: str,
        start_index: int,
    ) -> Tuple[Node, int]:
        """インライン形式マーカーを解析

        Args:
            keywords: 解析されたキーワード
            attributes: 解析された属性
            content: インライン内容
            start_index: 開始インデックス

        Returns:
            解析結果ノードと次のインデックスのタプル
        """
        if not keywords:
            return (
                error_node(
                    "インライン解析エラー: キーワードが指定されていません",
                    start_index,
                ),
                start_index + 1,
            )

        # プライマリキーワードを取得
        primary_keyword = keywords[0]

        # キーワード用のノードを作成
        node = self._create_node_for_keyword(primary_keyword, content)
        if node:
            self._apply_attributes_to_node(node, attributes)

        return node or self._create_error_node(start_index), start_index + 1

    def _create_node_for_keyword(self, keyword: str, content: str) -> Optional[Node]:
        """指定されたキーワードと内容に適したノードを作成

        Args:
            keyword: プライマリキーワード
            content: ノード内容

        Returns:
            作成されたノード、キーワードが認識されない場合はNone
        """
        # キーワードからノードタイプへのマッピング
        keyword_mapping = {
            "太字": "BoldNode",
            "イタリック": "ItalicNode",
            "見出し1": "HeadingNode",
            "見出し2": "HeadingNode",
            "見出し3": "HeadingNode",
            "見出し4": "HeadingNode",
            "見出し5": "HeadingNode",
            "ハイライト": "HighlightNode",
        }

        if keyword in keyword_mapping:
            # キーワード用のファクトリ関数を取得
            factory_func = (
                self.keyword_parser.get_node_factory() if self.keyword_parser else None
            )

            if factory_func:
                return cast(Node | None, factory_func(content))

        return None

    def _apply_attributes_to_node(
        self, node: Node, attributes: Dict[str, Any]
    ) -> None:
        """ノードに属性を適用

        Args:
            node: 対象ノード
            attributes: 適用する属性
        """
        for key, value in attributes.items():
            if hasattr(node, key):
                setattr(node, key, value)

    def _create_error_node(self, start_index: int) -> Node:
        """解析失敗用のエラーノードを作成

        Args:
            start_index: エラーが発生したインデックス

        Returns:
            エラーノード
        """
        return error_node("マーカー解析エラー: ノード作成に失敗しました", start_index)

    # ===== 新記法解析 =====

    def parse_new_marker_format(
        self, line: str
    ) -> tuple[list[str], dict[str, Any], list[str]] | None:
        """新記法 # キーワード # 形式のマーカーを解析"""
        line = line.strip()

        # 手動で最後の#マーカーを探す（color属性対応）
        if not (line.startswith("#") or line.startswith("＃")):
            return None

        last_hash_pos = -1
        for i in range(len(line) - 1, 0, -1):
            if line[i] in ("#", "＃"):
                last_hash_pos = i
                break

        if last_hash_pos == -1 or last_hash_pos == 0:
            return None

        start_marker = line[0]
        keyword_part = line[1:last_hash_pos]
        end_marker = line[last_hash_pos]

        if not keyword_part.strip():
            return (
                [],
                {},
                [
                    f"無効なマーカー文字: {start_marker}{keyword_part}{end_marker}。"
                    "正しい形式: # キーワード # または ＃キーワード＃"
                ],
            )

        # キーワード部分と属性を解析
        keywords, attributes, errors = self.parse_marker_keywords(keyword_part)

        # 新記法固有の検証
        additional_errors = self._validate_new_format_syntax(
            start_marker, end_marker, keyword_part
        )
        errors.extend(additional_errors)

        return keywords, attributes, errors

    def _validate_new_format_syntax(
        self, start_marker: str, end_marker: str, keyword_part: str
    ) -> list[str]:
        """新記法固有の構文検証"""
        errors: List[str] = []

        # 空のキーワード部分チェック
        if not keyword_part.strip():
            errors.append(
                "キーワードが指定されていません。例: # 太字 # または # 見出し1 #"
            )

        # キーワード長さチェック
        if len(keyword_part.strip()) > 50:
            errors.append(
                f"キーワードが長すぎます（50文字以内）: '{keyword_part[:20]}...'"
            )

        # 不正文字チェック
        invalid_chars = set(keyword_part) & {"<", ">", '"', "'", "&"}
        if invalid_chars:
            errors.append(f"無効な文字が含まれています: {', '.join(invalid_chars)}")

        # Markdownとの競合チェック
        if keyword_part.strip().isdigit():
            errors.append(
                f"数字のみのキーワード '{keyword_part}' はMarkdown見出しと競合します"
            )

        # 予約語チェック
        reserved_words = ["#", "##", "###", "javascript:", "data:", "vbscript:"]
        if keyword_part.strip().lower() in [w.lower() for w in reserved_words]:
            errors.append(f"予約語 '{keyword_part}' は使用できません")

        # 空白のみの複合キーワードチェック
        if "+" in keyword_part or "＋" in keyword_part:
            parts = self._KEYWORD_SPLIT_PATTERN.split(keyword_part)
            empty_parts = [i for i, part in enumerate(parts) if not part.strip()]
            if empty_parts:
                errors.append(
                    f"複合キーワードに空の部分があります（位置: {empty_parts}）"
                )

        return errors

    # ===== 委譲メソッド =====

    def parse_marker_keywords(
        self, marker_content: str
    ) -> tuple[list[str], dict[str, Any], list[str]]:
        """マーカーコンテンツからキーワードと属性を解析"""
        if self.keyword_parser:
            return self.keyword_parser.parse_marker_keywords(marker_content)
        return [marker_content], {}, []

    def extract_color_attribute(self, marker_content: str) -> tuple[str, str]:
        """マーカーコンテンツからcolor属性を抽出"""
        if self.attribute_parser:
            return self.attribute_parser.extract_color_attribute(marker_content)
        return marker_content, ""

    def split_compound_keywords(self, keyword_content: str) -> list[str]:
        """複合キーワードを分割"""
        if self.keyword_parser:
            return self.keyword_parser.split_compound_keywords(keyword_content)
        return [keyword_content]

    def normalize_marker_syntax(self, marker_content: str) -> str:
        """マーカー構文正規化"""
        if self.content_parser:
            return self.content_parser.normalize_marker_syntax(marker_content)
        return marker_content

    def is_new_marker_format(self, line: str) -> bool:
        """行が新記法 # キーワード # 形式かどうかを判定"""
        if self.content_parser:
            return self.content_parser.is_new_marker_format(line)
        return bool(self._FORMAT_CHECK_PATTERN.match(line))

    def is_block_end_marker(self, line: str) -> bool:
        """行がブロック終了マーカー ## または ＃＃ かどうかを判定"""
        if self.content_parser:
            return self.content_parser.is_block_end_marker(line)
        return line.strip() in self.BLOCK_END_MARKERS

    def extract_inline_content(self, line: str) -> str | None:
        """インライン記法からコンテンツを抽出"""
        if self.content_parser:
            return self.content_parser.extract_inline_content(line)
        return None

    # ===== レガシー互換性メソッド =====

    def parse_footnotes(self, text: str) -> list[dict[str, Any]]:
        """廃止済み脚注パーサー - 新記法ブロック形式に移行"""
        self.logger.warning(
            "parse_footnotes() is deprecated. "
            "Use new block format '# 脚注 #内容##' instead."
        )
        return []

    def extract_footnotes_from_text(
        self, text: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """廃止済み脚注抽出機能 - 新記法ブロック形式に移行"""
        self.logger.warning(
            "extract_footnotes_from_text() is deprecated. "
            "Use new block format '# 脚注 #内容##' instead."
        )
        return text, []

    def parse_block_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple[Node, int]:
        """ブロックマーカーを解析（メインエントリーポイント）

        Args:
            lines: 入力行のリスト
            start_index: 解析開始インデックス

        Returns:
            解析結果ノードと次のインデックスのタプル
        """
        # 新形式パーサーに委譲
        return self.parse_new_format_marker(lines, start_index)

    def _is_simple_image_marker(self, line: str) -> bool:
        """行がシンプルな画像マーカーかどうかをチェック

        Args:
            line: チェックする行

        Returns:
            シンプルな画像マーカーの場合True
        """
        if not self.keyword_parser:
            return False

        # 画像ファイル拡張子をチェック
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
        return any(line.lower().endswith(ext) for ext in image_extensions)

    # ===== セキュリティ・サニタイゼーション =====

    def _contains_color_attribute(self, content: str) -> bool:
        """コンテンツにcolor属性が含まれているかをチェック"""
        return bool(self._COLOR_ATTRIBUTE_PATTERN.search(content))

    def _contains_malicious_content(self, content: str) -> bool:
        """脚注内容に悪意のあるコンテンツが含まれているかチェック"""
        if not content:
            return False

        malicious_patterns = ["<script", "javascript:", "data:", "vbscript:"]
        content_lower = content.lower()
        for pattern in malicious_patterns:
            if pattern in content_lower:
                return True
        return False

    def _sanitize_footnote_content(self, content: str) -> str:
        """脚注内容のサニタイゼーション"""
        if not content:
            return ""
        return content.strip()

    def _validate_footnote_structure(self, footnotes: list[Any]) -> list[str]:
        """脚注構造の妥当性検証"""
        errors: list[str] = []
        if not footnotes:
            return errors
        return errors

    def _sanitize_color_attribute(self, color_value: str) -> str:
        """color属性値をサニタイゼーション"""
        sanitized = color_value.strip()
        sanitized = sanitized.replace("&", "&amp;")
        sanitized = sanitized.replace("<", "&lt;")
        sanitized = sanitized.replace(">", "&gt;")
        sanitized = sanitized.replace('"', "&quot;")
        sanitized = sanitized.replace("'", "&#x27;")
        if sanitized.lower().startswith(("javascript:", "data:", "vbscript:")):
            return "#000000"
        return sanitized