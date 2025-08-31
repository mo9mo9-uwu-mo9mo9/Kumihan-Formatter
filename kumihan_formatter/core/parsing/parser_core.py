"""Parser Core - パーサーコア専用モジュール

parser.py分割により抽出 (Phase3最適化)
メインParserクラスの実装
"""

import threading
import time
from typing import Any, Dict, List, Optional

from ..ast_nodes import Node, error_node
import logging


# 統合最適化後：削除されたモジュールからの局所定義
class ParallelProcessingError(Exception):
    """並列処理固有のエラー

    並列処理実行中に発生するエラーを表現する例外クラス。
    プロセス間通信、リソース競合、タイムアウト等の問題を示す。

    Examples:
        >>> raise ParallelProcessingError("プロセス間でのデータ競合が発生")
    """

    pass


class ChunkProcessingError(Exception):
    """チャンク処理でのエラー

    テキストをチャンク単位で処理する際に発生するエラー。
    チャンク分割失敗、処理中断、結果統合失敗等を示す。

    Examples:
        >>> raise ChunkProcessingError("チャンクサイズが制限を超過")
    """

    pass


class MemoryMonitoringError(Exception):
    """メモリ監視でのエラー

    メモリ使用量監視システムで発生するエラー。
    メモリ制限超過、監視システム障害、リソース不足等を示す。

    Examples:
        >>> raise MemoryMonitoringError("メモリ使用量が制限値250MBを超過")
    """

    pass


class ParallelProcessingConfig:
    """並列処理の設定管理"""

    def __init__(self) -> None:
        """並列処理設定の初期化

        デフォルトの並列処理設定値を設定する。
        しきい値、チャンクサイズ、メモリ監視、タイムアウト等を含む。
        """
        # 並列処理しきい値設定
        self.parallel_threshold_lines = 10000  # 10K行以上で並列化
        self.parallel_threshold_size = 10 * 1024 * 1024  # 10MB以上で並列化

        # チャンク設定
        self.min_chunk_size = 50
        self.max_chunk_size = 2000
        self.target_chunks_per_core = 2  # CPUコアあたりのチャンク数

        # メモリ監視設定
        self.memory_warning_threshold_mb = 150
        self.memory_critical_threshold_mb = 250
        self.memory_check_interval = 10  # チャンク数

        # タイムアウト設定
        self.processing_timeout_seconds = 300  # 5分
        self.chunk_timeout_seconds = 30  # 30秒

        # パフォーマンス設定
        self.enable_progress_callbacks = True
        self.progress_update_interval = 100  # 行数
        self.enable_memory_monitoring = True
        self.enable_gc_optimization = True

    @classmethod
    def from_environment(cls) -> "ParallelProcessingConfig":
        """環境変数から設定を読み込み

        環境変数からカスタム設定値を読み取り、デフォルト設定を
        上書きした設定インスタンスを作成する。

        Returns:
            ParallelProcessingConfig: 環境変数適用済み設定インスタンス

        Environment Variables:
            KUMIHAN_PARALLEL_THRESHOLD_LINES: 並列処理開始行数しきい値
            KUMIHAN_PARALLEL_THRESHOLD_SIZE: 並列処理開始サイズしきい値
            KUMIHAN_MEMORY_LIMIT_MB: メモリ制限値（MB）
            KUMIHAN_PROCESSING_TIMEOUT: 処理タイムアウト値（秒）
        """
        import os

        config = cls()

        # 環境変数からの設定上書き
        if threshold_lines := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_LINES"):
            try:
                config.parallel_threshold_lines = int(threshold_lines)
            except ValueError:
                pass

        if threshold_size := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_SIZE"):
            try:
                config.parallel_threshold_size = int(threshold_size)
            except ValueError:
                pass

        if memory_limit := os.getenv("KUMIHAN_MEMORY_LIMIT_MB"):
            try:
                memory_limit_int = int(memory_limit)
                config.memory_critical_threshold_mb = memory_limit_int
                config.memory_warning_threshold_mb = int(memory_limit_int * 0.6)
            except ValueError:
                pass

        if timeout := os.getenv("KUMIHAN_PROCESSING_TIMEOUT"):
            try:
                config.processing_timeout_seconds = int(timeout)
            except ValueError:
                pass

        return config

    def validate(self) -> bool:
        """設定値の検証

        設定されたパラメータが有効な値の範囲内にあるかを検証する。
        各しきい値、チャンクサイズ、メモリ制限の妥当性をチェック。

        Returns:
            bool: 全設定値が有効な場合True、無効な値がある場合False

        Validates:
            - 並列処理しきい値が正の値
            - チャンクサイズの最小値 < 最大値
            - メモリ警告値 < クリティカル値
            - タイムアウト値が正の値
        """
        try:
            assert self.parallel_threshold_lines > 0
            assert self.parallel_threshold_size > 0
            assert self.min_chunk_size > 0
            assert self.max_chunk_size > self.min_chunk_size
            assert self.memory_warning_threshold_mb > 0
            assert self.memory_critical_threshold_mb > self.memory_warning_threshold_mb
            assert self.processing_timeout_seconds > 0
            return True
        except AssertionError:
            return False


from ...parsers.unified_keyword_parser import (
    UnifiedKeywordParser as KeywordParser,
)


class Parser:
    """統合パーサークラス - コア実装

    Kumihan記法テキストを解析してASTノードに変換する統合パーサー。
    Phase3最適化により抽出されたメインパーサーで、元のparser.pyから
    分離され、機能が整理されている。逐次処理と並列処理に対応。

    Attributes:
        config (Dict[str, Any]): パーサー設定辞書
        lines (List[str]): 処理対象の行リスト
        current (int): 現在の処理行インデックス
        errors (List[str]): エラーメッセージリスト
        graceful_errors (List[str]): グレースフルエラーリスト
        parallel_config (ParallelProcessingConfig): 並列処理設定

    Examples:
        >>> parser = Parser()
        >>> content = "# 見出し #内容##"
        >>> nodes = parser.parse(content)
        >>> print(len(nodes))
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """パーサーを初期化

        パーサーインスタンスを初期化し、設定とコンポーネントを準備する。

        Args:
            config (Optional[Dict[str, Any]]): パーサー設定辞書。
                Noneの場合はデフォルト設定を使用。
        """
        self.config = config or {}
        self.lines: List[str] = []
        self.current = 0
        self.errors: List[str] = []
        self.logger = logging.getLogger(__name__)

        # Graceful error handling
        self.graceful_errors: List[str] = []
        self.graceful_syntax_errors: List[str] = []

        # 並列処理設定
        self.parallel_config = ParallelProcessingConfig()

        # パーサー初期化（統合最適化後：利用可能なもののみ）
        try:
            self.keyword_parser: Optional[KeywordParser] = KeywordParser()
        except Exception:
            self.keyword_parser = None

        # 統合最適化後: 並列処理は無効化（簡素化のため）
        self.parallel_processor = None

        # しきい値設定
        self.parallel_threshold_lines = 1000
        self.parallel_threshold_size = 50000

        # スレッド制御
        self._cancelled = False

        # パフォーマンス統計
        self._thread_local = threading.local()

    @property
    def _thread_local_storage(self) -> threading.local:
        """スレッドローカルストレージを取得

        Returns:
            threading.local: スレッドローカルデータストレージ
        """
        return self._thread_local

    def parse(self, content: str, use_parallel: bool = True) -> List[Node]:
        """テキストを解析してASTノードのリストを返す

        Kumihan記法テキストを解析し、対応するASTノードリストに変換する。
        エラー処理、パフォーマンス監視、キャンセル機能を含む。

        Args:
            content (str): 解析対象のKumihan記法テキスト
            use_parallel (bool, optional): 並列処理使用フラグ。Defaults to True.
                （注：統合最適化後は逐次処理のみ使用）

        Returns:
            List[Node]: 解析されたASTノードのリスト

        Examples:
            >>> parser = Parser()
            >>> nodes = parser.parse("# 見出し #内容##")
            >>> print(nodes[0].type)  # "text"
        """
        if not content:
            return []

        start_time = time.time()
        self.lines = content.splitlines()
        self.current = 0
        self.errors = []
        self.graceful_errors = []
        self._cancelled = False

        try:
            # 統合最適化後：逐次処理のみ（並列処理は無効化）
            result = self.parse_streaming_from_text(content)

            # パフォーマンス統計記録
            processing_time = time.time() - start_time
            self.logger.info(
                f"解析完了: {len(self.lines)}行を{processing_time:.3f}秒で処理"
            )

            return result

        except Exception as e:
            self.logger.error(f"解析エラー: {e}")
            self.add_error(f"解析エラー: {str(e)}")
            return [error_node(f"解析エラー: {str(e)}")]

    def parse_optimized(self, content: str) -> List[Node]:
        """最適化された解析（シンプル版）

        高速化を重視したシンプルな解析処理。基本的な行単位解析のみ実行。

        Args:
            content (str): 解析対象テキスト

        Returns:
            List[Node]: 解析結果のASTノードリスト
        """
        if not content:
            return []

        self.lines = self._split_lines_optimized(content)
        self.current = 0
        self.errors = []

        results = []
        for i, line in enumerate(self.lines):
            if self._cancelled:
                break

            self.current = i
            try:
                node = self._parse_line(line)
                if node:
                    results.append(node)
            except Exception as e:
                self.add_error(f"行 {i+1}: {str(e)}")
                results.append(error_node(f"行 {i+1}: {str(e)}"))

        return results

    def _split_lines_optimized(self, content: str) -> List[str]:
        """最適化された行分割

        各種改行文字に対応した高速な行分割処理。

        Args:
            content (str): 分割対象テキスト

        Returns:
            List[str]: 分割された行のリスト
        """
        # 高速な行分割（改行文字を保持）
        if "\r\n" in content:
            return content.split("\r\n")
        elif "\r" in content:
            return content.split("\r")
        else:
            return content.split("\n")

    def parse_streaming_from_text(self, content: str) -> List[Node]:
        """ストリーミング解析（逐次処理）

        行単位でストリーミング解析を実行し、グレースフルエラー
        ハンドリングにより処理を継続する。

        Args:
            content (str): 解析対象テキスト

        Returns:
            List[Node]: 解析結果のASTノードリスト
        """
        results = []
        self.lines = content.splitlines()

        for i, line in enumerate(self.lines):
            if self._cancelled:
                break

            self.current = i

            try:
                node = self._parse_line_with_graceful_errors(line)
                if node:
                    results.append(node)
            except Exception as e:
                error_msg = f"行 {i+1}: {str(e)}"
                self.add_error(error_msg)
                results.append(error_node(error_msg))

        return results

    def parse_parallel_streaming(self, content: str) -> List[Node]:
        """並列ストリーミング解析（統合アーキテクチャ対応）

        統合最適化後は逐次処理をメインとし、必要時のみ並列化。
        現在の実装では逐次処理にフォールバック。

        Args:
            content (str): 解析対象テキスト

        Returns:
            List[Node]: 解析結果のASTノードリスト
        """
        # 統合最適化後は逐次処理をメインとし、必要時のみ並列化
        return self.parse_streaming_from_text(content)

    def cancel_parsing(self) -> None:
        """解析をキャンセル

        進行中の解析処理を安全にキャンセルする。
        次のループで処理が停止される。
        """
        self._cancelled = True

    def get_performance_statistics(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得

        現在の解析処理状況とパフォーマンス情報を取得。

        Returns:
            Dict[str, Any]: パフォーマンス統計辞書
                - total_lines: 総行数
                - current_line: 現在処理行
                - error_count: エラー数
                - graceful_error_count: グレースフルエラー数
                - cancelled: キャンセル状態
        """
        return {
            "total_lines": len(self.lines),
            "current_line": self.current + 1,
            "error_count": len(self.errors),
            "graceful_error_count": len(self.graceful_errors),
            "cancelled": self._cancelled,
        }

    def get_parallel_processing_metrics(self) -> Dict[str, Any]:
        """並列処理のメトリクスを取得

        統合アーキテクチャでは並列処理を無効化しているため、
        無効状態の情報を返す。

        Returns:
            Dict[str, Any]: 並列処理メトリクス辞書
        """
        return {"parallel_processing": "disabled", "architecture": "unified"}

    def _parse_line(self, line: str) -> Optional[Node]:
        """単一行の解析（統合最適化後）

        一行のKumihan記法テキストをASTノードに変換する。
        統合パーサーアーキテクチャを使用。

        Args:
            line (str): 解析対象の行

        Returns:
            Optional[Node]: 解析結果のASTノード、空行の場合None
        """
        if not line.strip():
            return None

        # 統合パーサーアーキテクチャを使用
        try:
            # create_nodeのインポートを使用
            from ..ast_nodes import create_node

            # シンプルなテキストノード作成（統合最適化後）
            return create_node("text", line)

        except Exception as e:
            self.logger.error(f"行解析エラー: {e}")
            return error_node(f"行解析エラー: {str(e)}")

    def _parse_line_with_graceful_errors(self, line: str) -> Optional[Node]:
        """グレースフルエラーハンドリング付き行解析

        エラーが発生しても処理を継続し、エラーノードとして
        結果に含める安全な行解析処理。

        Args:
            line (str): 解析対象の行

        Returns:
            Optional[Node]: 解析結果またはエラーノード
        """
        try:
            return self._parse_line(line)
        except Exception as e:
            # グレースフルエラーとして記録
            self.graceful_errors.append(f"行 {self.current + 1}: {str(e)}")
            return error_node(f"構文エラー: {str(e)}")

    def add_error(self, error: str) -> None:
        """エラーを追加

        解析エラーをエラーリストに追加し、ログ出力する。

        Args:
            error (str): エラーメッセージ
        """
        self.errors.append(error)
