#!/usr/bin/env python3
"""
AST Performance Optimizer - Issue #643 Medium Priority Issue対応
ASTパース負荷軽減とメモリリーク対策システム

目的: 全ファイルのAST解析時の高い計算負荷とメモリリークを解決
- ASTパース結果のキャッシュ
- メモリ効率的なパーシング
- ガベージコレクション最適化
- 段階的パーシング戦略
"""

import ast
import concurrent.futures
import gc
import hashlib
import json
import multiprocessing
import pickle
import threading
import time
import weakref
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Union

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class ParseStrategy(Enum):
    """パーシング戦略"""

    FULL = "full"  # 完全解析
    MINIMAL = "minimal"  # 最小限解析
    SELECTIVE = "selective"  # 選択的解析
    INCREMENTAL = "incremental"  # 段階的解析


class CacheLevel(Enum):
    """キャッシュレベル"""

    MEMORY = "memory"  # メモリキャッシュ
    DISK = "disk"  # ディスクキャッシュ
    HYBRID = "hybrid"  # ハイブリッド


@dataclass
class ASTCacheEntry:
    """ASTキャッシュエントリ"""

    file_path: Path
    content_hash: str
    parsed_ast: Optional[ast.AST]
    parse_time: float
    memory_usage: int
    access_count: int
    last_accessed: datetime
    created_at: datetime
    strategy_used: ParseStrategy


@dataclass
class ParseMetrics:
    """パーシングメトリクス"""

    total_files: int
    cached_hits: int
    cache_misses: int
    total_parse_time: float
    peak_memory_usage: int
    gc_collections: int
    memory_leaks: List[str]


class ASTPerformanceOptimizer:
    """ASTパフォーマンス最適化システム"""

    def __init__(self, config_path: Optional[Path] = None):
        """初期化"""
        self.config_path = (
            config_path
            or Path(__file__).parent.parent.parent.parent
            / "config"
            / "ast_optimization.json"
        )
        self.config = self._load_config()

        # キャッシュ設定
        self.cache_level = CacheLevel(self.config.get("cache_level", "hybrid"))
        self.max_memory_cache_size = self.config.get(
            "max_memory_cache_size", 100
        )  # エントリ数
        self.max_memory_usage_mb = self.config.get("max_memory_usage_mb", 200)
        self.cache_ttl_hours = self.config.get("cache_ttl_hours", 24)

        # メモリキャッシュ
        self._memory_cache: Dict[str, ASTCacheEntry] = {}
        self._cache_lock = threading.RLock()

        # ディスクキャッシュ
        self.disk_cache_dir = Path(
            self.config.get("disk_cache_dir", "/tmp/kumihan_ast_cache")
        )
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

        # パフォーマンス追跡
        self.metrics = ParseMetrics(
            total_files=0,
            cached_hits=0,
            cache_misses=0,
            total_parse_time=0.0,
            peak_memory_usage=0,
            gc_collections=0,
            memory_leaks=[],
        )

        # 弱参照によるメモリリーク検出
        self._ast_references: Set[weakref.ref] = set()

        # GCチューニング
        self._configure_garbage_collection()

        # クリーンアップスレッド
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup, daemon=True, name="ASTCacheCleanup"
        )
        self._cleanup_thread.start()

        logger.info("ASTパフォーマンス最適化システム初期化完了")

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"AST最適化設定読み込み失敗: {e}")

        # デフォルト設定
        return {
            "cache_level": "hybrid",
            "max_memory_cache_size": 100,
            "max_memory_usage_mb": 200,
            "cache_ttl_hours": 24,
            "disk_cache_dir": "/tmp/kumihan_ast_cache",
            "parse_strategies": {
                "small_files": "full",  # < 1KB
                "medium_files": "selective",  # 1KB - 100KB
                "large_files": "minimal",  # > 100KB
                "huge_files": "incremental",  # > 1MB
            },
            "memory_optimization": {
                "enable_gc_tuning": true,
                "gc_threshold0": 700,
                "gc_threshold1": 10,
                "gc_threshold2": 10,
                "force_gc_interval": 50,
                "max_ast_nodes": 10000,
            },
            "selective_parsing": {
                "parse_function_defs": true,
                "parse_class_defs": true,
                "parse_imports": true,
                "parse_strings": false,
                "parse_comments": false,
                "skip_docstrings": true,
            },
        }

    def _configure_garbage_collection(self):
        """ガベージコレクション設定"""
        gc_config = self.config.get("memory_optimization", {})

        if gc_config.get("enable_gc_tuning", True):
            # GC閾値調整（メモリ効率重視）
            gc.set_threshold(
                gc_config.get("gc_threshold0", 700),
                gc_config.get("gc_threshold1", 10),
                gc_config.get("gc_threshold2", 10),
            )
            logger.debug(f"GC閾値調整: {gc.get_threshold()}")

    def _get_file_hash(self, file_path: Path, content: Optional[str] = None) -> str:
        """ファイルハッシュ計算"""
        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                return ""

        # ファイルサイズとmodtime、内容ハッシュの組み合わせ
        stat = file_path.stat()
        hash_input = f"{file_path}_{stat.st_size}_{stat.st_mtime}_{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _determine_parse_strategy(self, file_path: Path, content: str) -> ParseStrategy:
        """ファイルサイズに基づくパーシング戦略決定"""
        file_size = len(content.encode("utf-8"))
        strategies = self.config.get("parse_strategies", {})

        if file_size < 1024:  # 1KB未満
            return ParseStrategy(strategies.get("small_files", "full"))
        elif file_size < 102400:  # 100KB未満
            return ParseStrategy(strategies.get("medium_files", "selective"))
        elif file_size < 1048576:  # 1MB未満
            return ParseStrategy(strategies.get("large_files", "minimal"))
        else:  # 1MB以上
            return ParseStrategy(strategies.get("huge_files", "incremental"))

    def _parse_with_strategy(
        self, content: str, strategy: ParseStrategy, file_path: Path
    ) -> Optional[ast.AST]:
        """戦略に応じたパーシング実行"""

        try:
            if strategy == ParseStrategy.FULL:
                return ast.parse(content)

            elif strategy == ParseStrategy.MINIMAL:
                # 構文チェックのみ（ASTは最小限）
                try:
                    tree = ast.parse(content)
                    # ノード数制限
                    max_nodes = self.config.get("memory_optimization", {}).get(
                        "max_ast_nodes", 10000
                    )
                    if self._count_ast_nodes(tree) > max_nodes:
                        logger.warning(f"AST節点数が上限を超過: {file_path}")
                        return None
                    return tree
                except SyntaxError:
                    return None

            elif strategy == ParseStrategy.SELECTIVE:
                # 選択的パーシング
                return self._selective_parse(content)

            elif strategy == ParseStrategy.INCREMENTAL:
                # 段階的パーシング
                return self._incremental_parse(content)

        except Exception as e:
            logger.debug(f"パーシングエラー ({strategy.value}): {file_path} - {e}")
            return None

        return None

    def _selective_parse(self, content: str) -> Optional[ast.AST]:
        """選択的パーシング実行"""
        selective_config = self.config.get("selective_parsing", {})

        try:
            # 完全パーシングを実行
            tree = ast.parse(content)

            # 必要な部分のみ保持
            filtered_tree = ast.Module(body=[], type_ignores=[])

            for node in tree.body:
                include_node = False

                if isinstance(node, ast.FunctionDef) and selective_config.get(
                    "parse_function_defs", True
                ):
                    include_node = True
                elif isinstance(node, ast.ClassDef) and selective_config.get(
                    "parse_class_defs", True
                ):
                    include_node = True
                elif isinstance(
                    node, (ast.Import, ast.ImportFrom)
                ) and selective_config.get("parse_imports", True):
                    include_node = True

                if include_node:
                    # docstringスキップ設定
                    if selective_config.get("skip_docstrings", True):
                        node = self._remove_docstrings(node)
                    filtered_tree.body.append(node)

            return filtered_tree

        except Exception as e:
            logger.debug(f"選択的パーシングエラー: {e}")
            return None

    def _incremental_parse(self, content: str) -> Optional[ast.AST]:
        """段階的パーシング実行"""
        # 大きなファイルを分割してパーシング
        lines = content.split("\n")
        chunk_size = 1000  # 1000行ずつ

        parsed_chunks = []

        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i : i + chunk_size]
            chunk_content = "\n".join(chunk_lines)

            try:
                # 構文的に完全なチャンクかチェック
                chunk_tree = ast.parse(chunk_content)
                parsed_chunks.append(chunk_tree)
            except SyntaxError:
                # 不完全なチャンクは簡易解析のみ
                logger.debug(f"チャンク {i}-{i+chunk_size} は不完全、スキップ")
                continue

        if not parsed_chunks:
            return None

        # 最初のチャンクのみ返す（メモリ効率重視）
        return parsed_chunks[0]

    def _remove_docstrings(self, node: ast.AST) -> ast.AST:
        """docstring除去"""
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                # docstringを削除
                node.body = node.body[1:]
        return node

    def _count_ast_nodes(self, tree: ast.AST) -> int:
        """AST節点数カウント"""
        count = 1
        for child in ast.iter_child_nodes(tree):
            count += self._count_ast_nodes(child)
        return count

    def parse_file_optimized(
        self,
        file_path: Union[str, Path],
        content: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Optional[ast.AST]:
        """最適化されたファイルパーシング"""

        file_path = Path(file_path)
        start_time = time.time()

        # メトリクス更新
        self.metrics.total_files += 1

        try:
            # コンテンツ読み込み
            if content is None:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            # ファイルハッシュ計算
            content_hash = self._get_file_hash(file_path, content)
            cache_key = f"{file_path}_{content_hash}"

            # キャッシュチェック
            if not force_refresh:
                cached_ast = self._get_cached_ast(cache_key)
                if cached_ast is not None:
                    self.metrics.cached_hits += 1
                    return cached_ast

            # キャッシュミス
            self.metrics.cache_misses += 1

            # パーシング戦略決定
            strategy = self._determine_parse_strategy(file_path, content)

            # メモリ使用量監視
            import psutil

            process = psutil.Process()
            memory_before = process.memory_info().rss

            # パーシング実行
            parsed_ast = self._parse_with_strategy(content, strategy, file_path)

            # メモリ使用量記録
            memory_after = process.memory_info().rss
            memory_used = memory_after - memory_before

            if memory_after > self.metrics.peak_memory_usage:
                self.metrics.peak_memory_usage = memory_after

            # パーシング時間記録
            parse_time = time.time() - start_time
            self.metrics.total_parse_time += parse_time

            # キャッシュ保存
            if parsed_ast is not None:
                self._cache_ast(
                    cache_key,
                    file_path,
                    content_hash,
                    parsed_ast,
                    parse_time,
                    memory_used,
                    strategy,
                )

                # 弱参照でメモリリーク監視
                self._track_ast_reference(parsed_ast)

            # 定期的なGC実行
            if (
                self.metrics.total_files
                % self.config.get("memory_optimization", {}).get(
                    "force_gc_interval", 50
                )
                == 0
            ):
                self._force_garbage_collection()

            return parsed_ast

        except Exception as e:
            logger.error(f"最適化パーシングエラー: {file_path} - {e}")
            return None

    def _get_cached_ast(self, cache_key: str) -> Optional[ast.AST]:
        """キャッシュからAST取得"""

        with self._cache_lock:
            # メモリキャッシュチェック
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]

                # TTLチェック
                if datetime.now() - entry.created_at < timedelta(
                    hours=self.cache_ttl_hours
                ):
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    return entry.parsed_ast
                else:
                    # 期限切れ削除
                    del self._memory_cache[cache_key]

            # ディスクキャッシュチェック
            if self.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                return self._load_from_disk_cache(cache_key)

        return None

    def _cache_ast(
        self,
        cache_key: str,
        file_path: Path,
        content_hash: str,
        ast_tree: ast.AST,
        parse_time: float,
        memory_usage: int,
        strategy: ParseStrategy,
    ):
        """ASTをキャッシュ"""

        with self._cache_lock:
            # メモリキャッシュサイズ制限
            if len(self._memory_cache) >= self.max_memory_cache_size:
                self._evict_lru_cache_entry()

            # メモリキャッシュ保存
            entry = ASTCacheEntry(
                file_path=file_path,
                content_hash=content_hash,
                parsed_ast=ast_tree,
                parse_time=parse_time,
                memory_usage=memory_usage,
                access_count=1,
                last_accessed=datetime.now(),
                created_at=datetime.now(),
                strategy_used=strategy,
            )

            self._memory_cache[cache_key] = entry

            # ディスクキャッシュ保存
            if self.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                self._save_to_disk_cache(cache_key, entry)

    def _evict_lru_cache_entry(self):
        """LRU方式でキャッシュエントリを削除"""
        if not self._memory_cache:
            return

        # 最も古いアクセスのエントリを削除
        lru_key = min(
            self._memory_cache.keys(), key=lambda k: self._memory_cache[k].last_accessed
        )
        del self._memory_cache[lru_key]

    def _save_to_disk_cache(self, cache_key: str, entry: ASTCacheEntry):
        """ディスクキャッシュに保存"""
        try:
            cache_file = self.disk_cache_dir / f"{cache_key}.pkl"

            # ASTを除外した軽量版を保存（メモリ効率重視）
            light_entry = ASTCacheEntry(
                file_path=entry.file_path,
                content_hash=entry.content_hash,
                parsed_ast=None,  # 大きなASTはディスクに保存しない
                parse_time=entry.parse_time,
                memory_usage=entry.memory_usage,
                access_count=entry.access_count,
                last_accessed=entry.last_accessed,
                created_at=entry.created_at,
                strategy_used=entry.strategy_used,
            )

            with open(cache_file, "wb") as f:
                pickle.dump(light_entry, f)

        except Exception as e:
            logger.debug(f"ディスクキャッシュ保存エラー: {e}")

    def _load_from_disk_cache(self, cache_key: str) -> Optional[ast.AST]:
        """ディスクキャッシュから読み込み"""
        try:
            cache_file = self.disk_cache_dir / f"{cache_key}.pkl"

            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    entry = pickle.load(f)

                # TTLチェック
                if datetime.now() - entry.created_at < timedelta(
                    hours=self.cache_ttl_hours
                ):
                    # メタデータのみ（ASTは再パースが必要）
                    return None
                else:
                    # 期限切れファイル削除
                    cache_file.unlink()

        except Exception as e:
            logger.debug(f"ディスクキャッシュ読み込みエラー: {e}")

        return None

    def _track_ast_reference(self, ast_tree: ast.AST):
        """AST参照の追跡（メモリリーク検出用）"""

        def cleanup_callback(ref):
            self._ast_references.discard(ref)

        ref = weakref.ref(ast_tree, cleanup_callback)
        self._ast_references.add(ref)

    def _force_garbage_collection(self):
        """強制ガベージコレクション"""
        collected = gc.collect()
        self.metrics.gc_collections += 1

        if collected > 0:
            logger.debug(f"GC実行: {collected}オブジェクト回収")

        # メモリリーク検出
        alive_refs = len([ref for ref in self._ast_references if ref() is not None])
        if alive_refs > 100:  # 閾値
            logger.warning(f"潜在的メモリリーク検出: {alive_refs}個のAST参照が残存")
            self.metrics.memory_leaks.append(
                f"AST references: {alive_refs} at {datetime.now()}"
            )

    def _periodic_cleanup(self):
        """定期的なクリーンアップ"""
        while True:
            try:
                time.sleep(300)  # 5分間隔

                with self._cache_lock:
                    # 期限切れキャッシュエントリ削除
                    expired_keys = []
                    for key, entry in self._memory_cache.items():
                        if datetime.now() - entry.created_at > timedelta(
                            hours=self.cache_ttl_hours
                        ):
                            expired_keys.append(key)

                    for key in expired_keys:
                        del self._memory_cache[key]

                    if expired_keys:
                        logger.debug(
                            f"期限切れキャッシュ削除: {len(expired_keys)}エントリ"
                        )

                # ディスクキャッシュクリーンアップ
                self._cleanup_disk_cache()

                # 強制GC
                self._force_garbage_collection()

            except Exception as e:
                logger.error(f"定期クリーンアップエラー: {e}")

    def _cleanup_disk_cache(self):
        """ディスクキャッシュクリーンアップ"""
        try:
            current_time = datetime.now()
            cleaned_files = 0

            for cache_file in self.disk_cache_dir.glob("*.pkl"):
                try:
                    # ファイル更新時刻チェック
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if current_time - file_time > timedelta(hours=self.cache_ttl_hours):
                        cache_file.unlink()
                        cleaned_files += 1
                except Exception:
                    continue

            if cleaned_files > 0:
                logger.debug(
                    f"ディスクキャッシュクリーンアップ: {cleaned_files}ファイル削除"
                )

        except Exception as e:
            logger.debug(f"ディスクキャッシュクリーンアップエラー: {e}")

    def parse_files_parallel(
        self, file_paths: List[Union[str, Path]], max_workers: Optional[int] = None
    ) -> Dict[Path, Optional[ast.AST]]:
        """複数ファイルの並列パーシング"""

        parallel_config = self.config.get("parallel_processing", {})

        if not parallel_config.get("enable_parallel_parsing", True):
            # 並列処理無効時は順次処理
            results = {}
            for file_path in file_paths:
                results[Path(file_path)] = self.parse_file_optimized(file_path)
            return results

        # ワーカー数決定
        if max_workers is None:
            max_workers_config = parallel_config.get("max_workers", "auto")
            if max_workers_config == "auto":
                max_workers = min(multiprocessing.cpu_count(), len(file_paths), 8)
            else:
                max_workers = int(max_workers_config)

        # ワーカープール種別決定
        pool_type = parallel_config.get("worker_pool_type", "thread")
        timeout_per_file = parallel_config.get("timeout_per_file", 30)

        results = {}

        # ThreadPoolExecutor使用（I/Oバウンドなタスクのため）
        if pool_type == "thread":
            executor_class = ThreadPoolExecutor
        else:
            executor_class = ProcessPoolExecutor

        try:
            with executor_class(max_workers=max_workers) as executor:
                # ファイルパスをチャンクに分割
                chunk_size = parallel_config.get("chunk_size", 10)
                file_chunks = [
                    file_paths[i : i + chunk_size]
                    for i in range(0, len(file_paths), chunk_size)
                ]

                # 並列タスク実行
                future_to_files = {}
                for chunk in file_chunks:
                    for file_path in chunk:
                        future = executor.submit(self._parse_file_safe, file_path)
                        future_to_files[future] = Path(file_path)

                # 結果収集
                for future in as_completed(
                    future_to_files, timeout=timeout_per_file * len(file_paths)
                ):
                    file_path = future_to_files[future]
                    try:
                        results[file_path] = future.result()
                    except Exception as e:
                        logger.warning(f"並列パーシング失敗: {file_path} - {e}")
                        results[file_path] = None

        except Exception as e:
            logger.error(f"並列パーシングエラー: {e}")
            # フォールバック: 順次処理
            for file_path in file_paths:
                if Path(file_path) not in results:
                    results[Path(file_path)] = self.parse_file_optimized(file_path)

        return results

    def _parse_file_safe(self, file_path: Union[str, Path]) -> Optional[ast.AST]:
        """並列処理用の安全なファイルパーシング"""
        try:
            return self.parse_file_optimized(file_path)
        except Exception as e:
            logger.debug(f"安全パーシング失敗: {file_path} - {e}")
            return None

    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        with self._cache_lock:
            cache_hit_rate = (
                self.metrics.cached_hits / max(1, self.metrics.total_files) * 100
            )

            return {
                "total_files_parsed": self.metrics.total_files,
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "total_parse_time": f"{self.metrics.total_parse_time:.2f}s",
                "average_parse_time": f"{self.metrics.total_parse_time / max(1, self.metrics.total_files):.3f}s",
                "peak_memory_usage_mb": f"{self.metrics.peak_memory_usage / 1024 / 1024:.1f}MB",
                "gc_collections": self.metrics.gc_collections,
                "memory_cache_size": len(self._memory_cache),
                "active_ast_references": len(
                    [ref for ref in self._ast_references if ref() is not None]
                ),
                "memory_leaks_detected": len(self.metrics.memory_leaks),
                "disk_cache_files": (
                    len(list(self.disk_cache_dir.glob("*.pkl")))
                    if self.disk_cache_dir.exists()
                    else 0
                ),
            }

    def clear_cache(self, cache_type: str = "all"):
        """キャッシュクリア"""
        with self._cache_lock:
            if cache_type in ["all", "memory"]:
                cleared_memory = len(self._memory_cache)
                self._memory_cache.clear()
                logger.info(f"メモリキャッシュクリア: {cleared_memory}エントリ")

            if cache_type in ["all", "disk"]:
                cleared_disk = 0
                try:
                    for cache_file in self.disk_cache_dir.glob("*.pkl"):
                        cache_file.unlink()
                        cleared_disk += 1
                    logger.info(f"ディスクキャッシュクリア: {cleared_disk}ファイル")
                except Exception as e:
                    logger.error(f"ディスクキャッシュクリアエラー: {e}")

        # 強制GC
        self._force_garbage_collection()


# グローバルインスタンス
_global_ast_optimizer: Optional[ASTPerformanceOptimizer] = None


def get_ast_optimizer() -> ASTPerformanceOptimizer:
    """グローバルAST最適化システム取得"""
    global _global_ast_optimizer
    if _global_ast_optimizer is None:
        _global_ast_optimizer = ASTPerformanceOptimizer()
    return _global_ast_optimizer


# 便利な関数群
def parse_file_fast(
    file_path: Union[str, Path],
    content: Optional[str] = None,
    force_refresh: bool = False,
) -> Optional[ast.AST]:
    """高速ファイルパーシング（関数版）"""
    return get_ast_optimizer().parse_file_optimized(file_path, content, force_refresh)


def get_parse_metrics() -> Dict[str, Any]:
    """パーシングメトリクス取得（関数版）"""
    return get_ast_optimizer().get_performance_metrics()


def clear_ast_cache(cache_type: str = "all"):
    """ASTキャッシュクリア（関数版）"""
    get_ast_optimizer().clear_cache(cache_type)
