"""
レンダリングキャッシュ - バリデーター・ユーティリティ

TTL計算・キー生成・バリデーション
Issue #492 Phase 5A - render_cache.py分割
"""

import hashlib
import json
from typing import Any, Union


class RenderCacheValidators:
    """レンダリングキャッシュのバリデーター・ユーティリティ

    責任:
    - キャッシュキーの生成
    - TTL（有効期限）の動的計算
    - レンダリング関連のバリデーション
    """

    def __init__(self, default_ttl: int = 1800):
        """バリデーターを初期化

        Args:
            default_ttl: デフォルトTTL（秒）
        """
        self.default_ttl = default_ttl

    def generate_cache_key(
        self,
        content_hash: str,
        template_name: str,
        render_options: Union[dict[str, Any], None] = None,
        config_hash: Union[str, None] = None,
    ) -> str:
        """レンダリング用キャッシュキーを生成

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            render_options: レンダリングオプション
            config_hash: 設定のハッシュ値

        Returns:
            生成されたキャッシュキー
        """
        key_parts = [
            content_hash,
            template_name,
        ]

        # オプションハッシュ
        if render_options:
            options_str = json.dumps(render_options, sort_keys=True)
            options_hash = hashlib.md5(options_str.encode("utf-8")).hexdigest()[:8]
            key_parts.append(options_hash)

        # 設定ハッシュ
        if config_hash:
            key_parts.append(config_hash[:8])

        return "render_" + "_".join(key_parts)

    def calculate_ttl(
        self,
        output_size: int,
        render_time: float,
        node_count: int,
    ) -> int:
        """レンダリング結果に応じたTTLを計算

        Args:
            output_size: 出力サイズ（バイト）
            render_time: レンダリング時間（秒）
            node_count: 処理されたノード数

        Returns:
            動的に調整されたTTL（秒）
        """
        base_ttl = self.default_ttl

        # 大きな出力ほど長いTTL
        if output_size > 100000:  # 100KB以上
            base_ttl *= 2
        elif output_size > 10000:  # 10KB以上
            base_ttl *= 1.5  # type: ignore

        # レンダリング時間が長いほど長いTTL
        if render_time > 2.0:  # 2秒以上
            base_ttl *= 3
        elif render_time > 0.5:  # 0.5秒以上
            base_ttl *= 2

        # ノード数が多いほど長いTTL
        if node_count > 500:
            base_ttl *= 1.5  # type: ignore

        return int(base_ttl)

    def validate_cache_key(self, cache_key: str) -> bool:
        """キャッシュキーの形式を検証

        Args:
            cache_key: 検証するキャッシュキー

        Returns:
            キーが有効な形式かどうか
        """
        if not cache_key:
            return False

        if not cache_key.startswith("render_"):
            return False

        # 最低限の構成要素をチェック
        parts = cache_key.replace("render_", "").split("_")
        return len(parts) >= 2  # content_hash + template_name

    def validate_render_options(self, render_options: Any) -> bool:
        """レンダリングオプションの形式を検証

        Args:
            render_options: 検証するレンダリングオプション

        Returns:
            オプションが有効な形式かどうか
        """
        if render_options is None:
            return True

        if not isinstance(render_options, dict):
            return False

        # 辞書の値がJSONシリアライズ可能かチェック
        try:
            json.dumps(render_options, sort_keys=True)
            return True
        except (TypeError, ValueError):
            return False

    def estimate_cache_efficiency(
        self,
        output_size: int,
        render_time: float,
        hit_rate: float = 0.0,
    ) -> dict[str, Any]:
        """キャッシュ効率の推定

        Args:
            output_size: 出力サイズ（バイト）
            render_time: レンダリング時間（秒）
            hit_rate: キャッシュヒット率

        Returns:
            キャッシュ効率の推定値
        """
        # メモリコスト（KB単位）
        memory_cost = output_size / 1024

        # 時間節約効果
        time_saved_per_hit = render_time

        # 効率スコア（時間節約 / メモリコスト）
        efficiency_score = 0.0
        if memory_cost > 0:
            efficiency_score = (time_saved_per_hit * hit_rate) / memory_cost

        return {
            "memory_cost_kb": memory_cost,
            "time_saved_per_hit": time_saved_per_hit,
            "efficiency_score": efficiency_score,
            "recommended_ttl": self.calculate_ttl(output_size, render_time, 0),
            "cache_worthy": efficiency_score > 0.1,  # 閾値
        }
