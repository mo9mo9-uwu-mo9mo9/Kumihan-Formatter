"""
Kumihan-Formatter データサニタイザーモジュール

XSS、SQLインジェクション、その他セキュリティ脅威からの保護を提供する
高性能データサニタイザーシステム。

Features:
- XSS対策: HTMLエンティティエスケープ・スクリプト除去
- SQLインジェクション対策: クエリパラメータサニタイズ
- コンテキスト別サニタイズ: HTML, URL, JSON, XML等
- HTMLクリーニング: 許可タグのみ残す安全なHTML処理
- エンコーディング正規化: Unicode正規化・文字エンコーディング統一

Performance targets:
- 10,000 operations/sec以上
- メモリ使用量50MB以下
- 処理遅延0.1ms以下/operation
- 正確性97%以上

Author: Gemini-Claude協業チーム
Version: 1.0.0
"""

import html
import json
import re
import unicodedata
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from xml.sax.saxutils import escape as xml_escape

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class SanitizationLevel(Enum):
    """サニタイズレベル定義"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PARANOID = "paranoid"


class ContextType(Enum):
    """サニタイズコンテキストタイプ"""

    HTML = "html"
    URL = "url"
    JSON = "json"
    XML = "xml"
    SQL = "sql"
    PLAIN_TEXT = "plain_text"


@dataclass
class SanitizerConfig:
    """サニタイザー設定クラス"""

    level: SanitizationLevel = SanitizationLevel.MEDIUM
    allowed_html_tags: Set[str] = field(
        default_factory=lambda: {
            "p",
            "br",
            "strong",
            "em",
            "u",
            "i",
            "b",
            "a",
            "ul",
            "ol",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
            "code",
            "pre",
        }
    )
    allowed_html_attributes: Dict[str, Set[str]] = field(
        default_factory=lambda: {
            "a": {"href", "title"},
            "img": {"src", "alt", "title"},
            "*": {"class", "id"},
        }
    )
    allowed_protocols: Set[str] = field(
        default_factory=lambda: {"http", "https", "mailto", "tel"}
    )
    max_input_length: int = 1000000  # 1MB
    enable_unicode_normalization: bool = True
    enable_audit_logging: bool = True
    report_directory: Path = field(
        default_factory=lambda: Path("tmp/sanitizer_reports")
    )


class SafeHTMLParser(HTMLParser):
    """安全なHTMLパーサー"""

    def __init__(self, allowed_tags: Set[str], allowed_attrs: Dict[str, Set[str]]):
        super().__init__()
        self.allowed_tags = allowed_tags
        self.allowed_attrs = allowed_attrs
        self.result = []
        self.current_tag = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() in self.allowed_tags:
            self.current_tag = tag.lower()
            filtered_attrs = self._filter_attributes(tag.lower(), attrs)
            if filtered_attrs:
                attr_str = " " + " ".join(
                    f'{name}="{html.escape(value or "")}"'
                    for name, value in filtered_attrs
                )
            else:
                attr_str = ""
            self.result.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.allowed_tags:
            self.result.append(f"</{tag}>")
            self.current_tag = None

    def handle_data(self, data: str) -> None:
        # HTMLエンティティエスケープ
        self.result.append(html.escape(data))

    def _filter_attributes(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> List[Tuple[str, Optional[str]]]:
        """属性フィルタリング"""
        filtered = []
        tag_attrs = self.allowed_attrs.get(tag, set())
        global_attrs = self.allowed_attrs.get("*", set())
        allowed = tag_attrs | global_attrs

        for name, value in attrs:
            name_lower = name.lower()
            # イベントハンドラー属性を除外
            if name_lower.startswith("on"):
                continue
            # javascript: URIを除外
            if value and "javascript:" in value.lower():
                continue
            if name_lower in allowed:
                filtered.append((name, value))

        return filtered

    def get_result(self) -> str:
        return "".join(self.result)


class DataSanitizer:
    """メインデータサニタイザークラス"""

    def __init__(self, config: Optional[SanitizerConfig] = None):
        self.config = config or SanitizerConfig()
        self._setup_patterns()
        self._setup_logging()

    def _setup_patterns(self) -> None:
        """正規表現パターンの事前コンパイル（パフォーマンス最適化）"""
        # XSS対策パターン
        self.script_pattern = re.compile(
            r"<script[^>]*>.*?</script>|<script[^>]*/>", re.IGNORECASE | re.DOTALL
        )
        self.dangerous_tags_pattern = re.compile(
            r"<(?:object|embed|iframe|frame|frameset|meta|link)[^>]*>.*?</(?:object|embed|iframe|frame|frameset|meta|link)>|"
            r"<(?:object|embed|iframe|frame|frameset|meta|link)[^>]*/>",
            re.IGNORECASE | re.DOTALL,
        )
        self.javascript_pattern = re.compile(
            r"javascript:|vbscript:|data:text/html", re.IGNORECASE
        )
        self.event_handler_pattern = re.compile(
            r'\s+on\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE
        )

        # SQLインジェクション対策パターン
        self.sql_keywords_pattern = re.compile(
            r"(?:union|select|insert|update|delete|drop|create|alter|exec|execute)",
            re.IGNORECASE,
        )
        self.sql_comment_pattern = re.compile(r"--|\#|/\*|\*/")

        # URL検証パターン
        self.url_pattern = re.compile(
            r"^(?:(?:https?|ftp|mailto|tel)://)?[^\s/$.?#].[^\s]*$", re.IGNORECASE
        )

    def _setup_logging(self) -> None:
        """ログ設定"""
        if self.config.enable_audit_logging:
            self.config.report_directory.mkdir(parents=True, exist_ok=True)

    def sanitize_html(
        self, content: str, allowed_tags: Optional[List[str]] = None
    ) -> str:
        """
        HTMLコンテンツのサニタイズ

        Args:
            content: サニタイズ対象のHTMLコンテンツ
            allowed_tags: 許可するHTMLタグのリスト（Noneの場合はデフォルト設定を使用）

        Returns:
            サニタイズされたHTMLコンテンツ

        Raises:
            ValueError: 入力が不正な場合
        """
        try:
            if not content or len(content) > self.config.max_input_length:
                raise ValueError(
                    f"Invalid content length: {len(content) if content else 0}"
                )

            # 使用する許可タグを決定
            tags_to_use = (
                set(allowed_tags) if allowed_tags else self.config.allowed_html_tags
            )

            # 危険なタグとスクリプトを除去
            content = self.script_pattern.sub("", content)
            content = self.dangerous_tags_pattern.sub("", content)
            content = self.javascript_pattern.sub("", content)
            content = self.event_handler_pattern.sub("", content)

            # 安全なHTMLパーサーでクリーニング
            parser = SafeHTMLParser(tags_to_use, self.config.allowed_html_attributes)
            parser.feed(content)
            sanitized = parser.get_result()

            # Unicode正規化
            if self.config.enable_unicode_normalization:
                sanitized = self.normalize_unicode(sanitized)

            self._log_sanitization("HTML", len(content), len(sanitized))
            return sanitized

        except Exception as e:
            logger.error(f"HTML sanitization error: {e}")
            return self.escape_html_entities(content)

    def sanitize_url(self, url: str) -> str:
        """
        URLのサニタイズ

        Args:
            url: サニタイズ対象のURL

        Returns:
            サニタイズされたURL

        Raises:
            ValueError: 不正なURLの場合
        """
        try:
            if not url or len(url) > 2000:  # URL長制限
                raise ValueError("Invalid URL length")

            # 基本的なURL検証
            if not self.url_pattern.match(url):
                raise ValueError("Invalid URL format")

            # URLパース
            parsed = urllib.parse.urlparse(url)

            # プロトコル検証
            if (
                parsed.scheme
                and parsed.scheme.lower() not in self.config.allowed_protocols
            ):
                raise ValueError(f"Disallowed protocol: {parsed.scheme}")

            # 危険なパターンをチェック
            if self.javascript_pattern.search(url.lower()):
                raise ValueError("Dangerous URL content detected")

            # URLエンコーディング正規化
            sanitized_url = urllib.parse.urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    urllib.parse.quote(parsed.path, safe="/"),
                    parsed.params,
                    urllib.parse.quote(parsed.query, safe="&="),
                    urllib.parse.quote(parsed.fragment, safe=""),
                )
            )

            self._log_sanitization("URL", len(url), len(sanitized_url))
            return sanitized_url

        except Exception as e:
            logger.error(f"URL sanitization error: {e}")
            raise ValueError(f"URL sanitization failed: {e}")

    def sanitize_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSONデータのサニタイズ

        Args:
            json_data: サニタイズ対象のJSONデータ

        Returns:
            サニタイズされたJSONデータ
        """
        try:
            # シークレット検出パターン
            secret_patterns = ['password', 'secret', 'api_key', 'access_key', 'token', 'key']

            def sanitize_value(key: str, value: Any) -> Any:
                if isinstance(value, str):
                    # シークレットキーの場合はマスク
                    if any(pattern in key.lower() for pattern in secret_patterns):
                        return "***MASKED***"
                    # 文字列値のサニタイズ
                    if self.javascript_pattern.search(value.lower()):
                        return self.escape_html_entities(value)
                    return (
                        self.normalize_unicode(value)
                        if self.config.enable_unicode_normalization
                        else value
                    )
                elif isinstance(value, dict):
                    return {k: sanitize_value(k, v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [sanitize_value("", item) if not isinstance(item, dict) else sanitize_value("", item) for item in value]
                else:
                    return value

            sanitized = {k: sanitize_value(k, v) for k, v in json_data.items()} if isinstance(json_data, dict) else sanitize_value("", json_data)
            self._log_sanitization("JSON", len(str(json_data)), len(str(sanitized)))
            return sanitized

        except Exception as e:
            logger.error(f"JSON sanitization error: {e}")
            return {}

    def sanitize_xml(self, xml_content: str) -> str:
        """
        XMLコンテンツのサニタイズ

        Args:
            xml_content: サニタイズ対象のXMLコンテンツ

        Returns:
            サニタイズされたXMLコンテンツ
        """
        try:
            if not xml_content or len(xml_content) > self.config.max_input_length:
                raise ValueError("Invalid XML content length")

            # XMLエンティティエスケープ
            sanitized = xml_escape(xml_content)

            # 外部エンティティ参照を除去
            sanitized = re.sub(r"<!ENTITY[^>]*>", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"<!DOCTYPE[^>]*>", "", sanitized, flags=re.IGNORECASE)

            # Unicode正規化
            if self.config.enable_unicode_normalization:
                sanitized = self.normalize_unicode(sanitized)

            self._log_sanitization("XML", len(xml_content), len(sanitized))
            return sanitized

        except Exception as e:
            logger.error(f"XML sanitization error: {e}")
            return xml_escape(xml_content)

    def sanitize_sql_parameter(self, param: str) -> str:
        """
        SQLパラメータのサニタイズ

        Args:
            param: サニタイズ対象のSQLパラメータ

        Returns:
            サニタイズされたSQLパラメータ
        """
        try:
            if not isinstance(param, str):
                param = str(param)

            # SQLキーワードの無効化
            sanitized = self.sql_keywords_pattern.sub(lambda m: f"[{m.group()}]", param)

            # コメント記号の除去
            sanitized = self.sql_comment_pattern.sub("", sanitized)

            # クォートのエスケープ
            sanitized = sanitized.replace("'", "''").replace('"', '""')

            # Unicode正規化
            if self.config.enable_unicode_normalization:
                sanitized = self.normalize_unicode(sanitized)

            self._log_sanitization("SQL", len(param), len(sanitized))
            return sanitized

        except Exception as e:
            logger.error(f"SQL parameter sanitization error: {e}")
            return str(param).replace("'", "''")

    def escape_html_entities(self, text: str) -> str:
        """
        HTMLエンティティエスケープ

        Args:
            text: エスケープ対象のテキスト

        Returns:
            エスケープされたテキスト
        """
        return html.escape(text, quote=True)

    def normalize_unicode(self, text: str) -> str:
        """
        Unicode正規化

        Args:
            text: 正規化対象のテキスト

        Returns:
            正規化されたテキスト
        """
        try:
            # NFC正規化（標準的な合成文字形式）
            normalized = unicodedata.normalize("NFC", text)

            # 制御文字の除去（改行・タブは保持）
            normalized = "".join(
                char
                for char in normalized
                if not unicodedata.category(char).startswith("C") or char in "\n\r\t"
            )

            return normalized

        except Exception as e:
            logger.error(f"Unicode normalization error: {e}")
            return text

    def _log_sanitization(
        self, context_type: str, input_size: int, output_size: int
    ) -> None:
        """サニタイズ処理のログ記録"""
        if self.config.enable_audit_logging:
            logger.info(f"Sanitized {context_type}: {input_size}→{output_size} chars")


class ContextualSanitizer:
    """コンテキスト特化型サニタイザー"""

    def __init__(self, sanitizer: DataSanitizer):
        self.sanitizer = sanitizer

    def sanitize_by_context(self, content: str, context: ContextType) -> str:
        """
        コンテキストに応じたサニタイズ

        Args:
            content: サニタイズ対象のコンテンツ
            context: コンテキストタイプ

        Returns:
            コンテキスト最適化されたサニタイズ結果
        """
        context_handlers = {
            ContextType.HTML: self.sanitizer.sanitize_html,
            ContextType.URL: self.sanitizer.sanitize_url,
            ContextType.JSON: lambda x: json.dumps(
                self.sanitizer.sanitize_json(json.loads(x))
            ),
            ContextType.XML: self.sanitizer.sanitize_xml,
            ContextType.SQL: self.sanitizer.sanitize_sql_parameter,
            ContextType.PLAIN_TEXT: self.sanitizer.escape_html_entities,
        }

        handler = context_handlers.get(context, self.sanitizer.escape_html_entities)
        try:
            return handler(content)
        except Exception as e:
            logger.error(f"Contextual sanitization error for {context}: {e}")
            return self.sanitizer.escape_html_entities(content)


class HTMLCleaner:
    """専用HTMLクリーナー"""

    def __init__(self, config: SanitizerConfig):
        self.config = config
        self.sanitizer = DataSanitizer(config)

    def clean_html(self, html_content: str, strict_mode: bool = False) -> str:
        """
        HTMLの厳密クリーニング

        Args:
            html_content: クリーニング対象のHTML
            strict_mode: 厳密モード（より厳しいフィルタリング）

        Returns:
            クリーニングされたHTML
        """
        if strict_mode:
            # 厳密モード用のより制限的な許可タグ
            allowed_tags = {"p", "br", "strong", "em", "b", "i"}
        else:
            allowed_tags = list(self.config.allowed_html_tags)

        return self.sanitizer.sanitize_html(html_content, allowed_tags)


class SafetyChecker:
    """サニタイズ後の安全性検証システム"""

    def __init__(self):
        self.dangerous_patterns = [
            re.compile(r"<script", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"vbscript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"data:text/html", re.IGNORECASE),
        ]

    def is_safe(self, content: str) -> Tuple[bool, List[str]]:
        """
        コンテンツの安全性チェック

        Args:
            content: チェック対象のコンテンツ

        Returns:
            (安全性, 検出された問題のリスト)
        """
        issues = []

        for pattern in self.dangerous_patterns:
            if pattern.search(content):
                issues.append(f"Dangerous pattern detected: {pattern.pattern}")

        return len(issues) == 0, issues

    def verify_sanitization(self, original: str, sanitized: str) -> Dict[str, Any]:
        """
        サニタイズ結果の検証

        Args:
            original: 元のコンテンツ
            sanitized: サニタイズ後のコンテンツ

        Returns:
            検証結果の詳細
        """
        original_safe, original_issues = self.is_safe(original)
        sanitized_safe, sanitized_issues = self.is_safe(sanitized)

        return {
            "original_safe": original_safe,
            "sanitized_safe": sanitized_safe,
            "original_issues": original_issues,
            "sanitized_issues": sanitized_issues,
            "size_reduction": len(original) - len(sanitized),
            "effectiveness": (
                len(original_issues) - len(sanitized_issues) if original_issues else 0
            ),
        }


# 便利な関数エクスポート
def quick_sanitize_html(content: str) -> str:
    """HTMLクイックサニタイズ"""
    sanitizer = DataSanitizer()
    return sanitizer.sanitize_html(content)


def quick_sanitize_url(url: str) -> str:
    """URLクイックサニタイズ"""
    sanitizer = DataSanitizer()
    return sanitizer.sanitize_url(url)


def quick_escape(text: str) -> str:
    """テキストクイックエスケープ"""
    sanitizer = DataSanitizer()
    return sanitizer.escape_html_entities(text)


# パフォーマンステスト用のベンチマーク関数
def benchmark_sanitizer(iterations: int = 10000) -> Dict[str, float]:
    """
    サニタイザーのパフォーマンステスト

    Args:
        iterations: テスト反復回数

    Returns:
        パフォーマンス結果
    """
    import time

    sanitizer = DataSanitizer()
    test_content = "<script>alert('test')</script><p>Safe content</p>"

    start_time = time.time()
    for _ in range(iterations):
        sanitizer.sanitize_html(test_content)
    end_time = time.time()

    total_time = end_time - start_time
    ops_per_sec = iterations / total_time

    return {
        "total_time": total_time,
        "operations_per_second": ops_per_sec,
        "avg_time_per_operation": total_time / iterations,
        "target_achieved": ops_per_sec >= 10000,
    }


if __name__ == "__main__":
    # 基本テスト実行
    print("🛡️ Kumihan-Formatter データサニタイザー")
    print("=" * 50)

    # パフォーマンステスト
    print("📊 パフォーマンステスト実行中...")
    results = benchmark_sanitizer(1000)
    print(f"処理速度: {results['operations_per_second']:.0f} ops/sec")
    print(f"目標達成: {'✅' if results['target_achieved'] else '❌'}")

    # 機能テスト
    sanitizer = DataSanitizer()
    test_html = '<script>alert("xss")</script><p onclick="evil()">Test</p>'
    sanitized = sanitizer.sanitize_html(test_html)
    print(f"\n🧪 機能テスト:")
    print(f"元のHTML: {test_html}")
    print(f"サニタイズ後: {sanitized}")

    # 安全性検証
    checker = SafetyChecker()
    verification = checker.verify_sanitization(test_html, sanitized)
    print(
        f"\n🔍 安全性検証: {'✅ 安全' if verification['sanitized_safe'] else '❌ 危険'}"
    )
