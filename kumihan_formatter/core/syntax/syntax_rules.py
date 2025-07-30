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
        "枠線",
        "ハイライト",
        "見出し1",
        "見出し2",
        "見出し3",
        "見出し4",
        "見出し5",
        "折りたたみ",
        "ネタバレ",
        "目次",
        "画像",
    }

    # Keywords that accept color attribute
    COLOR_KEYWORDS: set[str] = {"ハイライト"}

    # Keywords that accept alt attribute
    ALT_KEYWORDS: set[str] = {"画像"}

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
        """Check if a keyword supports alt attribute"""
        return keyword in cls.ALT_KEYWORDS

    @classmethod
    def is_heading(cls, keyword: str) -> bool:
        """Check if a keyword is a heading"""
        return keyword in cls.HEADING_KEYWORDS

    @classmethod
    def parse_keywords(cls, keyword_part: str) -> list[str]:
        """Parse compound keywords separated by + or ＋"""
        if not keyword_part:
            return []

        # Split by + or ＋
        keywords = re.split(r"[+＋]", keyword_part)

        # Clean and validate
        result = []
        for kw in keywords:
            kw = kw.strip()
            if kw:
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
            else:
                return keyword.split("color=")[0].strip()
        # Check for alt attribute (with or without space)
        elif "alt=" in keyword:
            if " alt=" in keyword:
                return keyword.split(" alt=")[0].strip()
            else:
                return keyword.split("alt=")[0].strip()
        else:
            return keyword

    @classmethod
    def extract_color_value(cls, keyword: str) -> str:
        """Extract color value from keyword with color attribute"""
        if " color=" in keyword:
            return keyword.split(" color=")[1].strip()
        elif "color=" in keyword:
            return keyword.split("color=")[1].strip()
        return ""

    @classmethod
    def extract_alt_value(cls, keyword: str) -> str:
        """Extract alt value from keyword with alt attribute"""
        if " alt=" in keyword:
            return keyword.split(" alt=")[1].strip()
        elif "alt=" in keyword:
            return keyword.split("alt=")[1].strip()
        return ""

    @classmethod
    def has_color_attribute(cls, keyword: str) -> bool:
        """Check if keyword has color attribute"""
        return "color=" in keyword

    @classmethod
    def has_alt_attribute(cls, keyword: str) -> bool:
        """Check if keyword has alt attribute"""
        return "alt=" in keyword

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
        return []

    @classmethod
    def get_sorted_keywords(cls) -> list[str]:
        """Get sorted list of valid keywords for error messages"""
        return sorted(cls.VALID_KEYWORDS)

    @staticmethod
    def get_all_rules() -> dict[str, list[str]]:
        """すべての構文ルールを辞書形式で返す（テスト互換性のため）
        
        Returns:
            dict: ルールカテゴリ別のキーワードリスト
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
        pattern = r'[#＃]([^#＃]+?)[#＃]'  # 新記法
        
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
            "conflict_resolution": "競合する記法の解決"
        }
