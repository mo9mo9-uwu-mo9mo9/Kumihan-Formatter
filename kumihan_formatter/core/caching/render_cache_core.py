"""
レンダリングキャッシュ - コア機能

メインキャッシュクラスと基本操作
Issue #492 Phase 5A - render_cache.py分割
"""

from pathlib import Path
from typing import Any, Callable, Union

from ..performance import get_global_monitor
from ..utilities.logger import get_logger
from .cache_strategies import AdaptiveStrategy
from .render_cache_metadata import RenderCacheMetadata
from .render_cache_validators import RenderCacheValidators
from .smart_cache import SmartCache


class RenderCacheCore(SmartCache):
    """レンダリング結果専用キャッシュ - コア機能

    責任:
    - SmartCacheの拡張
    - HTML出力のキャッシュ
    - 基本的なCRUD操作
    """

    def __init__(
        self,
        cache_dir: Union[Path, None] = None,
        max_memory_mb: float = 150.0,
        max_entries: int = 500,
        default_ttl: int = 1800,  # 30分
    ):
        """レンダリングキャッシュを初期化

        Args:
            cache_dir: キャッシュディレクトリ
            max_memory_mb: 最大メモリ使用量（MB）
            max_entries: 最大エントリ数
            default_ttl: デフォルト有効期限（秒）
        """
        self.logger = get_logger(__name__)
        self.logger.info(
            f"RenderCacheCore初期化開始: max_memory={max_memory_mb}MB, max_entries={max_entries}, ttl={default_ttl}s"
        )

        super().__init__(
            name="render_cache",
            max_memory_entries=max_entries,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl,
            strategy=AdaptiveStrategy(frequency_weight=0.5, size_weight=0.5),
            cache_dir=cache_dir,
            enable_file_cache=True,
        )

        # 分離されたコンポーネント
        self.metadata = RenderCacheMetadata()
        self.validators = RenderCacheValidators(default_ttl=default_ttl)

        # 設定ハッシュ（設定変更検知用）
        self._config_hash: Union[str, None] = None

        self.logger.debug(f"RenderCacheCore初期化完了: cache_dir={cache_dir}")

    def get_rendered_html(
        self,
        content_hash: str,
        template_name: str,
        render_options: Union[dict[str, Any], None] = None,
    ) -> str | None:
        """レンダリング結果をキャッシュから取得

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            render_options: レンダリングオプション

        Returns:
            キャッシュされたHTML文字列
        """
        self.logger.debug(
            f"レンダリングキャッシュ取得要求: content_hash={content_hash[:8]}..., template={template_name}"
        )

        # キャッシュキーを生成
        cache_key = self.validators.generate_cache_key(
            content_hash, template_name, render_options, self._config_hash
        )

        # キャッシュから取得
        with get_global_monitor().measure("render_cache_lookup"):
            cached_html = self.get(cache_key)

        if cached_html is not None:
            # メタデータを更新
            self.metadata.update_last_accessed(cache_key)
            return cached_html  # type: ignore

        return None

    def cache_rendered_html(
        self,
        content_hash: str,
        template_name: str,
        html_output: str,
        render_options: Union[dict[str, Any], None] = None,
        render_time: float = 0.0,
        node_count: int = 0,
    ) -> None:
        """レンダリング結果をキャッシュに保存

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            html_output: 生成されたHTML
            render_options: レンダリングオプション
            render_time: レンダリング時間
            node_count: 処理されたノード数
        """
        # キャッシュキーを生成
        cache_key = self.validators.generate_cache_key(
            content_hash, template_name, render_options, self._config_hash
        )

        # メタデータを記録
        self.metadata.add_metadata(
            cache_key=cache_key,
            content_hash=content_hash,
            template_name=template_name,
            render_time=render_time,
            node_count=node_count,
            output_size=len(html_output.encode("utf-8")),
        )

        # TTLを動的に調整
        ttl = self.validators.calculate_ttl(len(html_output), render_time, node_count)

        # キャッシュに保存
        with get_global_monitor().measure("render_cache_store"):
            self.set(cache_key, html_output, ttl=ttl)

    def get_render_or_compute(
        self,
        content_hash: str,
        template_name: str,
        render_func: Callable[..., str],
        render_options: Union[dict[str, Any], None] = None,
        **render_kwargs: Any,
    ) -> str:
        """キャッシュから取得または新規レンダリング

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            render_func: レンダリング関数
            render_options: レンダリングオプション
            **render_kwargs: レンダリング関数への追加引数

        Returns:
            レンダリングされたHTML
        """
        # キャッシュから取得を試行
        cached_html = self.get_rendered_html(
            content_hash, template_name, render_options
        )

        if cached_html is not None:
            return cached_html

        # レンダリングを実行
        import time

        start_time = time.perf_counter()

        with get_global_monitor().measure(
            "render_execution",
            node_count=render_kwargs.get("node_count", 0),
        ):
            if render_options:
                html_output = render_func(
                    render_options=render_options, **render_kwargs
                )
            else:
                html_output = render_func(**render_kwargs)

        end_time = time.perf_counter()
        render_time = end_time - start_time

        # 結果をキャッシュに保存
        self.cache_rendered_html(
            content_hash=content_hash,
            template_name=template_name,
            html_output=html_output,
            render_options=render_options,
            render_time=render_time,
            node_count=render_kwargs.get("node_count", 0),
        )

        return html_output

    def invalidate_by_template(self, template_name: str) -> int:
        """テンプレート名による無効化

        Args:
            template_name: 無効化するテンプレート名

        Returns:
            無効化されたエントリ数
        """
        keys_to_invalidate = self.metadata.get_keys_by_template(template_name)
        return self._invalidate_keys(keys_to_invalidate)

    def invalidate_by_content_hash(self, content_hash: str) -> int:
        """コンテンツハッシュによる無効化

        Args:
            content_hash: 無効化するコンテンツハッシュ

        Returns:
            無効化されたエントリ数
        """
        keys_to_invalidate = self.metadata.get_keys_by_content_hash(content_hash)
        return self._invalidate_keys(keys_to_invalidate)

    def invalidate_by_config_change(self, new_config_hash: str) -> int:
        """設定変更による全体無効化

        Args:
            new_config_hash: 新しい設定のハッシュ値

        Returns:
            無効化されたエントリ数
        """
        if self._config_hash == new_config_hash:
            return 0  # 設定変更なし

        # 全キャッシュを無効化
        invalidated_count = len(self.metadata.get_all_metadata())
        self.clear()
        self.metadata.clear()
        self._config_hash = new_config_hash

        return invalidated_count

    def _invalidate_keys(self, keys: list[str]) -> int:
        """指定されたキーを無効化

        Args:
            keys: 無効化するキーのリスト

        Returns:
            無効化されたエントリ数
        """
        invalidated_count = 0

        for key in keys:
            if self.delete(key):
                invalidated_count += 1
            self.metadata.remove_metadata(key)

        return invalidated_count
