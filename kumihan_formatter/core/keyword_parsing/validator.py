"""
キーワード検証とサジェスト - Issue #476対応

キーワードの有効性チェック、エラーメッセージ、サジェスト機能。
"""

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
