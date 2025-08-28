"""Content Parser Utilities - コンテンツ解析ユーティリティ

分離された責任:
- パターン設定・初期化
- 分類器・解析器のセットアップ
- 共通ユーティリティ関数
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import logging


def setup_content_patterns() -> Dict[str, re.Pattern[str]]:
    """コンテンツパターンの設定"""
    return {
        "footnote": re.compile(r"\[\^\w+\]:\s*(.*)"),
        "inline_footnote": re.compile(r"\[\^(\w+)\]"),
        "entity_name": re.compile(r"[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*"),
        "entity_date": re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"),
        "entity_number": re.compile(r"\d+(?:\.\d+)?"),
        "entity_url": re.compile(r"https?://[\w\-\.\/]+"),
        "semantic_header": re.compile(r"^#+\s+(.+)$", re.MULTILINE),
        "semantic_list": re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE),
        "semantic_emphasis": re.compile(r"(\*\*|__)(.*?)\1"),
        "new_marker": re.compile(r"^# \w+ #.*##$"),
        "block_end": re.compile(r"^##$"),
        "marker_content": re.compile(r"#(.*)#(.*?)##", re.DOTALL),
    }


def setup_content_classifiers() -> Dict[str, Any]:
    """コンテンツ分類器の設定"""
    return {
        "text_type": ["paragraph", "heading", "list", "code", "quote", "table"],
        "language": ["japanese", "english", "mixed", "unknown"],
        "structure": ["simple", "complex", "hierarchical", "mixed"],
        "complexity": ["low", "medium", "high", "very_high"],
    }


def setup_structure_analyzers() -> Dict[str, Any]:
    """構造解析器の設定"""
    return {
        "paragraph": {"min_sentences": 1, "max_sentences": 20},
        "sentence": {"min_words": 3, "max_words": 50},
        "entity": {"types": ["name", "date", "number", "url"]},
    }


def classify_text_type(content: str) -> str:
    """テキストタイプの分類"""
    content = content.strip()

    if content.startswith("#"):
        return "heading"
    elif content.startswith(("-", "*", "+")):
        return "list"
    elif content.startswith("```"):
        return "code"
    elif content.startswith(">"):
        return "quote"
    elif "|" in content and content.count("|") >= 2:
        return "table"
    else:
        return "paragraph"


def classify_language(content: str) -> str:
    """言語の分類"""
    japanese_pattern = re.compile(r"[ひらがなカタカナ漢字]")
    english_pattern = re.compile(r"[a-zA-Z]")

    japanese_count = len(japanese_pattern.findall(content))
    english_count = len(english_pattern.findall(content))
    total_chars = len(re.sub(r"\s", "", content))

    if total_chars == 0:
        return "unknown"

    japanese_ratio = japanese_count / total_chars
    english_ratio = english_count / total_chars

    if japanese_ratio > 0.7:
        return "japanese"
    elif english_ratio > 0.7:
        return "english"
    elif japanese_ratio > 0.1 and english_ratio > 0.1:
        return "mixed"
    else:
        return "unknown"


def classify_structure(content: str) -> str:
    """構造の分類"""
    lines = content.split("\n")

    if len(lines) <= 3:
        return "simple"
    elif any(line.startswith("#") for line in lines):
        return "hierarchical"
    elif len(lines) > 10:
        return "complex"
    else:
        return "mixed"


def classify_complexity(content: str) -> str:
    """複雑度の分類"""
    lines = content.split("\n")
    words = content.split()

    complexity_score = 0.0
    complexity_score += len(lines) * 0.1
    complexity_score += len(words) * 0.01
    complexity_score += content.count("#") * 0.5
    complexity_score += content.count("```") * 1.0
    complexity_score += content.count("|") * 0.3

    if complexity_score < 5:
        return "low"
    elif complexity_score < 15:
        return "medium"
    elif complexity_score < 30:
        return "high"
    else:
        return "very_high"


def analyze_paragraphs(content: str) -> Dict[str, Any]:
    """段落解析"""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    return {
        "count": len(paragraphs),
        "avg_length": (
            sum(len(p) for p in paragraphs) // len(paragraphs) if paragraphs else 0
        ),
        "paragraphs": paragraphs,
    }


def analyze_sentences(content: str) -> Dict[str, Any]:
    """文章解析"""
    sentences = re.split(r"[.!?。！？]", content)
    sentences = [s.strip() for s in sentences if s.strip()]
    return {
        "count": len(sentences),
        "avg_length": (
            sum(len(s) for s in sentences) // len(sentences) if sentences else 0
        ),
        "sentences": sentences,
    }


def extract_entities(
    content: str, patterns: Dict[str, re.Pattern[str]]
) -> Dict[str, List[str]]:
    """エンティティ抽出"""
    entities = {}

    entities["names"] = patterns["entity_name"].findall(content)
    entities["dates"] = patterns["entity_date"].findall(content)
    entities["numbers"] = patterns["entity_number"].findall(content)
    entities["urls"] = patterns["entity_url"].findall(content)

    return entities


def sanitize_footnote_content(content: str) -> str:
    """脚注コンテンツのサニタイズ"""
    # 改行とタブを正規化
    content = re.sub(r"\n\s*", " ", content)
    content = re.sub(r"\t+", " ", content)

    # 余分な空白を削除
    content = re.sub(r"\s+", " ", content)

    return content.strip()


def validate_footnote_structure(content: str) -> List[str]:
    """脚注構造の検証"""
    errors = []

    # 脚注参照のパターン
    footnote_refs = re.findall(r"\[\^(\w+)\]", content)
    footnote_defs = re.findall(r"\[\^(\w+)\]:\s*(.+)", content)

    # 定義されている脚注ID
    defined_ids = {match[0] for match in footnote_defs}
    referenced_ids = set(footnote_refs)

    # 参照されているが定義されていない脚注
    undefined_refs = referenced_ids - defined_ids
    if undefined_refs:
        errors.append(f"未定義の脚注参照: {', '.join(undefined_refs)}")

    # 定義されているが参照されていない脚注
    unused_defs = defined_ids - referenced_ids
    if unused_defs:
        errors.append(f"未使用の脚注定義: {', '.join(unused_defs)}")

    # 空の脚注定義をチェック
    for ref_id, definition in footnote_defs:
        if not definition.strip():
            errors.append(f"空の脚注定義: [{ref_id}]")

    return errors


def validate_new_format_structure(content: str) -> List[str]:
    """新フォーマット構造の検証"""
    errors = []

    new_format_pattern = re.compile(r"^# \w+ #.*##$")
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        if new_format_pattern.match(line):
            if not line.endswith("##"):
                errors.append(f"行 {i}: 新フォーマットの終了マーカーが不正です")

    return errors


def validate_block_structure_in_content(content: str) -> List[str]:
    """コンテンツ内のブロック構造検証"""
    errors = []
    lines = content.split("\n")

    open_blocks = []

    for i, line in enumerate(lines, 1):
        line = line.strip()

        # ブロック開始の検出
        if line.startswith("#") and line.endswith("#"):
            if not line.endswith("##"):
                open_blocks.append((i, line))

        # ブロック終了の検出
        elif line == "##":
            if not open_blocks:
                errors.append(f"行 {i}: 対応するブロック開始がない終了マーカーです")
            else:
                open_blocks.pop()

    # 未閉じのブロックをチェック
    for line_num, block_start in open_blocks:
        errors.append(f"行 {line_num}: ブロックが閉じられていません: {block_start}")

    return errors


def extract_footnotes_from_text(content: str) -> Tuple[str, List[Dict[str, str]]]:
    """テキストから脚注を抽出"""
    footnotes = []
    footnote_pattern = re.compile(r"\[\^(\w+)\]:\s*(.*)")

    # 脚注定義を抽出
    for match in footnote_pattern.finditer(content):
        footnote_id = match.group(1)
        footnote_content = match.group(2).strip()
        footnotes.append({"id": footnote_id, "content": footnote_content})

    # 脚注定義を削除したテキストを返す
    cleaned_content = footnote_pattern.sub("", content)

    return cleaned_content, footnotes


def parse_footnotes(footnotes_data: List[Dict[str, str]]) -> Dict[str, str]:
    """脚注データの解析"""
    parsed_footnotes = {}

    for footnote in footnotes_data:
        footnote_id = footnote["id"]
        content = footnote["content"]

        # コンテンツをサニタイズ
        sanitized_content = sanitize_footnote_content(content)
        parsed_footnotes[footnote_id] = sanitized_content

    return parsed_footnotes


def extract_inline_content(content: str) -> List[Dict[str, Any]]:
    """インラインコンテンツの抽出"""
    inline_elements = []

    # インライン脚注参照
    footnote_refs = re.finditer(r"\[\^(\w+)\]", content)
    for match in footnote_refs:
        inline_elements.append(
            {
                "type": "footnote_ref",
                "id": match.group(1),
                "position": match.span(),
            }
        )

    return inline_elements


def is_new_marker_format(line: str) -> bool:
    """新マーカーフォーマットの判定"""
    return bool(re.match(r"^# \w+ #.*##$", line.strip()))


def is_block_end_marker(line: str) -> bool:
    """ブロック終了マーカーの判定"""
    return line.strip() == "##"


def normalize_marker_syntax(content: str) -> str:
    """マーカー構文の正規化"""
    # 新フォーマットを正規化
    content = re.sub(
        r"^#\s*(\w+)\s*#\s*(.*?)\s*##$", r"# \1 #\2##", content, flags=re.MULTILINE
    )

    return content
