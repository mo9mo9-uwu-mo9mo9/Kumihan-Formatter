"""
キーワード検証とサジェスト - Issue #476対応

キーワードの有効性チェック、エラーメッセージ、サジェスト機能。
"""

import re
from difflib import get_close_matches

from .definitions import KeywordDefinitions


class KeywordValidator:
    """キーワード検証クラス"""

    def __init__(self, definitions: KeywordDefinitions) -> None:
        """キーワードバリデーターを初期化

        Args:
            definitions: キーワード定義
        """
        self.definitions = definitions

    def validate_keywords(self, keywords: list[str]) -> tuple[list[str], list[str]]:
        """
        キーワードを検証し、有効なものとエラーを返す

        Args:
            keywords: 検証するキーワードのリスト

        Returns:
            tuple: (有効キーワード, エラーメッセージ)
        """
        valid_keywords = []
        error_messages = []

        for keyword in keywords:
            if self.definitions.is_valid_keyword(keyword):
                valid_keywords.append(keyword)
            else:
                error_msg = f"不明なキーワード: {keyword}"
                suggestions = self.get_keyword_suggestions(keyword)
                if suggestions:
                    error_msg += f" (候補: {', '.join(suggestions)})"
                error_messages.append(error_msg)

        return valid_keywords, error_messages

    def get_keyword_suggestions(
        self, invalid_keyword: str, max_suggestions: int = 3
    ) -> list[str]:
        """
        無効なキーワードに対する修正候補を取得

        Args:
            invalid_keyword: 無効なキーワード
            max_suggestions: 最大候補数

        Returns:
            list[str]: 修正候補のリスト
        """
        all_keywords = self.definitions.get_all_keywords()
        suggestions = get_close_matches(
            invalid_keyword, all_keywords, n=max_suggestions, cutoff=0.6
        )
        return suggestions

    def validate_single_keyword(self, keyword: str) -> tuple[bool, str | None]:
        """単一キーワードの検証

        Args:
            keyword: 検証するキーワード

        Returns:
            tuple: (有効性, エラーメッセージ)
        """
        if self.definitions.is_valid_keyword(keyword):
            return True, None

        error_msg = f"不明なキーワード: {keyword}"
        suggestions = self.get_keyword_suggestions(keyword)
        if suggestions:
            error_msg += f" (候補: {', '.join(suggestions)})"

        return False, error_msg

    def is_keyword_valid(self, keyword: str) -> bool:
        """キーワードが有効かチェック

        Args:
            keyword: チェックするキーワード

        Returns:
            有効な場合True
        """
        return self.definitions.is_valid_keyword(keyword)

    def get_all_valid_keywords(self) -> list[str]:
        """すべての有効キーワードを取得

        Returns:
            有効キーワードのリスト
        """
        return self.definitions.get_all_keywords()

    def check_keyword_conflicts(self, keywords: list[str]) -> list[str]:
        """キーワード間の競合をチェック

        Args:
            keywords: チェックするキーワードリスト

        Returns:
            競合警告メッセージのリスト
        """
        warnings = []

        # 同じタグのキーワードが複数あるかチェック
        tag_counts: dict[str, list[str]] = {}
        for keyword in keywords:
            if self.definitions.is_valid_keyword(keyword):
                tag = self.definitions.get_tag_for_keyword(keyword)
                if tag:
                    if tag in tag_counts:
                        tag_counts[tag].append(keyword)
                    else:
                        tag_counts[tag] = [keyword]

        # 複数の同じタグがある場合は警告
        for tag, tag_keywords in tag_counts.items():
            if len(tag_keywords) > 1:
                warnings.append(
                    f"同じタグ({tag})のキーワードが複数あります: {', '.join(tag_keywords)}"
                )

        return warnings

    def validate_keyword_combination(
        self, keywords: list[str]
    ) -> tuple[bool, list[str]]:
        """
        キーワード組み合わせの妥当性を包括的に検証

        Args:
            keywords: 検証するキーワードのリスト

        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []

        # 基本的なキーワード検証
        valid_keywords, validation_errors = self.validate_keywords(keywords)
        errors.extend(validation_errors)

        if not valid_keywords:
            return False, errors

        # 見出しレベルの重複チェック
        heading_keywords = [k for k in valid_keywords if k.startswith("見出し")]
        if len(heading_keywords) > 1:
            errors.append(
                f"複数の見出しレベルは使用できません: {', '.join(heading_keywords)}"
            )

        # details型（折りたたみ・ネタバレ）の重複チェック
        details_keywords = [
            k for k in valid_keywords if k in ["折りたたみ", "ネタバレ"]
        ]
        if len(details_keywords) > 1:
            errors.append(
                f"複数のdetails型は使用できません: {', '.join(details_keywords)}"
            )

        # 論理的に矛盾する組み合わせのチェック
        # 見出しとdetailsの組み合わせは推奨しない（警告レベル）
        if heading_keywords and details_keywords:
            errors.append(
                f"見出しとdetails型の組み合わせは推奨されません: 見出し={heading_keywords}, details={details_keywords}"
            )

        # 同じタグの重複チェック（警告レベル）
        warnings = self.check_keyword_conflicts(valid_keywords)
        errors.extend(warnings)

        return len(errors) == 0, errors

    def validate_color_value(self, color_value: str) -> tuple[bool, str | None]:
        """
        color属性値の妥当性を検証

        Args:
            color_value: 検証するcolor値

        Returns:
            tuple: (is_valid, error_message)
        """
        if not color_value:
            return False, "color値が空です"

        # 16進数カラーコード (#RGB, #RRGGBB)
        hex_pattern = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
        if hex_pattern.match(color_value):
            return True, None

        # CSS名前付きカラー（基本的なもの）
        named_colors = {
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "pink",
            "brown",
            "black",
            "white",
            "gray",
            "grey",
            "cyan",
            "magenta",
            "lime",
            "navy",
            "teal",
            "olive",
            "maroon",
            "silver",
            "aqua",
            "fuchsia",
            "lightblue",
            "lightgreen",
            "lightyellow",
            "lightgray",
            "darkblue",
            "darkgreen",
            "darkred",
            "transparent",
        }

        if color_value.lower() in named_colors:
            return True, None

        # RGB/RGBA形式 (rgb(r,g,b), rgba(r,g,b,a))
        rgb_pattern = re.compile(
            r"^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[0-9.]+)?\s*\)$"
        )
        if rgb_pattern.match(color_value):
            return True, None

        return (
            False,
            f"無効なcolor値です: '{color_value}' (例: #ff0000, red, rgb(255,0,0))",
        )

    def validate_attributes(self, attributes: dict[str, str]) -> list[str]:
        """
        属性値の妥当性を検証

        Args:
            attributes: 検証する属性辞書

        Returns:
            list[str]: エラーメッセージのリスト
        """
        errors = []

        # color属性の検証
        if "color" in attributes:
            is_valid, error_msg = self.validate_color_value(attributes["color"])
            if not is_valid:
                errors.append(error_msg)

        # alt属性の検証（画像用）
        if "alt" in attributes:
            alt_value = attributes["alt"]
            if len(alt_value) > 100:
                errors.append(
                    f"alt属性が長すぎます（100文字以内）: '{alt_value[:20]}...'"
                )

            # HTML特殊文字の検証
            if any(char in alt_value for char in ["<", ">", '"', "'"]):
                errors.append("alt属性にHTML特殊文字が含まれています")

        return errors
