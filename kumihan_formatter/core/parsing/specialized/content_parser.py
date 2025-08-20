"""統一コンテンツパーサー

Issue #880 Phase 2B: 既存のContentParser系統を統合
- core/block_parser/content_parser.py
- core/keyword_parsing/parsers/content_parser.py
の機能を統合・整理
"""

import re
from typing import Any, Dict, List, Optional, Union

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..protocols import ParserType


class UnifiedContentParser(UnifiedParserBase, CompositeMixin):
    """統一コンテンツパーサー

    汎用的なコンテンツ解析:
    - プレーンテキスト処理
    - 混在記法の統合解析
    - フォールバック処理
    - コンテンツ分類・構造化
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.CONTENT)

        # コンテンツ解析の設定
        self._setup_content_patterns()
        self._setup_content_classifiers()
        self._setup_structure_analyzers()

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

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """コンテンツの解析可能性を判定（常にTrue - フォールバック）"""
        return super().can_parse(content)

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """コンテンツ解析の実装"""
        self._start_timer("content_parsing")

        try:
            text = content if isinstance(content, str) else "\n".join(content)

            # 解析結果を格納するノード
            root_node = create_node("content_document", content=text)

            # コンテンツ分類
            classification = self._classify_content(text)
            root_node.metadata["classification"] = classification

            # 構造解析
            structure = self._analyze_content_structure(text)
            root_node.metadata["structure"] = structure

            # コンテンツ分割・構造化
            structured_content = self._structure_content(
                text, classification, structure
            )
            root_node.children = structured_content

            # エンティティ抽出
            entities = self._extract_entities(text)
            root_node.metadata["entities"] = entities

            self._end_timer("content_parsing")
            return root_node

        except Exception as e:
            self.add_error(f"コンテンツ解析エラー: {str(e)}")
            return create_node("error", content=f"Content parse error: {e}")

    def _classify_content(self, text: str) -> Dict[str, Any]:
        """コンテンツの分類"""
        classification = {}

        for classifier_name, classifier_func in self.content_classifiers.items():
            try:
                result = classifier_func(text)
                classification[classifier_name] = result
            except Exception as e:
                self.add_warning(f"分類エラー ({classifier_name}): {e}")
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
        # 語彙の多様性、文の長さ、構造の複雑さなどを考慮
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

    def _analyze_content_structure(self, text: str) -> Dict[str, Any]:
        """コンテンツ構造の解析"""
        structure = {}

        for analyzer_name, analyzer_func in self.structure_analyzers.items():
            try:
                result = analyzer_func(text)
                structure[analyzer_name] = result
            except Exception as e:
                self.add_warning(f"構造解析エラー ({analyzer_name}): {e}")
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
        # 簡単な意味構造解析
        structure = {
            "has_questions": bool(re.search(r"[？?]", text)),
            "has_exclamations": bool(re.search(r"[！!]", text)),
            "has_quotes": bool(re.search(r'[「」""\'\'"]', text)),
            "has_emphasis": bool(re.search(r"[*_**__]", text)),
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
            structure["keywords"] = high_freq_words[:10]  # 上位10語

        return structure

    def _structure_content(
        self, text: str, classification: Dict[str, Any], structure: Dict[str, Any]
    ) -> List[Node]:
        """コンテンツの構造化"""
        nodes = []

        # 段落ベースの分割
        paragraphs = self.content_patterns["paragraph_break"].split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        for i, paragraph in enumerate(paragraphs):
            para_node = create_node("paragraph", content=paragraph)
            para_node.metadata.update(
                {
                    "index": i,
                    "length": len(paragraph),
                    "word_count": len(paragraph.split()),
                }
            )

            # 段落内エンティティの抽出
            para_entities = self._extract_entities(paragraph)
            if para_entities:
                para_node.metadata["entities"] = para_entities

            nodes.append(para_node)

        return nodes

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """エンティティ抽出"""
        entities = {}

        for pattern_name, pattern in self.content_patterns.items():
            if pattern_name in ["url", "email", "date", "time", "number"]:
                matches = pattern.findall(text)
                if matches:
                    entities[pattern_name] = matches

        return entities

    # 外部API メソッド

    def parse_mixed_content(
        self, content: str, prefer_format: Optional[str] = None
    ) -> Node:
        """混在記法コンテンツの解析"""
        # 優先フォーマットが指定されている場合の特別処理
        if prefer_format:
            self.add_warning(f"優先フォーマット指定: {prefer_format}")

        return self.parse(content)

    def extract_text_summary(self, node: Node) -> Dict[str, Any]:
        """テキストサマリーの抽出"""
        summary = {
            "total_characters": 0,
            "total_words": 0,
            "paragraphs": 0,
            "entities": {},
            "classification": node.metadata.get("classification", {}),
        }

        def count_from_node(n: Node) -> None:
            if hasattr(n, "content") and isinstance(n.content, str):
                summary["total_characters"] += len(n.content)
                summary["total_words"] += len(n.content.split())

                if n.node_type == "paragraph":
                    summary["paragraphs"] += 1

                # エンティティの集計
                entities = n.metadata.get("entities", {})
                for entity_type, entity_list in entities.items():
                    if entity_type not in summary["entities"]:
                        summary["entities"][entity_type] = []
                    summary["entities"][entity_type].extend(entity_list)

            for child in getattr(n, "children", []):
                count_from_node(child)

        count_from_node(node)
        return summary

    def suggest_improvements(self, node: Node) -> List[str]:
        """コンテンツ改善提案"""
        suggestions = []

        classification = node.metadata.get("classification", {})
        structure = node.metadata.get("structure", {})

        # 構造改善の提案
        if structure.get("paragraph", {}).get("count", 0) == 1:
            suggestions.append("長い文章は段落に分けると読みやすくなります")

        if classification.get("complexity") == "high":
            suggestions.append(
                "複雑な表現をより分かりやすく簡略化できないか検討してください"
            )

        # エンティティに基づく提案
        entities = node.metadata.get("entities", {})
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
        stats = self._get_performance_stats()
        stats.update(
            {
                "content_classifiers": list(self.content_classifiers.keys()),
                "structure_analyzers": list(self.structure_analyzers.keys()),
                "parser_type": self.parser_type,
            }
        )
        return stats
