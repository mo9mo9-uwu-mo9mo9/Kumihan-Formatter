"""パーサー共通機能Mixin

Issue #880 Phase 2: 再利用可能な機能コンポーネント
既存パーサーの共通機能を抽出・統合
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from ...utilities.logger import get_logger


class CachingMixin:
    """キャッシング機能Mixin"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = True

    def _get_cache_key(self, content: Union[str, List[str]], extra: str = "") -> str:
        """キャッシュキーを生成"""
        if isinstance(content, str):
            content_hash = hash(content)
        else:
            content_hash = hash(tuple(content))

        parser_type = getattr(self, "parser_type", "unknown")
        return f"{parser_type}:{content_hash}:{extra}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        if self._cache_enabled and key in self._cache:
            return self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """キャッシュに保存"""
        if self._cache_enabled:
            self._cache[key] = value


class ValidationMixin:
    """検証機能Mixin"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._validation_errors: List[str] = []
        self._validation_warnings: List[str] = []

    def _validate_content_structure(self, content: Union[str, List[str]]) -> bool:
        """コンテンツ構造の基本検証"""
        self._validation_errors.clear()
        self._validation_warnings.clear()

        if not content:
            self._validation_errors.append("空のコンテンツです")
            return False

        if isinstance(content, str):
            if len(content.strip()) == 0:
                self._validation_errors.append("空文字列です")
                return False
        elif isinstance(content, list):
            if not any(line.strip() for line in content if isinstance(line, str)):
                self._validation_errors.append("有効な行がありません")
                return False

        return True

    def _validate_encoding(self, content: str) -> bool:
        """エンコーディングの検証"""
        try:
            content.encode("utf-8")
            return True
        except UnicodeEncodeError as e:
            self._validation_errors.append(f"エンコーディングエラー: {e}")
            return False

    def _validate_line_length(
        self, content: Union[str, List[str]], max_length: int = 1000
    ) -> bool:
        """行長の検証"""
        lines = content.split("\n") if isinstance(content, str) else content

        for i, line in enumerate(lines):
            if len(line) > max_length:
                self._validation_warnings.append(
                    f"行 {i+1} が長すぎます: {len(line)} > {max_length} 文字"
                )

        return True


class PatternMatchingMixin:
    """パターンマッチング機能Mixin"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """共通パターンの設定"""
        # Kumihan記法パターン
        self.kumihan_patterns = {
            "block_start": re.compile(r"^#\s*([^#]+?)\s*#"),
            "block_end": re.compile(r"##\s*$"),
            "inline_block": re.compile(r"^#\s*([^#]+?)\s*#([^#]*?)##$"),
            "keyword_attributes": re.compile(r"\[([^\]]+)\]"),
            "color_attribute": re.compile(r"\[color:([#a-zA-Z0-9]+)\]"),
        }

        # Markdown パターン
        self.markdown_patterns = {
            "heading": re.compile(r"^#{1,6}\s+"),
            "bold": re.compile(r"\*\*([^*]+)\*\*"),
            "italic": re.compile(r"\*([^*]+)\*"),
            "code": re.compile(r"`([^`]+)`"),
            "link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
        }

        # リストパターン
        self.list_patterns = {
            "unordered": re.compile(r"^\s*[-*+]\s+"),
            "ordered": re.compile(r"^\s*\d+\.\s+"),
            "nested": re.compile(r"^(\s+)[-*+]\s+"),
        }

    def _match_kumihan_block(self, line: str) -> Optional[Dict[str, str]]:
        """Kumihanブロック記法のマッチング"""
        match = self.kumihan_patterns["inline_block"].match(line)
        if match:
            return {
                "keyword": match.group(1).strip(),
                "content": match.group(2).strip(),
                "type": "inline_block",
            }

        # ブロック開始のマッチング
        match = self.kumihan_patterns["block_start"].match(line)
        if match:
            return {"keyword": match.group(1).strip(), "type": "block_start"}

        return None

    def _extract_attributes(self, text: str) -> Tuple[str, Dict[str, str]]:
        """属性の抽出"""
        attributes = {}
        clean_text = text

        # 色属性の抽出
        color_match = self.kumihan_patterns["color_attribute"].search(text)
        if color_match:
            attributes["color"] = color_match.group(1)
            clean_text = self.kumihan_patterns["color_attribute"].sub("", clean_text)

        # 一般属性の抽出
        for match in self.kumihan_patterns["keyword_attributes"].finditer(text):
            attr_text = match.group(1)
            if ":" in attr_text:
                key, value = attr_text.split(":", 1)
                attributes[key.strip()] = value.strip()

        # 属性部分を除去
        clean_text = (
            self.kumihan_patterns["keyword_attributes"].sub("", clean_text).strip()
        )

        return clean_text, attributes


class FormattingMixin:
    """フォーマット機能Mixin"""

    def _normalize_whitespace(self, text: str) -> str:
        """空白の正規化"""
        # 連続する空白を単一スペースに
        text = re.sub(r"\s+", " ", text)
        # 前後の空白を削除
        return text.strip()

    def _normalize_line_endings(self, content: str) -> str:
        """改行コードの正規化"""
        return content.replace("\r\n", "\n").replace("\r", "\n")

    def _clean_html_entities(self, text: str) -> str:
        """HTMLエンティティのクリーンアップ"""
        html_entities = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
        }

        for entity, char in html_entities.items():
            text = text.replace(entity, char)

        return text

    def _escape_special_chars(self, text: str) -> str:
        """特殊文字のエスケープ"""
        special_chars = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
            "&": "&amp;",
        }

        for char, escaped in special_chars.items():
            text = text.replace(char, escaped)

        return text


class ErrorHandlingMixin:
    """エラーハンドリング機能Mixin"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._errors: List[str] = []
        self._warnings: List[str] = []
        self.logger = get_logger(self.__class__.__name__)

    def _add_error(self, message: str, context: Optional[str] = None) -> None:
        """エラーメッセージを追加"""
        full_message = f"{message}"
        if context:
            full_message += f" (コンテキスト: {context})"

        self._errors.append(full_message)
        self.logger.error(full_message)

    def _add_warning(self, message: str, context: Optional[str] = None) -> None:
        """警告メッセージを追加"""
        full_message = f"{message}"
        if context:
            full_message += f" (コンテキスト: {context})"

        self._warnings.append(full_message)
        self.logger.warning(full_message)

    def _clear_messages(self) -> None:
        """メッセージをクリア"""
        self._errors.clear()
        self._warnings.clear()

    def _has_errors(self) -> bool:
        """エラーがあるかチェック"""
        return len(self._errors) > 0

    def _has_warnings(self) -> bool:
        """警告があるかチェック"""
        return len(self._warnings) > 0


class PerformanceMixin:
    """パフォーマンス機能Mixin"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._performance_stats: Dict[str, Any] = {}

    def _start_timer(self, operation: str) -> None:
        """タイマー開始"""
        self._performance_stats[f"{operation}_start"] = time.time()

    def _end_timer(self, operation: str) -> float:
        """タイマー終了して経過時間を返す"""

        start_key = f"{operation}_start"
        if start_key in self._performance_stats:
            elapsed = time.time() - self._performance_stats[start_key]
            self._performance_stats[f"{operation}_elapsed"] = elapsed
            return cast(float, elapsed)
        return 0.0

    def _get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        return self._performance_stats.copy()


class CompositeMixin(
    CachingMixin,
    ValidationMixin,
    PatternMatchingMixin,
    FormattingMixin,
    ErrorHandlingMixin,
    PerformanceMixin,
):
    """すべてのMixinを統合したコンポジットMixin"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
