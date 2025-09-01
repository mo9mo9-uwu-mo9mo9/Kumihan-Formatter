"""Parser Utils - パーサーユーティリティ統合モジュール

Issue #1252対応: パーサー関連ユーティリティの統合
以下のコンポーネントを統合:
- utils_core.py (コアユーティリティ)
- keyword_config.py (キーワード設定)
- keyword_validation.py (キーワード検証)
- keyword_extractors.py (キーワード抽出)

統合により重複処理を排除し、統一されたユーティリティ機能を提供
"""

import warnings
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..core.utilities.logger import get_logger
from .utils import (
    DEFAULT_KEYWORD_CONFIG,
    DEFAULT_VALIDATION_RULES,
    DEFAULT_EXTRACTION_CONFIG,
    build_keyword_patterns,
    build_validation_patterns,
    build_utility_patterns,
    normalize_with_patterns,
)


class ParserUtilsError(Exception):
    """パーサーユーティリティ固有のエラー"""

    pass


class KeywordValidationError(Exception):
    """キーワード検証エラー"""

    pass


class ExtractionError(Exception):
    """抽出処理エラー"""

    pass


class ParserUtils:
    """統合パーサーユーティリティクラス

    Issue #1252対応:
    - ユーティリティ機能統合
    - キーワード設定・検証・抽出統合
    - 共通処理の統一化
    - エラーハンドリング統一
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """ParserUtils初期化

        Args:
            config: ユーティリティ設定辞書
        """
        self.config = config or {}
        self.logger = get_logger(__name__)

        # 設定初期化
        self._initialize_configurations()
        self._initialize_patterns()
        self._initialize_validators()

    def _initialize_configurations(self) -> None:
        """設定初期化（keyword_config.py統合）"""
        # キーワード/検証/抽出の既定値を読み込み
        self.keyword_config = {k: set(v) for k, v in DEFAULT_KEYWORD_CONFIG.items()}
        self.validation_rules = dict(DEFAULT_VALIDATION_RULES)
        self.extraction_config = dict(DEFAULT_EXTRACTION_CONFIG)

    def _initialize_patterns(self) -> None:
        """パターン初期化"""
        # パターンはビルダーから生成
        self.keyword_patterns = build_keyword_patterns()
        self.validation_patterns = build_validation_patterns()
        self.utility_patterns = build_utility_patterns()

    def _initialize_validators(self) -> None:
        """バリデーター初期化"""
        # 組み込みバリデーター関数
        self.validators = {
            "length": self._validate_length,
            "characters": self._validate_characters,
            "format": self._validate_format,
            "reserved": self._validate_reserved,
            "structure": self._validate_structure,
        }

    def get_all_keywords(self) -> Set[str]:
        """全キーワード取得

        Returns:
            全キーワードのセット
        """
        all_keywords = set()
        for category in self.keyword_config.values():
            all_keywords.update(category)
        return all_keywords

    def get_keywords_by_category(self, category: str) -> Set[str]:
        """カテゴリ別キーワード取得

        Args:
            category: キーワードカテゴリ

        Returns:
            指定カテゴリのキーワードセット
        """
        return self.keyword_config.get(category, set())

    def validate_keyword(self, keyword: str) -> bool:
        """キーワード検証（keyword_validation.py統合）

        Args:
            keyword: 検証対象キーワード

        Returns:
            検証結果
        """
        try:
            if not keyword:
                return False

            # 各バリデーター実行
            for validator_name, validator_func in self.validators.items():
                if not validator_func(keyword):
                    self.logger.debug(
                        f"キーワード検証失敗({validator_name}): {keyword}"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"キーワード検証エラー: {e}")
            raise KeywordValidationError(
                f"Validation error for keyword '{keyword}': {e}"
            )

    def extract_keywords(self, content: str, pattern_type: str = "basic") -> List[str]:
        """キーワード抽出（keyword_extractors.py統合）

        Args:
            content: 抽出対象コンテンツ
            pattern_type: 抽出パターンタイプ

        Returns:
            抽出されたキーワードリスト
        """
        try:
            if not content:
                return []

            pattern = self.keyword_patterns.get(
                pattern_type, self.keyword_patterns["basic"]
            )
            matches = pattern.findall(content)

            # 重複除去・検証
            valid_keywords = []
            for match in matches:
                if self.validate_keyword(match):
                    valid_keywords.append(match)

            # 設定に応じた後処理
            if not self.extraction_config["preserve_whitespace"]:
                valid_keywords = [kw.strip() for kw in valid_keywords]

            if not self.extraction_config["case_sensitive"]:
                # ケース統一（日本語は影響しない）
                valid_keywords = [kw.lower() for kw in valid_keywords]

            return list(dict.fromkeys(valid_keywords))  # 順序を保持した重複除去

        except Exception as e:
            self.logger.error(f"キーワード抽出エラー: {e}")
            raise ExtractionError(f"Keyword extraction failed: {e}")

    def normalize_content(self, content: str) -> str:
        """コンテンツ正規化（utils_core.py統合）

        Args:
            content: 正規化対象コンテンツ

        Returns:
            正規化後コンテンツ
        """
        if not content:
            return ""

        try:
            return normalize_with_patterns(content, self.utility_patterns)

        except Exception as e:
            self.logger.error(f"コンテンツ正規化エラー: {e}")
            return content  # エラー時は元のコンテンツを返却

    def split_compound_keywords(self, keyword: str) -> List[str]:
        """複合キーワード分割

        Args:
            keyword: 分割対象キーワード

        Returns:
            分割されたキーワードリスト
        """
        if not keyword:
            return []

        # 区切り文字による分割
        separators = ["-", "_", " ", "　"]  # 半角スペース、全角スペース含む

        parts = [keyword]
        for separator in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(separator))
            parts = new_parts

        # 空文字列除去・検証
        valid_parts = []
        for part in parts:
            part = part.strip()
            if part and self.validate_keyword(part):
                valid_parts.append(part)

        return valid_parts

    def find_keyword_in_categories(self, keyword: str) -> Optional[str]:
        """キーワードのカテゴリ検索

        Args:
            keyword: 検索対象キーワード

        Returns:
            見つかったカテゴリ名（見つからない場合はNone）
        """
        for category_name, keywords in self.keyword_config.items():
            if keyword in keywords:
                return category_name
        return None

    def suggest_similar_keywords(
        self, keyword: str, max_suggestions: int = 5
    ) -> List[str]:
        """類似キーワード提案

        Args:
            keyword: 基準キーワード
            max_suggestions: 最大提案数

        Returns:
            類似キーワードリスト
        """
        if not keyword:
            return []

        all_keywords = self.get_all_keywords()
        suggestions = []

        # 前方一致チェック
        prefix_matches = [kw for kw in all_keywords if kw.startswith(keyword)]
        suggestions.extend(prefix_matches[:max_suggestions])

        # 部分一致チェック（前方一致と重複しないもの）
        if len(suggestions) < max_suggestions:
            partial_matches = [
                kw for kw in all_keywords if keyword in kw and kw not in suggestions
            ]
            suggestions.extend(partial_matches[: max_suggestions - len(suggestions)])

        return suggestions[:max_suggestions]

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得

        Returns:
            パーサーユーティリティ統計情報
        """
        all_keywords = self.get_all_keywords()

        return {
            "total_keywords": len(all_keywords),
            "categories": list(self.keyword_config.keys()),
            "category_counts": {
                category: len(keywords)
                for category, keywords in self.keyword_config.items()
            },
            "validation_rules": len(self.validators),
            "extraction_patterns": len(self.keyword_patterns),
            "utility_patterns": len(self.utility_patterns),
        }

    # プライベートバリデーターメソッド
    def _validate_length(self, keyword: str) -> bool:
        """長さ検証"""
        raw_min = self.validation_rules.get("min_keyword_length", 1)
        raw_max = self.validation_rules.get("max_keyword_length", 255)

        def _to_int(x: Any, default: int) -> int:
            try:
                if isinstance(x, (int,)):
                    return int(x)
                if isinstance(x, str) and x.isdigit():
                    return int(x)
            except Exception:
                pass
            return default

        min_len: int = _to_int(raw_min, 1)
        max_len: int = _to_int(raw_max, 255)
        return min_len <= len(keyword) <= max_len

    def _validate_characters(self, keyword: str) -> bool:
        """文字検証"""
        return bool(self.validation_patterns["valid_chars"].match(keyword))

    def _validate_format(self, keyword: str) -> bool:
        """フォーマット検証"""
        # 不正な開始・終了文字チェック
        if self.validation_patterns["invalid_start"].match(keyword):
            return False
        if self.validation_patterns["invalid_end"].search(keyword):
            return False
        # 連続特殊文字チェック
        if self.validation_patterns["consecutive_special"].search(keyword):
            return False
        return True

    def _validate_reserved(self, keyword: str) -> bool:
        """予約語検証"""
        reserved: set[str] | list[str] = self.validation_rules["reserved_keywords"]
        return keyword not in set(reserved)

    def _validate_structure(self, keyword: str) -> bool:
        """構造検証（追加のルール）"""
        # 数字のみは無効
        if keyword.isdigit():
            return False
        # 特殊文字のみは無効
        if all(
            not c.isalnum() and c not in "\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf"
            for c in keyword
        ):
            return False
        return True


# 便利関数（統合）
def validate_keyword(keyword: str) -> bool:
    """キーワード検証便利関数

    Args:
        keyword: 検証対象キーワード

    Returns:
        検証結果
    """
    utils = ParserUtils()
    return utils.validate_keyword(keyword)


def extract_keywords_from_content(content: str) -> List[str]:
    """コンテンツからキーワード抽出便利関数

    Args:
        content: 抽出対象コンテンツ

    Returns:
        抽出されたキーワードリスト
    """
    utils = ParserUtils()
    return utils.extract_keywords(content)


def normalize_text(text: str) -> str:
    """テキスト正規化便利関数

    Args:
        text: 正規化対象テキスト

    Returns:
        正規化後テキスト
    """
    utils = ParserUtils()
    return utils.normalize_content(text)


# レガシー互換関数
def get_keyword_categories() -> Dict[str, Set[str]]:
    """キーワードカテゴリ取得（レガシー互換）"""
    warnings.warn(
        "get_keyword_categories() is deprecated. Use ParserUtils.keyword_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    utils = ParserUtils()
    return utils.keyword_config


def validate_keyword_legacy(keyword: str) -> bool:
    """レガシーキーワード検証"""
    warnings.warn(
        "validate_keyword_legacy() is deprecated. Use validate_keyword() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return validate_keyword(keyword)


# エクスポート定義
__all__ = [
    # 統合エラークラス
    "ParserUtilsError",
    "KeywordValidationError",
    "ExtractionError",
    # メインクラス
    "ParserUtils",
    # 便利関数
    "validate_keyword",
    "extract_keywords_from_content",
    "normalize_text",
    # レガシー互換関数
    "get_keyword_categories",
    "validate_keyword_legacy",
]
