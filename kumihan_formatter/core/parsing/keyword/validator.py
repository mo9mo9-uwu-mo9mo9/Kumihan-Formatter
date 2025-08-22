"""
キーワード検証とサジェスト - Issue #476対応

キーワードの有効性チェック、エラーメッセージ、サジェスト機能。
"""

import re
from difflib import get_close_matches
from typing import List

from .definitions import KeywordDefinitions


class KeywordValidator:
    """キーワード検証クラス"""

    def __init__(self, definitions: KeywordDefinitions) -> None:
        """キーワードバリデーターを初期化

        Args:
            definitions: キーワード定義
        """
        self.definitions = definitions

    def validate(self, text: str) -> list[str]:
        """テキストを解析してキーワード検証を実行（新記法のみ対応）

        Args:
            text: 検証対象のテキスト

        Returns:
            list[str]: エラーメッセージのリスト
        """
        # 新記法のみに対応
        if "#" in text or "＃" in text:
            # 新記法の解析
            keywords = self._extract_keywords_from_new_format(text)
            _, errors = self.validate_keywords(keywords)
            return errors
        else:
            return []  # 記法が見つからない場合はエラーなし

    def _extract_keywords_from_new_format(self, text: str) -> list[str]:
        """新記法からキーワードを抽出"""
        keywords: List[str] = []

        # #キーワード# 形式
        pattern = r"[#＃]([^#＃]+?)[#＃]"
        matches = re.findall(pattern, text)
        for match in matches:
            keyword = match.strip().split()[0]  # 最初の単語をキーワードとして扱う
            if keyword:
                keywords.append(keyword)

        return keywords

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

        # 特別な対応：英語-日本語キーワード対応
        english_to_japanese = {
            "アンダーライン": "下線",
            "太文字": "太字",
            "ボールド": "太字",
            "イタリクス": "イタリック",
            "ストライク": "取り消し線",
            "クォート": "引用",
        }

        # 特別対応のキーワードがあるかチェック
        if invalid_keyword in english_to_japanese:
            japanese_equivalent = english_to_japanese[invalid_keyword]
            if japanese_equivalent in all_keywords:
                return [japanese_equivalent]

        # まず標準的なcutoffで試行
        suggestions = get_close_matches(
            invalid_keyword, all_keywords, n=max_suggestions, cutoff=0.6
        )

        # 候補が見つからない場合は、より寛容なcutoffで再試行
        if not suggestions:
            suggestions = get_close_matches(
                invalid_keyword, all_keywords, n=max_suggestions, cutoff=0.3
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

        suggestions = self.get_keyword_suggestions(keyword)
        error_msg = f"不明なキーワード: {keyword}"
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
        errors: List[str] = []

        # 基本的なキーワード検証
        valid_keywords, validation_errors = self.validate_keywords(keywords)
        errors.extend(validation_errors)

        if not valid_keywords:
            return False, errors

        # 見出し系とdetails系の組み合わせチェック
        heading_keywords = [k for k in valid_keywords if k.startswith("見出し")]
        details_keywords = [
            k for k in valid_keywords if k in ["折りたたみ", "ネタバレ"]
        ]

        if heading_keywords and details_keywords:
            errors.append(
                f"見出しとdetails型の組み合わせは推奨されません: "
                f"見出し={heading_keywords}, details={details_keywords}"
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

        # 色名定義
        named_colors = {
            "red",
            "blue",
            "green",
            "yellow",
            "orange",
            "purple",
            "black",
            "white",
            "gray",
            "pink",
            "brown",
            "cyan",
            "magenta",
            "lime",
            "navy",
            "silver",
        }

        if color_value.lower() in named_colors:
            return True, None

        # 16進数色コードの検証
        if color_value.startswith("#") and len(color_value) in [4, 7]:
            hex_part = color_value[1:]
            if all(c in "0123456789abcdefABCDEF" for c in hex_part):
                return True, None

        return False, f"無効なcolor値: {color_value}"

    def validate_attributes(self, attributes: dict[str, str]) -> list[str]:
        """
        属性値の妥当性を検証

        Args:
            attributes: 検証する属性辞書

        Returns:
            list[str]: エラーメッセージのリスト
        """
        errors: List[str] = []

        # color属性の検証
        if "color" in attributes:
            is_valid, error_msg = self.validate_color_value(attributes["color"])
            if not is_valid and error_msg is not None:
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
