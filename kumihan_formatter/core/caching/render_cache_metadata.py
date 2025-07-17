"""
レンダリングキャッシュ - メタデータ管理

レンダリングメタデータの保存・取得・管理
Issue #492 Phase 5A - render_cache.py分割
"""

from datetime import datetime
from typing import Any, Dict, Union


class RenderCacheMetadata:
    """レンダリングキャッシュのメタデータ管理

    責任:
    - レンダリングメタデータの保存・取得
    - テンプレート・コンテンツハッシュ別の検索
    - アクセス時刻の更新
    """

    def __init__(self) -> None:
        """メタデータマネージャーを初期化"""
        self._render_metadata: dict[str, dict[str, Any]] = {}

    def add_metadata(
        self,
        cache_key: str,
        content_hash: str,
        template_name: str,
        render_time: float,
        node_count: int,
        output_size: int,
    ) -> None:
        """新しいレンダリングメタデータを追加

        Args:
            cache_key: キャッシュキー
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            render_time: レンダリング時間
            node_count: 処理されたノード数
            output_size: 出力サイズ（バイト）
        """
        now = datetime.now().isoformat()

        self._render_metadata[cache_key] = {
            "content_hash": content_hash,
            "template_name": template_name,
            "render_time": render_time,
            "node_count": node_count,
            "output_size": output_size,
            "cached_at": now,
            "last_accessed": now,
        }

    def update_last_accessed(self, cache_key: str) -> None:
        """最終アクセス時刻を更新

        Args:
            cache_key: 更新するキャッシュキー
        """
        if cache_key in self._render_metadata:
            self._render_metadata[cache_key][
                "last_accessed"
            ] = datetime.now().isoformat()

    def get_metadata(self, cache_key: str) -> Union[dict[str, Any], None]:
        """指定されたキーのメタデータを取得

        Args:
            cache_key: 取得するキャッシュキー

        Returns:
            メタデータ辞書。存在しない場合はNone
        """
        return self._render_metadata.get(cache_key)

    def get_all_metadata(self) -> dict[str, dict[str, Any]]:
        """全メタデータを取得

        Returns:
            全メタデータ辞書
        """
        return self._render_metadata.copy()

    def get_keys_by_template(self, template_name: str) -> list[str]:
        """テンプレート名で該当するキーを取得

        Args:
            template_name: 検索するテンプレート名

        Returns:
            該当するキーのリスト
        """
        return [
            key
            for key, metadata in self._render_metadata.items()
            if metadata.get("template_name") == template_name
        ]

    def get_keys_by_content_hash(self, content_hash: str) -> list[str]:
        """コンテンツハッシュで該当するキーを取得

        Args:
            content_hash: 検索するコンテンツハッシュ

        Returns:
            該当するキーのリスト
        """
        return [
            key
            for key, metadata in self._render_metadata.items()
            if metadata.get("content_hash") == content_hash
        ]

    def get_by_template(self, template_name: str) -> dict[str, dict[str, Any]]:
        """テンプレート名で該当するメタデータを取得

        Args:
            template_name: 検索するテンプレート名

        Returns:
            該当するメタデータ辞書
        """
        return {
            key: metadata
            for key, metadata in self._render_metadata.items()
            if metadata.get("template_name") == template_name
        }

    def remove_metadata(self, cache_key: str) -> bool:
        """指定されたキーのメタデータを削除

        Args:
            cache_key: 削除するキャッシュキー

        Returns:
            削除が成功したかどうか
        """
        if cache_key in self._render_metadata:
            del self._render_metadata[cache_key]
            return True
        return False

    def clear(self) -> None:
        """全メタデータをクリア"""
        self._render_metadata.clear()

    def get_template_stats(self) -> dict[str, int]:
        """テンプレート別の統計情報を取得

        Returns:
            テンプレート名をキーとした使用回数の辞書
        """
        template_stats: Dict[str, int] = {}
        for metadata in self._render_metadata.values():
            template_name = metadata.get("template_name", "unknown")
            template_stats[template_name] = template_stats.get(template_name, 0) + 1
        return template_stats

    def get_render_times(self) -> list[float]:
        """全エントリのレンダリング時間を取得

        Returns:
            レンダリング時間のリスト
        """
        return [
            metadata["render_time"]
            for metadata in self._render_metadata.values()
            if "render_time" in metadata
        ]

    def get_output_sizes(self) -> list[int]:
        """全エントリの出力サイズを取得

        Returns:
            出力サイズのリスト
        """
        return [
            metadata["output_size"]
            for metadata in self._render_metadata.values()
            if "output_size" in metadata
        ]

    def get_template_usage_stats(self) -> dict[str, dict[str, Any]]:
        """テンプレート使用パターンの詳細統計

        Returns:
            テンプレート別の詳細統計情報
        """
        template_stats: Dict[str, Dict[str, Any]] = {}

        for metadata in self._render_metadata.values():
            template_name = metadata.get("template_name", "unknown")
            if template_name not in template_stats:
                template_stats[template_name] = {
                    "count": 0,
                    "total_render_time": 0,
                    "sizes": [],
                }

            stats = template_stats[template_name]
            stats["count"] += 1
            stats["total_render_time"] += metadata.get("render_time", 0)

            output_size = metadata.get("output_size", 0)
            stats["sizes"].append(output_size)

        # 平均値を計算
        for template_name, stats in template_stats.items():
            if stats["count"] > 0:
                stats["avg_render_time"] = stats["total_render_time"] / stats["count"]
                stats["avg_output_size"] = sum(stats["sizes"]) / len(stats["sizes"])
            del stats["sizes"]  # 不要なデータを削除

        return template_stats
