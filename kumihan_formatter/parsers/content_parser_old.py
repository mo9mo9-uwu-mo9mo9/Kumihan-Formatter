"""UnifiedContentParser - 統合コンテンツ解析エンジン

Issue #914 Phase 2: 4つのContentParserを統合
- parsers/content_parser.py (プロトコル準拠ベース)
- specialized/content_parser.py (高度コンテンツ解析)
- keyword/content_parser.py (脚注・インライン処理)
- block/content_parser.py (ブロック処理・エラー回復)
"""

import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import (
        ParseResult,
        ParseContext,
        BaseParserProtocol,
    )
    from ..core.ast_nodes.node import Node
else:
    BaseParserProtocol = object


class UnifiedContentParser(BaseParserProtocol):
    """統合コンテンツ解析エンジン - BaseParserProtocol実装

    機能統合:
    - プロトコル準拠インターface (BaseParserProtocol)
    - 高度コンテンツ解析・分類・エンティティ抽出
    - 脚注・インラインコンテンツ処理
    - ブロック処理・エラー回復機能
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        # Core parser initialization (fallback)
        self.core_parser = None
        try:
            from ..core.parsing.specialized.content_parser import (
                UnifiedContentParser as CoreContentParser,
            )

            self.core_parser = CoreContentParser()
        except ImportError:
            self.logger.warning(
                "Core content parser not available, using built-in implementation"
            )

        # Content analysis patterns
        self._setup_content_patterns()
        self._setup_content_classifiers()
        self._setup_structure_analyzers()

        self.logger.info("UnifiedContentParser initialized with full functionality")

    def _setup_content_patterns(self) -> None:
        """コンテンツ解析パターンの設定"""
        self.content_patterns = {
            # 段落区切り: 空行
            "paragraph_break": re.compile(r"\n\s*\n"),
            # 文境界: 句読点 + 空白/改行
            "sentence_break": re.compile(r"[.!?。！？]\s+"),
            # URL: http/https形式
            "url": re.compile(r"https?://[\w\-._~:/?#\[\]@!$&\'()*+,;=%]+"),
            # メールアドレス
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            # 日付パターン: YYYY-MM-DD, YYYY/MM/DD
            "date": re.compile(
                r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\b"
            ),
            # 時刻パターン: HH:MM
            "time": re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),
            # 数値: 整数、小数
            "number": re.compile(r"\b\d+(?:\.\d+)?\b"),
            # 日本語文字
            "japanese": re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"),
            # アルファベット
            "alphabetic": re.compile(r"[A-Za-z]+"),
            # 特殊文字・記号
            "symbols": re.compile(r"[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"),
            # インラインコンテンツパターン
            "inline_content": re.compile(r"^#\s*([^#]+?)\s*#([^#]*?)##$"),
            # 脚注パターン
            "footnote": re.compile(r"\[\^([^\]]+)\]"),
        }

    def _setup_content_classifiers(self) -> None:
        """コンテンツ分類器の設定"""
        self.content_classifiers = {
            "text_type": self._classify_text_type,
            "language": self._classify_language,
            "structure": self._classify_structure,
            "complexity": self._classify_complexity,
        }

    def _setup_structure_analyzers(self) -> None:
        """構造解析器の設定"""
        self.structure_analyzers = {
            "paragraph": self._analyze_paragraphs,
            "sentence": self._analyze_sentences,
            "entity": self._analyze_entities,
            "semantic": self._analyze_semantic_structure,
        }

    def parse(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> "ParseResult":
        """統一コンテンツ解析 - BaseParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        from ..core.ast_nodes.node import Node

        try:
            # Core parser がある場合は優先使用
            if self.core_parser:
                try:
                    legacy_result = self.core_parser.parse(content)
                    return self._convert_to_parse_result(legacy_result)
                except Exception as e:
                    self.logger.warning(f"Core parser failed, using built-in: {e}")

            # 統合解析実装
            all_nodes = []

            # 1. コンテンツ分類
            classification = self._classify_content(content)

            # 2. 構造解析
            structure = self._analyze_content_structure(content)

            # 3. エンティティ抽出
            entities = self._extract_entities(content)

            # 4. 脚注抽出
            footnotes = self.extract_footnotes_from_text(content)

            # 5. インラインコンテンツ処理
            inline_processed = self._process_inline_content(content)

            # 6. 段落構造化
            structured_nodes = self._structure_content(
                content, classification, structure
            )
            all_nodes.extend(structured_nodes)

            # 7. 脚注ノード追加
            if footnotes:
                footnote_node = Node(
                    type="footnotes",
                    content="",
                    attributes={"footnotes": footnotes, "count": len(footnotes)},
                )
                all_nodes.append(footnote_node)

            return ParseResult(
                success=True,
                nodes=all_nodes,
                errors=[],
                warnings=[],
                metadata={
                    "classification": classification,
                    "structure": structure,
                    "entities": entities,
                    "footnotes_count": len(footnotes),
                    "parser_type": "unified_content",
                    "inline_processed": inline_processed,
                },
            )

        except Exception as e:
            self.logger.error(f"Content parsing error: {e}")
            return self._create_error_parse_result(str(e), content)

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            errors = []

            # 基本的なコンテンツ検証
            if not content:
                errors.append("Empty content")
                return errors
            elif len(content.strip()) == 0:
                errors.append("Content contains only whitespace")
                return errors

            # 制御文字のチェック
            for i, char in enumerate(content):
                if ord(char) < 32 and char not in ["\n", "\r", "\t"]:
                    errors.append(
                        f"Invalid control character at position {i}: {repr(char)}"
                    )

            # 脚注の検証
            footnotes = self.extract_footnotes_from_text(content)
            footnote_errors = self._validate_footnote_structure(footnotes)
            errors.extend(footnote_errors)

            # インライン記法の検証
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if self.is_new_marker_format(line):
                    if not self._validate_new_format_structure(line):
                        errors.append(f"Invalid inline format at line {i+1}: {line}")

            # ブロック構造の検証
            block_errors = self._validate_block_structure_in_content(content)
            errors.extend(block_errors)

            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedContentParser",
            "version": "3.0.0",
            "supported_formats": [
                "text",
                "content",
                "kumihan",
                "mixed_content",
                "footnotes",
            ],
            "capabilities": [
                "content_parsing",
                "text_processing",
                "content_validation",
                "control_character_detection",
                "content_classification",
                "entity_extraction",
                "semantic_analysis",
                "footnote_parsing",
                "inline_content_extraction",
                "block_error_recovery",
                "structure_analysis",
                "mixed_format_parsing",
            ],
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported

    def _convert_to_parse_result(self, legacy_result: Any) -> "ParseResult":
        """Dict結果をParseResultに変換"""
        from ..core.parsing.base.parser_protocols import ParseResult

        if isinstance(legacy_result, dict):
            return ParseResult(
                success=not legacy_result.get("error"),
                nodes=[],  # TODO: 適切なNode変換
                errors=[legacy_result["error"]] if legacy_result.get("error") else [],
                warnings=[],
                metadata=legacy_result,
            )
        else:
            return ParseResult(
                success=True,
                nodes=[],
                errors=[],
                warnings=[],
                metadata={"raw_result": legacy_result},
            )

    def _create_error_parse_result(
        self, error_msg: str, original_content: str
    ) -> "ParseResult":
        """エラー結果作成"""
        from ..core.parsing.base.parser_protocols import ParseResult

        return ParseResult(
            success=False,
            nodes=[],
            errors=[error_msg],
            warnings=[],
            metadata={
                "original_content": original_content,
                "parser_type": "unified_content",
            },
        )

    # === コンテンツ分類メソッド ===

    def _classify_content(self, text: str) -> Dict[str, Any]:
        """コンテンツの分類"""
        classification = {}

        for classifier_name, classifier_func in self.content_classifiers.items():
            try:
                result = classifier_func(text)
                classification[classifier_name] = result
            except Exception as e:
                self.logger.warning(f"分類エラー ({classifier_name}): {e}")
                classification[classifier_name] = "unknown"

        return classification

    def _classify_text_type(self, text: str) -> str:
        """テキストタイプの分類"""
        # 特殊記法の検出
        if re.search(r"#[^#]+#[^#]*##", text):
            return "kumihan"
        elif re.search(r"^#{1,6}\s", text, re.MULTILINE):
            return "markdown"
        elif re.search(r"<[^>]+>", text):
            return "html"
        elif re.search(r"```|`[^`]+`", text):
            return "code_mixed"
        else:
            return "plain_text"

    def _classify_language(self, text: str) -> str:
        """言語の分類"""
        japanese_chars = len(self.content_patterns["japanese"].findall(text))
        alphabetic_chars = len(self.content_patterns["alphabetic"].findall(text))
        total_chars = len(text.replace(" ", "").replace("\n", ""))

        if total_chars == 0:
            return "unknown"

        japanese_ratio = japanese_chars / total_chars
        alphabetic_ratio = alphabetic_chars / total_chars

        if japanese_ratio > 0.3:
            return "japanese"
        elif alphabetic_ratio > 0.7:
            return "english"
        elif japanese_ratio > 0.1 and alphabetic_ratio > 0.3:
            return "mixed"
        else:
            return "other"

    def _classify_structure(self, text: str) -> str:
        """構造の分類"""
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        if len(non_empty_lines) <= 1:
            return "single_line"
        elif len(self.content_patterns["paragraph_break"].findall(text)) > 0:
            return "multi_paragraph"
        elif len(non_empty_lines) <= 5:
            return "short_text"
        else:
            return "long_text"

    def _classify_complexity(self, text: str) -> str:
        """複雑さの分類"""
        words = text.split()
        unique_words = set(words)

        if len(words) == 0:
            return "empty"

        vocabulary_diversity = len(unique_words) / len(words)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # URLs、メール、特殊記法の存在
        has_special_content = bool(
            self.content_patterns["url"].search(text)
            or self.content_patterns["email"].search(text)
            or re.search(r"[#*`\[\](){}<>]", text)
        )

        if vocabulary_diversity > 0.8 and avg_word_length > 6:
            return "high"
        elif has_special_content or vocabulary_diversity > 0.6:
            return "medium"
        else:
            return "low"

    # === 構造解析メソッド ===

    def _analyze_content_structure(self, text: str) -> Dict[str, Any]:
        """コンテンツ構造の解析"""
        structure = {}

        for analyzer_name, analyzer_func in self.structure_analyzers.items():
            try:
                result = analyzer_func(text)
                structure[analyzer_name] = result
            except Exception as e:
                self.logger.warning(f"構造解析エラー ({analyzer_name}): {e}")
                structure[analyzer_name] = {}

        return structure

    def _analyze_paragraphs(self, text: str) -> Dict[str, Any]:
        """段落解析"""
        paragraphs = self.content_patterns["paragraph_break"].split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return {
            "count": len(paragraphs),
            "lengths": [len(p) for p in paragraphs],
            "avg_length": (
                sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
            ),
        }

    def _analyze_sentences(self, text: str) -> Dict[str, Any]:
        """文解析"""
        sentences = self.content_patterns["sentence_break"].split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        return {
            "count": len(sentences),
            "lengths": [len(s) for s in sentences],
            "avg_length": (
                sum(len(s) for s in sentences) / len(sentences) if sentences else 0
            ),
        }

    def _analyze_entities(self, text: str) -> Dict[str, Any]:
        """エンティティ解析"""
        entities = {}

        # URL抽出
        urls = self.content_patterns["url"].findall(text)
        if urls:
            entities["urls"] = urls

        # メールアドレス抽出
        emails = self.content_patterns["email"].findall(text)
        if emails:
            entities["emails"] = emails

        # 日付抽出
        dates = self.content_patterns["date"].findall(text)
        if dates:
            entities["dates"] = dates

        # 時刻抽出
        times = self.content_patterns["time"].findall(text)
        if times:
            entities["times"] = times

        # 数値抽出
        numbers = self.content_patterns["number"].findall(text)
        if numbers:
            entities["numbers"] = numbers

        return entities

    def _analyze_semantic_structure(self, text: str) -> Dict[str, Any]:
        """意味構造解析"""
        structure: Dict[str, Any] = {
            "has_questions": bool(re.search(r"[？?]", text)),
            "has_exclamations": bool(re.search(r"[！!]", text)),
            "has_quotes": bool(re.search(r'[「」""\'\'"]', text)),
            "has_emphasis": bool(re.search(r"[*_**__]", text)),
            "keywords": [],
        }

        # キーワード密度の簡単な分析
        words = text.split()
        word_freq: Dict[str, int] = {}
        for word in words:
            word = word.lower().strip(".,!?。！？")
            word_freq[word] = word_freq.get(word, 0) + 1

        # 高頻度語の抽出
        if word_freq:
            max_freq = max(word_freq.values())
            high_freq_words = [
                word
                for word, freq in word_freq.items()
                if freq >= max_freq * 0.5 and len(word) > 2
            ]
            structure["keywords"] = high_freq_words[:10]

        return structure

    # === エンティティ抽出メソッド ===

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """エンティティ抽出"""
        entities = {}

        for pattern_name, pattern in self.content_patterns.items():
            if pattern_name in ["url", "email", "date", "time", "number"]:
                matches = pattern.findall(text)
                if matches:
                    entities[pattern_name] = matches

        return entities

    # === コンテンツ構造化メソッド ===

    def _structure_content(
        self, text: str, classification: Dict[str, Any], structure: Dict[str, Any]
    ) -> List["Node"]:
        """コンテンツの構造化"""
        from ..core.ast_nodes.node import Node

        nodes = []

        # 段落ベースの分割
        paragraphs = self.content_patterns["paragraph_break"].split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        for i, paragraph in enumerate(paragraphs):
            para_node = Node(
                type="paragraph",
                content=paragraph,
                attributes={
                    "index": i,
                    "length": len(paragraph),
                    "word_count": len(paragraph.split()),
                },
            )

            # 段落内エンティティの抽出
            para_entities = self._extract_entities(paragraph)
            if (
                para_entities
                and hasattr(para_node, "attributes")
                and para_node.attributes is not None
            ):
                para_node.attributes["entities"] = para_entities

            nodes.append(para_node)

        return nodes

    def _process_inline_content(self, content: str) -> bool:
        """インラインコンテンツ処理"""
        lines = content.split("\n")
        processed = False

        for line in lines:
            if self.is_new_marker_format(line):
                processed = True
                break

        return processed

    # === 脚注処理メソッド ===

    def extract_footnotes_from_text(self, text: str) -> List[Dict[str, Any]]:
        """テキストから脚注抽出"""
        if not isinstance(text, str):
            return []

        footnotes = []
        footnote_pattern = self.content_patterns["footnote"]

        for match in footnote_pattern.finditer(text):
            footnote_id = match.group(1)
            position = match.start()

            footnote = {
                "id": footnote_id,
                "position": position,
                "content": self._sanitize_footnote_content(footnote_id),
            }
            footnotes.append(footnote)

        return footnotes

    def parse_footnotes(self, text: Any) -> List[Dict[str, Any]]:
        """脚注解析"""
        if not isinstance(text, str):
            return []

        footnotes: List[Dict[str, Any]] = []
        footnote_pattern = self.content_patterns["footnote"]
        matches = footnote_pattern.findall(text)
        for match in matches:
            footnotes.append({"id": match, "content": ""})
        return footnotes

    def _sanitize_footnote_content(self, content: Any) -> str:
        """脚注コンテンツのサニタイズ"""
        if not isinstance(content, str):
            return ""

        # 基本サニタイゼーション
        sanitized = content.strip()
        # HTMLエスケープ
        import html

        sanitized = html.escape(sanitized, quote=True)
        return sanitized

    # === インラインコンテンツ処理メソッド ===

    def extract_inline_content(self, line: Any) -> Optional[str]:
        """インラインコンテンツ抽出"""
        if not isinstance(line, str):
            return None

        # インラインコンテンツパターンでマッチング
        match = self.content_patterns["inline_content"].match(line)
        if match:
            return match.group(2).strip()

        return None

    def is_new_marker_format(self, line: Any) -> bool:
        """新マーカー形式判定"""
        if not isinstance(line, str):
            return False

        # インラインパターンの定義
        inline_pattern_1 = re.compile(r"^#\s*[^#]+?\s*#[^#]*?##$")
        inline_pattern_2 = re.compile(r"^##\s*[^#]+?\s*##$")
        inline_pattern_3 = re.compile(r"^###\s*[^#]+?\s*###$")

        # いずれかのパターンにマッチするかチェック
        if (
            inline_pattern_1.match(line)
            or inline_pattern_2.match(line)
            or inline_pattern_3.match(line)
        ):
            return True

        return False

    def is_block_end_marker(self, line: Any) -> bool:
        """ブロック終了マーカー判定"""
        if not isinstance(line, str):
            return False

        line = line.strip()
        # ブロック終了マーカーのチェック: ## または ＃＃
        if line == "##" or line == "＃＃":
            return True

        return False

    def normalize_marker_syntax(self, marker_content: Any) -> str:
        """マーカー記法の正規化"""
        if not isinstance(marker_content, str):
            return ""

        return marker_content.strip()

    # === バリデーション補助メソッド ===

    def _validate_footnote_structure(self, footnotes: Any) -> List[str]:
        """脚注構造の検証"""
        errors: List[str] = []

        if not isinstance(footnotes, list):
            errors.append("Footnotes must be a list")
            return errors

        seen_ids = set()
        for i, footnote in enumerate(footnotes):
            if not isinstance(footnote, dict):
                errors.append(f"Footnote {i} is not a dictionary")
                continue

            # 必須フィールドのチェック
            if "id" not in footnote:
                errors.append(f"Footnote {i} missing 'id' field")
                continue

            footnote_id = footnote["id"]

            # 重複IDのチェック
            if footnote_id in seen_ids:
                errors.append(f"Duplicate footnote ID: {footnote_id}")
            else:
                seen_ids.add(footnote_id)

            # 位置情報の検証
            if "position" in footnote:
                position = footnote["position"]
                if not isinstance(position, int) or position < 0:
                    errors.append(
                        f"Invalid position for footnote {footnote_id}: {position}"
                    )

        return errors

    def _validate_new_format_structure(self, line: Any) -> bool:
        """新フォーマット構造の検証"""
        if not isinstance(line, str):
            return False

        # 基本構造検証
        if line.count("#") < 3:  # 最低 # keyword # content ## が必要
            return False

        return True

    def _validate_block_structure_in_content(self, content: str) -> List[str]:
        """コンテンツ内のブロック構造検証"""
        errors = []
        lines = content.split("\n")

        open_blocks = 0
        for i, line in enumerate(lines):
            stripped = line.strip()

            # ブロック開始マーカー
            if re.match(r"^#\s*[^#]+\s*#", stripped):
                if not stripped.endswith("##"):
                    open_blocks += 1

            # ブロック終了マーカー
            elif stripped == "##":
                if open_blocks > 0:
                    open_blocks -= 1
                else:
                    errors.append(f"Unexpected closing marker at line {i+1}")

        if open_blocks > 0:
            errors.append(f"{open_blocks} unclosed block(s) found")

        return errors

    # === 高度API メソッド（specialized統合） ===

    def parse_mixed_content(
        self, content: str, prefer_format: Optional[str] = None
    ) -> "ParseResult":
        """混在記法コンテンツの解析"""
        # 優先フォーマットが指定されている場合の特別処理
        if prefer_format:
            self.logger.info(f"優先フォーマット指定: {prefer_format}")

        return self.parse(content)

    def extract_text_summary(self, parse_result: "ParseResult") -> Dict[str, Any]:
        """テキストサマリーの抽出"""
        summary = {
            "total_characters": 0,
            "total_words": 0,
            "paragraphs": 0,
            "entities": {},
            "classification": parse_result.metadata.get("classification", {}),
        }

        def count_from_node(node: "Node") -> None:
            if hasattr(node, "content") and isinstance(node.content, str):
                summary["total_characters"] += len(node.content)
                summary["total_words"] += len(node.content.split())

                if node.type == "paragraph":
                    summary["paragraphs"] += 1

                # エンティティの集計
                if hasattr(node, "attributes") and node.attributes:
                    entities = node.attributes.get("entities", {})
                    for entity_type, entity_list in entities.items():
                        if entity_type not in summary["entities"]:
                            summary["entities"][entity_type] = []
                        summary["entities"][entity_type].extend(entity_list)

            # 子ノードの処理（もしあれば）
            if hasattr(node, "children"):
                for child in node.children:
                    count_from_node(child)

        for node in parse_result.nodes:
            count_from_node(node)

        return summary

    def suggest_improvements(self, parse_result: "ParseResult") -> List[str]:
        """コンテンツ改善提案"""
        suggestions = []

        classification = parse_result.metadata.get("classification", {})
        structure = parse_result.metadata.get("structure", {})

        # 構造改善の提案
        if structure.get("paragraph", {}).get("count", 0) == 1:
            suggestions.append("長い文章は段落に分けると読みやすくなります")

        if classification.get("complexity") == "high":
            suggestions.append(
                "複雑な表現をより分かりやすく簡略化できないか検討してください"
            )

        # エンティティに基づく提案
        entities = parse_result.metadata.get("entities", {})
        if "urls" in entities and len(entities["urls"]) > 5:
            suggestions.append(
                "多数のURLがあります。リスト形式にまとめることを検討してください"
            )

        if classification.get("language") == "mixed":
            suggestions.append(
                "日本語と英語が混在しています。統一性を保つことを検討してください"
            )

        return suggestions

    def get_content_statistics(self) -> Dict[str, Any]:
        """コンテンツ解析統計を取得"""
        stats = {
            "content_classifiers": list(self.content_classifiers.keys()),
            "structure_analyzers": list(self.structure_analyzers.keys()),
            "parser_type": "unified_content",
            "version": "3.0.0",
            "features": [
                "classification",
                "entity_extraction",
                "footnotes",
                "inline_content",
                "validation",
            ],
        }
        return stats


# Alias for backward compatibility
ContentParser = UnifiedContentParser
