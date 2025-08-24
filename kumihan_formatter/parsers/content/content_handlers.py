"""Content Parser Handlers - コンテンツ処理ハンドラ

分離された責任:
- コンテンツ分類・解析処理
- 構造分析・セマンティック処理
- 高度な解析機能
"""

from typing import Any, Dict, List, Optional
import re
from ...core.utilities.logger import get_logger
from .content_utils import (
    classify_text_type,
    classify_language,
    classify_structure,
    classify_complexity,
    analyze_paragraphs,
    analyze_sentences,
    extract_entities,
    validate_footnote_structure,
    validate_new_format_structure,
    validate_block_structure_in_content,
)


class ContentHandler:
    """コンテンツ処理ハンドラクラス"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def classify_content(self, content: str) -> Dict[str, str]:
        """コンテンツの総合分類"""
        return {
            "text_type": classify_text_type(content),
            "language": classify_language(content),
            "structure": classify_structure(content),
            "complexity": classify_complexity(content),
        }

    def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """コンテンツ構造の解析"""
        return {
            "paragraphs": analyze_paragraphs(content),
            "sentences": analyze_sentences(content),
            "word_count": len(content.split()),
            "char_count": len(content),
            "line_count": len(content.split("\n")),
        }

    def analyze_entities(
        self, content: str, patterns: Dict[str, re.Pattern[str]]
    ) -> Dict[str, Any]:
        """エンティティの解析"""
        entities = extract_entities(content, patterns)

        return {
            "entities": entities,
            "entity_count": sum(len(ent_list) for ent_list in entities.values()),
            "entity_density": (
                sum(len(ent_list) for ent_list in entities.values())
                / len(content.split())
                if content.split()
                else 0
            ),
        }

    def analyze_semantic_structure(
        self, content: str, patterns: Dict[str, re.Pattern[str]]
    ) -> Dict[str, Any]:
        """セマンティック構造の解析"""
        semantic_data = {}

        # ヘッダーの解析
        headers = patterns["semantic_header"].findall(content)
        semantic_data["headers"] = headers
        semantic_data["header_count"] = len(headers)

        # リストの解析
        lists = patterns["semantic_list"].findall(content)
        semantic_data["lists"] = lists
        semantic_data["list_count"] = len(lists)

        # 強調の解析
        emphasis = patterns["semantic_emphasis"].findall(content)
        semantic_data["emphasis"] = [match[1] for match in emphasis]
        semantic_data["emphasis_count"] = len(emphasis)

        return semantic_data

    def structure_content(self, content: str) -> Dict[str, Any]:
        """コンテンツの構造化"""
        lines = content.split("\n")
        structured_content = {
            "sections": [],
            "current_section": None,
            "metadata": {"total_lines": len(lines)},
        }

        current_section = {"type": "content", "lines": [], "level": 0}

        for line in lines:
            line = line.strip()

            if line.startswith("#"):
                # 新しいセクションの開始
                if current_section["lines"]:
                    structured_content["sections"].append(current_section)

                level = len(line) - len(line.lstrip("#"))
                current_section = {
                    "type": "heading",
                    "lines": [line],
                    "level": level,
                    "title": line.lstrip("#").strip(),
                }
            else:
                current_section["lines"].append(line)

        if current_section["lines"]:
            structured_content["sections"].append(current_section)

        return structured_content

    def process_inline_content(self, content: str) -> Dict[str, Any]:
        """インラインコンテンツの処理"""
        inline_data = {
            "footnote_refs": [],
            "emphasis": [],
            "links": [],
            "processed_content": content,
        }

        # 脚注参照の処理
        footnote_pattern = re.compile(r"\[\^(\w+)\]")
        refs = footnote_pattern.findall(content)
        inline_data["footnote_refs"] = refs

        # 強調の処理
        emphasis_pattern = re.compile(r"(\*\*|__)(.*?)\1")
        emphasis_matches = emphasis_pattern.findall(content)
        inline_data["emphasis"] = [match[1] for match in emphasis_matches]

        # リンクの処理
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        links = link_pattern.findall(content)
        inline_data["links"] = [{"text": text, "url": url} for text, url in links]

        return inline_data

    def validate_content_structure(self, content: str) -> List[str]:
        """コンテンツ構造の検証"""
        errors = []

        # 脚注構造の検証
        footnote_errors = validate_footnote_structure(content)
        errors.extend(footnote_errors)

        # 新フォーマット構造の検証
        new_format_errors = validate_new_format_structure(content)
        errors.extend(new_format_errors)

        # ブロック構造の検証
        block_errors = validate_block_structure_in_content(content)
        errors.extend(block_errors)

        return errors


class ContentAnalyzer:
    """高度なコンテンツ解析クラス"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def parse_mixed_content(self, content: str) -> Dict[str, Any]:
        """混合コンテンツの解析"""
        # 異なる形式が混在するコンテンツを解析
        mixed_analysis = {
            "kumihan_blocks": [],
            "markdown_elements": [],
            "plain_text": [],
            "statistics": {},
        }

        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("# ") and line.endswith("##"):
                mixed_analysis["kumihan_blocks"].append(line)
            elif line.startswith("#") or line.startswith("*") or line.startswith("-"):
                mixed_analysis["markdown_elements"].append(line)
            else:
                mixed_analysis["plain_text"].append(line)

        # 統計情報の計算
        mixed_analysis["statistics"] = {
            "kumihan_ratio": (
                len(mixed_analysis["kumihan_blocks"]) / len(lines) if lines else 0
            ),
            "markdown_ratio": (
                len(mixed_analysis["markdown_elements"]) / len(lines) if lines else 0
            ),
            "plain_ratio": (
                len(mixed_analysis["plain_text"]) / len(lines) if lines else 0
            ),
        }

        return mixed_analysis

    def extract_text_summary(self, parse_result: Any) -> Dict[str, Any]:
        """テキストサマリーの抽出"""
        if not hasattr(parse_result, "nodes") or not parse_result.nodes:
            return {
                "summary": "解析結果が空です",
                "key_points": [],
                "word_count": 0,
                "reading_time": 0,
            }

        # ノードからテキストを抽出
        text_content = []
        for node in parse_result.nodes:
            if hasattr(node, "content") and node.content:
                text_content.append(str(node.content))

        full_text = " ".join(text_content)
        words = full_text.split()

        # キーポイントの抽出（最初の文または重要な文）
        sentences = re.split(r"[.!?。！？]", full_text)
        key_points = [s.strip() for s in sentences[:3] if s.strip()]

        return {
            "summary": (
                sentences[0].strip() if sentences else "サマリーを生成できませんでした"
            ),
            "key_points": key_points,
            "word_count": len(words),
            "reading_time": max(1, len(words) // 200),  # 200語/分で計算
            "content_length": len(full_text),
        }

    def suggest_improvements(self, parse_result: Any) -> List[str]:
        """改善提案の生成"""
        suggestions = []

        if not hasattr(parse_result, "nodes") or not parse_result.nodes:
            suggestions.append(
                "コンテンツが解析されていません。有効なコンテンツを提供してください。"
            )
            return suggestions

        # エラーがある場合の提案
        if hasattr(parse_result, "errors") and parse_result.errors:
            suggestions.append("構文エラーを修正してください。")

        # 警告がある場合の提案
        if hasattr(parse_result, "warnings") and parse_result.warnings:
            suggestions.append("警告を確認し、必要に応じて修正してください。")

        # ノード数に基づく提案
        node_count = len(parse_result.nodes)
        if node_count == 0:
            suggestions.append("コンテンツが空です。内容を追加してください。")
        elif node_count > 50:
            suggestions.append(
                "コンテンツが非常に長いです。セクションに分割することを検討してください。"
            )

        # テキスト解析に基づく提案
        text_content = []
        for node in parse_result.nodes:
            if hasattr(node, "content") and node.content:
                text_content.append(str(node.content))

        if text_content:
            full_text = " ".join(text_content)

            # 可読性の提案
            avg_sentence_length = len(full_text.split()) / max(
                1, full_text.count(".") + full_text.count("。")
            )
            if avg_sentence_length > 25:
                suggestions.append(
                    "文章が長すぎる可能性があります。短く分割することを検討してください。"
                )

            # 構造の提案
            if full_text.count("#") == 0 and len(full_text) > 500:
                suggestions.append(
                    "長いコンテンツには見出しを追加することをお勧めします。"
                )

        if not suggestions:
            suggestions.append("コンテンツの構造と内容は適切です。")

        return suggestions

    def get_content_statistics(self, content: str) -> Dict[str, Any]:
        """コンテンツ統計情報の取得"""
        lines = content.split("\n")
        words = content.split()

        return {
            "line_count": len(lines),
            "word_count": len(words),
            "char_count": len(content),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "avg_words_per_line": (
                len(words) / len([l for l in lines if l.strip()]) if lines else 0
            ),
        }
