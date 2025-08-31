"""Keyword Parser Validation - キーワードパーサーバリデーション

分離された責任:
- キーワード構文チェック
- 単一キーワードの妥当性チェック
- バリデーションキャッシュ管理
"""

from typing import List, Optional
import logging

if TYPE_CHECKING:
    pass

from .utils_core import create_cache_key


class KeywordValidator:
    """キーワードバリデーション専用クラス"""

    def __init__(self, config: "KeywordParserConfig") -> None:
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.cache = config.cache

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """キーワード構文チェック"""
        # キャッシュ確認
        cache_key = create_cache_key(content, "validate")
        cached_errors = self.cache.get_validation_cache(cache_key)
        if cached_errors is not None:
            return list(cached_errors)  # 明示的にリストに変換

        errors: List[str] = []

        if not content.strip():
            self.cache.set_validation_cache(cache_key, errors)
            return errors  # 空コンテンツは有効

        try:
            # キーワード抽出
            keyword_info = self.config.keyword_extractor.extract_keyword_info(content)
            if not keyword_info:
                self.cache.set_validation_cache(cache_key, errors)
                return errors  # キーワードなしは有効

            # 各バリデーター実行
            for (
                validator_name,
                validator,
            ) in self.config.validator_collection.validators.items():
                try:
                    validator_errors: List[str] = validator(keyword_info)
                    for error in validator_errors:
                        errors.append(f"{validator_name}: {error}")
                except Exception as e:
                    errors.append(f"Validation error ({validator_name}): {e}")

        except Exception as e:
            errors.append(f"Validation failed: {e}")

        # キャッシュ保存
        self.cache.set_validation_cache(cache_key, errors)
        return errors

    def validate_keyword(
        self, keyword: str, context: Optional["ParseContext"] = None
    ) -> bool:
        """単一キーワードの妥当性チェック（プロトコル準拠）"""
        # キャッシュ確認
        cache_key = f"validate_{keyword}_{id(context) if context else 0}"
        cached_result = self.cache.get_keyword_cache(cache_key)
        if cached_result is not None:
            return bool(cached_result.get("valid", False))

        # キーワード妥当性チェック
        is_valid: bool = (
            keyword in self.config.all_keywords
            or keyword in self.config.custom_handler.custom_handlers
            or self.config.custom_handler.is_valid_custom_keyword(keyword)
        )

        # キャッシュ保存
        self.cache.set_keyword_cache(
            cache_key, {"valid": is_valid} if is_valid else None
        )
        return is_valid
