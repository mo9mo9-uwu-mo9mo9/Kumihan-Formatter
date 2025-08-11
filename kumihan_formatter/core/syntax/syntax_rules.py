"""Syntax rules and keyword definitions

This module contains the definition of valid keywords, rules for keyword
combinations, and validation logic for Kumihan markup syntax.
"""

import re


class SyntaxRules:
    """Defines syntax rules and keyword validation for Kumihan markup"""

    # Valid keywords
    VALID_KEYWORDS: set[str] = {
        "太字",
        "イタリック",
        "下線",
        "取り消し線",
        "コード",
        "引用",
        "枠線",
        "ハイライト",
        "見出し1",
        "見出し2",
        "見出し3",
        "見出し4",
        "見出し5",
        "折りたたみ",
        "ネタバレ",
        "中央寄せ",
        "注意",
        "情報",
        "コードブロック",
        "テスト",
        "ルビ",
        "脚注",
        "リスト",
        "画像",
        "動画",
        "音声",
        # "目次" - Issue #799: 目次記法完全廃止、自動生成のみに変更
    }

    # Keywords that accept color attribute
    COLOR_KEYWORDS: set[str] = {"ハイライト"}

    # alt属性は削除されました（Phase 1）
    ALT_KEYWORDS: set[str] = set()

    # Heading keywords for conflict detection
    HEADING_KEYWORDS: set[str] = {"見出し1", "見出し2", "見出し3", "見出し4", "見出し5"}

    @classmethod
    def is_valid_keyword(cls, keyword: str) -> bool:
        """Check if a keyword is valid"""
        return keyword in cls.VALID_KEYWORDS

    @classmethod
    def supports_color(cls, keyword: str) -> bool:
        """Check if a keyword supports color attribute"""
        return keyword in cls.COLOR_KEYWORDS

    @classmethod
    def supports_alt(cls, keyword: str) -> bool:
        """Check if a keyword supports alt attribute - alt属性は削除されました（Phase 1）"""
        # alt属性は削除されました（Phase 1）
        return False

    @classmethod
    def is_heading(cls, keyword: str) -> bool:
        """Check if a keyword is a heading"""
        return keyword in cls.HEADING_KEYWORDS

    @classmethod
    def parse_keywords(cls, keyword_part: str) -> list[str]:
        """Parse compound keywords separated by + or ＋"""
        if not keyword_part:
            return []

        result = []
        keywords = keyword_part.replace("＋", "+").split("+")
        for kw in keywords:
            if kw.strip():
                result.append(kw)

        return result

    @classmethod
    def validate_color_format(cls, color: str) -> bool:
        """Validate color format (#RRGGBB)"""
        return bool(re.match(r"^#[0-9a-fA-F]{6}$", color))

    @classmethod
    def extract_base_keyword(cls, keyword: str) -> str:
        """Extract base keyword from keyword with attributes"""
        # Check for color attribute (with or without space)
        if "color=" in keyword:
            if " color=" in keyword:
                return keyword.split(" color=")[0].strip()

    @classmethod
    def extract_color_value(cls, keyword: str) -> str:
        """Extract color value from keyword with color attribute"""
        if " color=" in keyword:
            return keyword.split(" color=")[1].strip()

    @classmethod
    def extract_alt_value(cls, keyword: str) -> str:
        """Extract alt value from keyword with alt attribute - alt属性は削除されました（Phase 1）"""
        # alt属性は削除されました（Phase 1）
        return ""

    @classmethod
    def has_color_attribute(cls, keyword: str) -> bool:
        """Check if keyword has color attribute"""
        return "color=" in keyword

    @classmethod
    def has_alt_attribute(cls, keyword: str) -> bool:
        """Check if keyword has alt attribute - alt属性は削除されました（Phase 1）"""
        # alt属性は削除されました（Phase 1）
        return False

    @classmethod
    def find_duplicate_keywords(cls, keywords: list[str]) -> list[str]:
        """Find duplicate base keywords in list"""
        base_keywords = [cls.extract_base_keyword(kw) for kw in keywords]
        seen = set()
        duplicates = []

        for kw in base_keywords:
            if kw in seen:
                duplicates.append(kw)
            seen.add(kw)

        return duplicates

    @classmethod
    def find_conflicting_headings(cls, keywords: list[str]) -> list[str]:
        """Find conflicting heading keywords"""
        base_keywords = [cls.extract_base_keyword(kw) for kw in keywords]
        headings = [kw for kw in base_keywords if cls.is_heading(kw)]

        if len(headings) > 1:
            return headings

    @classmethod
    def get_sorted_keywords(cls) -> list[str]:
        """Get sorted list of valid keywords for error messages"""
        return sorted(cls.VALID_KEYWORDS)

    @staticmethod
    def get_all_rules() -> dict[str, set[str]]:
        """すべての構文ルールを辞書形式で返す（テスト互換性のため）

        Returns:
            dict: ルールカテゴリ別のキーワードセット
        """
        return {
            "valid_keywords": SyntaxRules.VALID_KEYWORDS,
            "color_keywords": SyntaxRules.COLOR_KEYWORDS,
            "alt_keywords": SyntaxRules.ALT_KEYWORDS,
            "heading_keywords": SyntaxRules.HEADING_KEYWORDS,
        }

    @staticmethod
    def check_text(text: str) -> list[str]:
        """テキストに対してルールチェックを実行（新記法のみ対応）

        Args:
            text: チェック対象のテキスト

        Returns:
            list[str]: 検出された違反事項のリスト
        """
        violations = []

        # 簡易的なキーワード抽出とチェック（新記法のみ）
        import re

        # 新記法のみ対応
        pattern = r"[#＃]([^#＃]+?)[#＃]"  # 新記法

        found_keywords = []
        matches = re.findall(pattern, text)
        for match in matches:
            keyword = match.strip().split()[0]  # 最初の単語を取得
            found_keywords.append(keyword)

        # キーワードの妥当性チェック
        for keyword in found_keywords:
            if not SyntaxRules.is_valid_keyword(keyword):
                violations.append(f"無効なキーワード: {keyword}")

        # 重複チェック
        duplicates = SyntaxRules.find_duplicate_keywords(found_keywords)
        for duplicate in duplicates:
            violations.append(f"重複するキーワード: {duplicate}")

        # 見出し競合チェック
        headings = [kw for kw in found_keywords if SyntaxRules.is_heading(kw)]
        if len(headings) > 1:
            violations.append(f"競合する見出しレベル: {', '.join(headings)}")

        return violations

    @staticmethod
    def check_marker_mixing(text: str) -> list[str]:
        """マーカー混在禁止ルールをチェック（Phase 1）

        Args:
            text: チェック対象のテキスト

        Returns:
            list[str]: 検出された違反事項のリスト
        """
        violations = []
        import re

        # 半角・全角マーカー混在チェック
        has_half_width = bool(re.search(r"[#]", text))
        has_full_width = bool(re.search(r"[＃]", text))

        if has_half_width and has_full_width:
            violations.append(
                "半角マーカー（#）と全角マーカー（＃）の混在は禁止されています"
            )

        return violations

    @staticmethod
    def check_color_case_mixing(text: str) -> list[str]:
        """color属性の大文字小文字混在禁止ルールをチェック（Phase 1）

        Args:
            text: チェック対象のテキスト

        Returns:
            list[str]: 検出された違反事項のリスト
        """
        violations = []
        import re

        # color属性のパターンを抽出（16進数カラーコードを除外）
        color_patterns = re.findall(r"color=([a-zA-Z][a-zA-Z]*)", text)

        if color_patterns:
            # 大文字小文字が混在していないかチェック
            lowercase_colors = [c for c in color_patterns if c.islower()]
            uppercase_colors = [c for c in color_patterns if c.isupper()]
            mixed_case_colors = [
                c for c in color_patterns if not c.islower() and not c.isupper()
            ]

            # 複数のカテゴリに色名が存在する場合のみ違反
            categories_with_colors = 0
            if lowercase_colors:
                categories_with_colors += 1
            if uppercase_colors:
                categories_with_colors += 1
            if mixed_case_colors:
                categories_with_colors += 1

            if categories_with_colors > 1:
                violations.append(
                    "color属性で大文字・小文字・混在表記の混用は禁止されています"
                )

        return violations

    @staticmethod
    def get_rule_categories() -> dict[str, str]:
        """ルールカテゴリの説明を取得（テスト互換性のため）

        Returns:
            dict: カテゴリ名と説明の辞書
        """
        return {
            "keyword_validation": "有効なキーワードの検証",
            "color_validation": "色指定属性の検証",
            "alt_validation": "代替テキスト属性の検証",
            "heading_validation": "見出しレベルの検証",
            "duplicate_detection": "重複キーワードの検出",
            "conflict_resolution": "競合する記法の解決",
        }
