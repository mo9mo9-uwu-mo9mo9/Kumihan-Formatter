"""
正規表現エンジン最適化システム
Issue #813対応 - performance_metrics.pyから分離
"""

from typing import Any, Dict, List

from ...utilities.logger import get_logger


class RegexOptimizer:
    """
    正規表現エンジン最適化システム

    特徴:
    - コンパイル済み正規表現の効率的キャッシング
    - 最適化されたパターンマッチング戦略
    - マッチング性能の大幅向上
    - メモリ効率的な正規表現処理
    """

    def __init__(self, cache_size_limit: int = 1000):
        self.logger = get_logger(__name__)
        self.cache_size_limit = cache_size_limit
        self._pattern_cache = {}
        self._usage_counter = {}
        self._compile_stats = {"hits": 0, "misses": 0, "evictions": 0}

        # 最適化された事前コンパイル済みパターン
        self._precompiled_patterns = self._initialize_precompiled_patterns()

        self.logger.info(
            f"RegexOptimizer initialized with cache limit: {cache_size_limit}"
        )

    def _initialize_precompiled_patterns(self) -> Dict[str, Any]:
        """よく使用される正規表現パターンを事前コンパイル"""
        import re

        patterns = {
            # Kumihanマークアップ基本パターン
            "inline_notation": re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##", re.MULTILINE),
            "block_marker": re.compile(r"^#\s*([^#]+?)\s*#([^#]*)##$", re.MULTILINE),
            "nested_markers": re.compile(r"#+([^#]+?)#+", re.MULTILINE),
            # よく使用される文字列処理パターン
            "whitespace_cleanup": re.compile(r"\s+"),
            "line_breaks": re.compile(r"\r?\n"),
            "empty_lines": re.compile(r"^\s*$", re.MULTILINE),
            # 色属性解析
            "color_attribute": re.compile(r"color\s*=\s*([#\w]+)"),
            "hex_color": re.compile(r"^#[0-9a-fA-F]{3,6}$"),
            # HTMLエスケープ
            "html_chars": re.compile(r"[<>&\"']"),
            # 特殊文字処理
            "japanese_chars": re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"),
        }

        self.logger.info(f"Pre-compiled {len(patterns)} regex patterns")
        return patterns

    def get_compiled_pattern(self, pattern_str: str, flags: int = 0) -> Any:
        """
        コンパイル済み正規表現を取得（キャッシュ機能付き）

        Args:
            pattern_str: 正規表現パターン文字列
            flags: 正規表現フラグ

        Returns:
            Pattern: コンパイル済み正規表現オブジェクト
        """
        import re

        cache_key = (pattern_str, flags)

        # キャッシュヒットチェック
        if cache_key in self._pattern_cache:
            self._compile_stats["hits"] += 1
            self._usage_counter[cache_key] = self._usage_counter.get(cache_key, 0) + 1
            return self._pattern_cache[cache_key]

        # キャッシュミス：新規コンパイル
        self._compile_stats["misses"] += 1

        try:
            compiled_pattern = re.compile(pattern_str, flags)

            # キャッシュサイズ制限チェック
            if len(self._pattern_cache) >= self.cache_size_limit:
                self._evict_least_used_pattern()

            # キャッシュに保存
            self._pattern_cache[cache_key] = compiled_pattern
            self._usage_counter[cache_key] = 1

            return compiled_pattern

        except re.error as e:
            self.logger.error(
                f"Regex compilation failed for pattern '{pattern_str}': {e}"
            )
            # フォールバック：文字列マッチング
            return None

    def _evict_least_used_pattern(self):
        """最も使用頻度の低いパターンをキャッシュから削除"""
        if not self._usage_counter:
            return

        # 最小使用回数のパターンを見つける
        least_used_key = min(self._usage_counter, key=self._usage_counter.get)

        # キャッシュから削除
        if least_used_key in self._pattern_cache:
            del self._pattern_cache[least_used_key]
        if least_used_key in self._usage_counter:
            del self._usage_counter[least_used_key]

        self._compile_stats["evictions"] += 1
        self.logger.debug(
            f"Evicted regex pattern from cache: {least_used_key[0][:50]}..."
        )

    def optimized_search(self, pattern_str: str, text: str, flags: int = 0) -> Any:
        """
        最適化された正規表現検索

        Args:
            pattern_str: 検索パターン
            text: 検索対象テキスト
            flags: 正規表現フラグ

        Returns:
            Match object or None
        """
        # 事前コンパイル済みパターンをチェック
        for name, precompiled in self._precompiled_patterns.items():
            if precompiled.pattern == pattern_str:
                return precompiled.search(text)

        # キャッシュからコンパイル済みパターンを取得
        compiled_pattern = self.get_compiled_pattern(pattern_str, flags)
        if compiled_pattern:
            return compiled_pattern.search(text)

        # フォールバック：単純文字列検索
        return pattern_str in text

    def optimized_findall(
        self, pattern_str: str, text: str, flags: int = 0
    ) -> List[str]:
        """
        最適化された正規表現全体検索

        Args:
            pattern_str: 検索パターン
            text: 検索対象テキスト
            flags: 正規表現フラグ

        Returns:
            List[str]: マッチした文字列のリスト
        """
        compiled_pattern = self.get_compiled_pattern(pattern_str, flags)
        if compiled_pattern:
            return compiled_pattern.findall(text)
        return []

    def optimized_substitute(
        self, pattern_str: str, replacement: str, text: str, flags: int = 0
    ) -> str:
        """
        最適化された正規表現置換

        Args:
            pattern_str: 置換パターン
            replacement: 置換文字列
            text: 対象テキスト
            flags: 正規表現フラグ

        Returns:
            str: 置換後テキスト
        """
        compiled_pattern = self.get_compiled_pattern(pattern_str, flags)
        if compiled_pattern:
            return compiled_pattern.sub(replacement, text)

        # フォールバック：単純文字列置換
        return text.replace(pattern_str, replacement)

    def batch_process_with_patterns(
        self, texts: List[str], patterns_and_replacements: List[tuple[str, str]]
    ) -> List[str]:
        """
        複数テキストに対する一括正規表現処理

        Args:
            texts: 処理対象テキストリスト
            patterns_and_replacements: (pattern, replacement)のタプルリスト

        Returns:
            List[str]: 処理済みテキストリスト
        """
        results = []

        # パターンを事前コンパイル
        compiled_patterns = []
        for pattern, replacement in patterns_and_replacements:
            compiled = self.get_compiled_pattern(pattern)
            if compiled:
                compiled_patterns.append((compiled, replacement))

        # 各テキストを処理
        for text in texts:
            processed_text = text
            for compiled_pattern, replacement in compiled_patterns:
                processed_text = compiled_pattern.sub(replacement, processed_text)
            results.append(processed_text)

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_requests = self._compile_stats["hits"] + self._compile_stats["misses"]
        hit_rate = (
            (self._compile_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "cache_size": len(self._pattern_cache),
            "cache_limit": self.cache_size_limit,
            "hit_rate_percent": hit_rate,
            "total_hits": self._compile_stats["hits"],
            "total_misses": self._compile_stats["misses"],
            "total_evictions": self._compile_stats["evictions"],
            "precompiled_patterns": len(self._precompiled_patterns),
        }

    def clear_cache(self):
        """キャッシュをクリア"""
        cleared_count = len(self._pattern_cache)
        self._pattern_cache.clear()
        self._usage_counter.clear()
        self._compile_stats = {"hits": 0, "misses": 0, "evictions": 0}

        self.logger.info(f"Regex cache cleared: {cleared_count} patterns removed")
