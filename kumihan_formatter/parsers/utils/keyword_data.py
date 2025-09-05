"""Default keyword/extraction/validation data for ParserUtils.

Keeping default dictionaries in a dedicated module reduces the footprint of
parser_utils.py and avoids accidental mutation across imports.
"""

from __future__ import annotations

from typing import Dict, Set, Any


DEFAULT_KEYWORD_CONFIG: Dict[str, Set[str]] = {
    "basic_keywords": {
        "太字",
        "イタリック",
        "見出し1",
        "見出し2",
        "見出し3",
        "リスト",
        "番号リスト",
        "引用",
        "コード",
        "リンク",
    },
    "advanced_keywords": {
        "テーブル",
        "画像",
        "注釈",
        "脚注",
        "数式",
        "図表",
        "キャプション",
        "参照",
        "索引",
    },
    "formatting_keywords": {
        "中央",
        "右寄せ",
        "左寄せ",
        "両端揃え",
        "色",
        "背景色",
        "フォント",
        "サイズ",
    },
    "structural_keywords": {
        "章",
        "節",
        "項",
        "段落",
        "改ページ",
        "セクション",
        "ブロック",
        "コンテナ",
    },
}


DEFAULT_VALIDATION_RULES: Dict[str, Any] = {
    "min_keyword_length": 1,
    "max_keyword_length": 20,
    "allow_numbers": True,
    "allow_special_chars": False,
    "reserved_keywords": {"エラー", "無効", "不明"},
}


DEFAULT_EXTRACTION_CONFIG: Dict[str, Any] = {
    "max_extraction_depth": 10,
    "enable_nested_extraction": True,
    "preserve_whitespace": False,
    "case_sensitive": True,
}


__all__ = [
    "DEFAULT_KEYWORD_CONFIG",
    "DEFAULT_VALIDATION_RULES",
    "DEFAULT_EXTRACTION_CONFIG",
]
