"""
パフォーマンス監視メトリクスシステム
Issue #694 Phase 3対応 - 詳細な性能測定・分析
"""

import json
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

from .logger import get_logger


@dataclass
class PerformanceSnapshot:
    """パフォーマンススナップショット"""

    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    processing_rate: float  # items/sec
    items_processed: int
    total_items: int
    stage: str
    thread_count: int = 0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0


@dataclass
class ProcessingStats:
    """処理統計情報"""

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_items: int = 0
    items_processed: int = 0
    errors_count: int = 0
    warnings_count: int = 0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    processing_phases: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """処理時間（秒）"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def items_per_second(self) -> float:
        """処理速度（アイテム/秒）"""
        duration = self.duration_seconds
        return self.items_processed / duration if duration > 0 else 0
    
    @property
    def completion_rate(self) -> float:
        """完了率（%）"""
        if self.total_items == 0:
            return 0.0
        return (self.items_processed / self.total_items) * 100


class PerformanceMonitor:
    """
    リアルタイムパフォーマンス監視システム

    機能:
    - CPU・メモリ使用量の継続監視
    - 処理速度・スループット測定
    - ボトルネック検出
    - メトリクス履歴保存
    - パフォーマンスレポート生成
    """

    def __init__(self, monitoring_interval: float = 1.0, history_size: int = 1000):
        self.logger = get_logger(__name__)
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 監視データ
        self.snapshots: deque[PerformanceSnapshot] = deque(maxlen=history_size)
        self.stats = ProcessingStats()

        # 監視制御
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # プロセス情報
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss

        # コールバック
        self.alert_callbacks: List[Callable[[str, Dict], None]] = []

        self.logger.info(
            f"PerformanceMonitor initialized: interval={monitoring_interval}s, history={history_size}"
        )

    def start_monitoring(self, total_items: int, initial_stage: str = "開始"):
        """パフォーマンス監視を開始"""
        with self._lock:
            if self._monitoring:
                self.logger.warning("Performance monitoring already started")
                return

            # 統計情報初期化
            self.stats = ProcessingStats(
                start_time=time.time(), total_items=total_items
            )
            self.stats.processing_phases.append(initial_stage)

            # 監視開始
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self._monitor_thread.start()

            self.logger.info(
                f"Performance monitoring started: {total_items} items, stage: {initial_stage}"
            )

    def stop_monitoring(self):
        """パフォーマンス監視を停止"""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False
            self.stats.end_time = time.time()

            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)

            self.logger.info(
                f"Performance monitoring stopped after {self.stats.duration_seconds:.2f}s"
            )

    def update_progress(self, items_processed: int, current_stage: str = ""):
        """進捗を更新"""
        with self._lock:
            self.stats.items_processed = items_processed

            if current_stage and current_stage not in self.stats.processing_phases:
                self.stats.processing_phases.append(current_stage)

    def add_error(self):
        """エラーカウントを増加"""
        with self._lock:
            self.stats.errors_count += 1

    def add_warning(self):
        """警告カウントを増加"""
        with self._lock:
            self.stats.warnings_count += 1

    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """アラートコールバックを追加"""
        self.alert_callbacks.append(callback)

    def get_current_snapshot(self) -> PerformanceSnapshot:
        """現在のパフォーマンススナップショットを取得"""
        try:
            # CPU・メモリ情報
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()

            # 処理速度計算
            processing_rate = self.stats.items_per_second

            # ディスクI/O（可能な場合）
            try:
                io_counters = self.process.io_counters()
                disk_io_read_mb = io_counters.read_bytes / 1024 / 1024
                disk_io_write_mb = io_counters.write_bytes / 1024 / 1024
            except (AttributeError, psutil.AccessDenied):
                disk_io_read_mb = disk_io_write_mb = 0.0

            # スレッド数
            thread_count = self.process.num_threads()

            # 現在のステージ
            current_stage = (
                self.stats.processing_phases[-1]
                if self.stats.processing_phases
                else "unknown"
            )

            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                processing_rate=processing_rate,
                items_processed=self.stats.items_processed,
                total_items=self.stats.total_items,
                stage=current_stage,
                thread_count=thread_count,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
            )

        except Exception as e:
            self.logger.error(f"Error creating performance snapshot: {e}")
            # フォールバック: 基本的な情報のみ
            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                processing_rate=0.0,
                items_processed=self.stats.items_processed,
                total_items=self.stats.total_items,
                stage="error",
            )

    def _monitoring_loop(self):
        """監視ループ（別スレッドで実行）"""
        self.logger.debug("Performance monitoring loop started")

        while self._monitoring:
            try:
                # スナップショット取得
                snapshot = self.get_current_snapshot()

                with self._lock:
                    self.snapshots.append(snapshot)

                    # ピークメモリ更新
                    if snapshot.memory_mb > self.stats.peak_memory_mb:
                        self.stats.peak_memory_mb = snapshot.memory_mb

                    # CPU平均計算（簡易版）
                    if len(self.snapshots) > 0:
                        recent_snapshots = list(self.snapshots)[-10:]  # 直近10サンプル
                        self.stats.avg_cpu_percent = sum(
                            s.cpu_percent for s in recent_snapshots
                        ) / len(recent_snapshots)

                # アラートチェック
                self._check_performance_alerts(snapshot)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

        self.logger.debug("Performance monitoring loop ended")

    def _check_performance_alerts(self, snapshot: PerformanceSnapshot):
        """パフォーマンスアラートをチェック"""
        alerts = []

        # 高CPU使用率アラート
        if snapshot.cpu_percent > 90:
            alerts.append(
                {
                    "type": "high_cpu",
                    "severity": "warning",
                    "message": f"高CPU使用率: {snapshot.cpu_percent:.1f}%",
                    "value": snapshot.cpu_percent,
                }
            )

        # 高メモリ使用率アラート
        if snapshot.memory_percent > 80:
            alerts.append(
                {
                    "type": "high_memory",
                    "severity": "warning",
                    "message": f"高メモリ使用率: {snapshot.memory_percent:.1f}% ({snapshot.memory_mb:.1f}MB)",
                    "value": snapshot.memory_percent,
                }
            )

        # 低処理速度アラート
        if (
            snapshot.processing_rate > 0 and snapshot.processing_rate < 100
        ):  # 100 items/sec未満
            alerts.append(
                {
                    "type": "low_processing_rate",
                    "severity": "info",
                    "message": f"低処理速度: {snapshot.processing_rate:.0f} items/sec",
                    "value": snapshot.processing_rate,
                }
            )

        # アラート通知
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert["type"], alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンス概要を取得"""
        with self._lock:
            recent_snapshots = list(self.snapshots)[-10:] if self.snapshots else []

            return {
                "duration_seconds": self.stats.duration_seconds,
                "items_processed": self.stats.items_processed,
                "total_items": self.stats.total_items,
                "completion_rate": self.stats.completion_rate,
                "items_per_second": self.stats.items_per_second,
                "errors_count": self.stats.errors_count,
                "warnings_count": self.stats.warnings_count,
                "peak_memory_mb": self.stats.peak_memory_mb,
                "avg_cpu_percent": self.stats.avg_cpu_percent,
                "processing_phases": self.stats.processing_phases,
                "current_memory_mb": (
                    recent_snapshots[-1].memory_mb if recent_snapshots else 0
                ),
                "current_cpu_percent": (
                    recent_snapshots[-1].cpu_percent if recent_snapshots else 0
                ),
                "snapshots_count": len(self.snapshots),
            }

    def generate_performance_report(self) -> str:
        """詳細なパフォーマンスレポートを生成"""
        summary = self.get_performance_summary()

        report_lines = [
            "🔍 パフォーマンス分析レポート",
            "=" * 50,
            f"処理時間: {summary['duration_seconds']:.2f}秒",
            f"処理項目: {summary['items_processed']:,} / "
            f"{summary['total_items']:,} ({summary['completion_rate']:.1f}%)",
            f"処理速度: {summary['items_per_second']:,.0f} items/秒",
            f"エラー: {summary['errors_count']}, 警告: {summary['warnings_count']}",
            "",
            "💾 リソース使用量:",
            f"  ピークメモリ: {summary['peak_memory_mb']:.1f}MB",
            f"  平均CPU: {summary['avg_cpu_percent']:.1f}%",
            f"  現在メモリ: {summary['current_memory_mb']:.1f}MB",
            f"  現在CPU: {summary['current_cpu_percent']:.1f}%",
            "",
            "🔄 処理フェーズ:",
        ]

        for phase in summary["processing_phases"]:
            report_lines.append(f"  - {phase}")

        # パフォーマンス傾向分析
        if len(self.snapshots) >= 5:
            report_lines.extend(
                [
                    "",
                    "📈 パフォーマンス傾向:",
                ]
            )

            snapshots_list = list(self.snapshots)

            # メモリ使用量傾向
            memory_trend = self._calculate_trend(
                [s.memory_mb for s in snapshots_list[-10:]]
            )
            memory_status = (
                "増加"
                if memory_trend > 0.5
                else "安定" if memory_trend > -0.5 else "減少"
            )
            report_lines.append(f"  メモリ使用量: {memory_status}")

            # 処理速度傾向
            rates = [
                s.processing_rate for s in snapshots_list[-10:] if s.processing_rate > 0
            ]
            if rates:
                rate_trend = self._calculate_trend(rates)
                rate_status = (
                    "向上"
                    if rate_trend > 0.5
                    else "安定" if rate_trend > -0.5 else "低下"
                )
                report_lines.append(f"  処理速度: {rate_status}")

        return "\n".join(report_lines)

    def _calculate_trend(self, values: List[float]) -> float:
        """値の傾向を計算（簡易線形回帰）"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_avg = sum(range(n)) / n
        y_avg = sum(values) / n

        numerator = sum((i - x_avg) * (values[i] - y_avg) for i in range(n))
        denominator = sum((i - x_avg) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    def save_metrics_to_file(self, file_path: Path):
        """メトリクスをファイルに保存"""
        try:
            metrics_data = {
                "summary": self.get_performance_summary(),
                "snapshots": [
                    {
                        "timestamp": s.timestamp,
                        "cpu_percent": s.cpu_percent,
                        "memory_mb": s.memory_mb,
                        "memory_percent": s.memory_percent,
                        "processing_rate": s.processing_rate,
                        "items_processed": s.items_processed,
                        "stage": s.stage,
                    }
                    for s in self.snapshots
                ],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Performance metrics saved to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save metrics to file: {e}")


class ProgressiveOutputSystem:
    """
    プログレッシブ出力システム（Issue #727 対応）

    機能:
    - リアルタイム結果出力
    - 段階的HTML生成
    - ユーザー体験向上
    - 大容量ファイル処理の可視性改善
    """

    def __init__(self, output_path: Optional[Path] = None, buffer_size: int = 1000):
        self.logger = get_logger(__name__)
        self.output_path = output_path
        self.buffer_size = buffer_size

        # 出力管理
        self.html_buffer = []
        self.total_nodes_processed = 0
        self.current_section = "header"

        # テンプレート部分
        self.html_header = ""
        self.html_footer = ""
        self.css_content = ""

        # ストリーム出力ファイル
        self.output_stream = None

        self.logger.info(
            f"Progressive output system initialized: buffer_size={buffer_size}"
        )

    def initialize_output_stream(
        self, template_content: str = "", css_content: str = ""
    ):
        """出力ストリームの初期化"""

        if not self.output_path:
            return  # ファイル出力無効

        try:
            self.output_stream = open(
                self.output_path, "w", encoding="utf-8", buffering=1
            )

            # HTMLヘッダーの準備
            self.css_content = css_content
            self.html_header = self._create_html_header(template_content)
            self.html_footer = self._create_html_footer()

            # ヘッダーを即座に出力
            self.output_stream.write(self.html_header)
            self.output_stream.flush()

            self.logger.info(f"Progressive output stream started: {self.output_path}")

        except Exception as e:
            self.logger.error(f"Failed to initialize output stream: {e}")
            self.output_stream = None

    def add_processed_node(self, node_html: str, node_info: dict = None):
        """処理済みノードの追加"""

        if not node_html.strip():
            return

        self.html_buffer.append(node_html)
        self.total_nodes_processed += 1

        # バッファサイズに達したら出力
        if len(self.html_buffer) >= self.buffer_size:
            self.flush_buffer()

        # プログレス表示
        if self.total_nodes_processed % 100 == 0:
            self.logger.info(
                f"Progressive output: {self.total_nodes_processed} nodes processed"
            )

    def flush_buffer(self):
        """バッファの強制出力"""

        if not self.html_buffer or not self.output_stream:
            return

        try:
            # バッファ内容をファイルに書き込み
            content = "\n".join(self.html_buffer)
            self.output_stream.write(content + "\n")
            self.output_stream.flush()

            # バッファクリア
            self.html_buffer.clear()

            self.logger.debug(f"Buffer flushed: {len(self.html_buffer)} items")

        except Exception as e:
            self.logger.error(f"Buffer flush error: {e}")

    def add_section_marker(self, section_name: str, section_content: str = ""):
        """セクションマーカーの追加"""

        self.current_section = section_name

        if section_content:
            section_html = f"""
<!-- ===== {section_name.upper()} SECTION START ===== -->
{section_content}
<!-- ===== {section_name.upper()} SECTION END ===== -->
"""
            self.add_processed_node(section_html)

    def finalize_output(self):
        """出力の最終化"""

        if not self.output_stream:
            return

        try:
            # 残りバッファを出力
            self.flush_buffer()

            # フッターを出力
            self.output_stream.write(self.html_footer)
            self.output_stream.flush()

            # ストリームクローズ
            self.output_stream.close()
            self.output_stream = None

            self.logger.info(
                f"Progressive output finalized: {self.total_nodes_processed} nodes, "
                f"output: {self.output_path}"
            )

        except Exception as e:
            self.logger.error(f"Output finalization error: {e}")

    def _create_html_header(self, template_content: str) -> str:
        """HTMLヘッダーの作成"""

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan Formatter - Progressive Output</title>
    <style>
{self.css_content}
/* Progressive output styles */
.kumihan-progressive-info {{
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    font-size: 12px;
    z-index: 1000;
}}
.kumihan-processing {{
    opacity: 0.7;
    transition: opacity 0.3s ease;
}}
    </style>
    <script>
// Progressive output JavaScript
let processedNodes = 0;
function updateProgressInfo() {{
    const info = document.querySelector('.kumihan-progressive-info');
    if (info) {{
        info.textContent = 'Kumihan-Formatter 処理中... ' + (window.processedNodes || 0) + ' nodes';
    }}
}}
setInterval(updateProgressInfo, 1000);
    </script>
</head>
<body>
<div class="kumihan-progressive-info">Kumihan Progressive Output - 処理開始</div>
<div class="kumihan-content">
<!-- PROGRESSIVE CONTENT START -->
"""

    def _create_html_footer(self) -> str:
        """HTMLフッターの作成"""

        return f"""
<!-- PROGRESSIVE CONTENT END -->
</div>
<script>
// Final processing info
const info = document.querySelector('.kumihan-progressive-info');
if (info) {{
    info.textContent = '✅ 処理完了 - {self.total_nodes_processed} nodes';
    info.style.backgroundColor = 'rgba(0,128,0,0.8)';
}}
document.querySelectorAll('.kumihan-processing').forEach(el => {{
    el.classList.remove('kumihan-processing');
}});
</script>
</body>
</html>"""

    def create_progress_html(self, current: int, total: int, stage: str = "") -> str:
        """プログレス表示HTML生成"""

        progress_percent = (current / total * 100) if total > 0 else 0

        return f"""
<div class="kumihan-progress-update" data-current="{current}" data-total="{total}">
    <div class="progress-bar" style="width: {progress_percent:.1f}%; background: linear-gradient(90deg, #4CAF50, #2196F3);"></div>
    <div class="progress-text">{stage} - {current}/{total} ({progress_percent:.1f}%)</div>
</div>
"""

    def get_output_statistics(self) -> dict:
        """出力統計の取得"""

        return {
            "total_nodes_processed": self.total_nodes_processed,
            "buffer_size": len(self.html_buffer),
            "current_section": self.current_section,
            "output_active": self.output_stream is not None,
            "output_path": str(self.output_path) if self.output_path else None,
        }

    def __enter__(self):
        """コンテキストマネージャー開始"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.finalize_output()


class PerformanceBenchmark:
    """
    パフォーマンスベンチマークシステム（Issue #727 対応）

    機能:
    - パーサー性能測定
    - メモリ効率テスト
    - 並列処理効果測定
    - 目標達成評価
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.results = {}
        self.test_data_cache = {}

    def run_comprehensive_benchmark(self) -> dict:
        """包括的ベンチマーク実行"""

        self.logger.info("🚀 Starting comprehensive performance benchmark...")

        benchmark_results = {
            "metadata": {
                "timestamp": time.time(),
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": os.cpu_count(),
            },
            "tests": {},
        }

        # テストケース定義
        test_cases = [
            {"name": "small", "lines": 1000, "description": "小規模ファイル(1K行)"},
            {"name": "medium", "lines": 5000, "description": "中規模ファイル(5K行)"},
            {"name": "large", "lines": 10000, "description": "大規模ファイル(10K行)"},
            {
                "name": "extra_large",
                "lines": 50000,
                "description": "超大規模ファイル(50K行)",
            },
        ]

        for test_case in test_cases:
            self.logger.info(f"📊 Testing {test_case['description']}...")

            test_results = self._run_single_benchmark(
                test_case["name"], test_case["lines"]
            )

            benchmark_results["tests"][test_case["name"]] = test_results

        # 目標達成評価
        benchmark_results["goal_assessment"] = self._assess_performance_goals(
            benchmark_results["tests"]
        )

        # サマリー生成
        benchmark_results["summary"] = self._generate_benchmark_summary(
            benchmark_results
        )

        self.logger.info("✅ Comprehensive benchmark completed")
        return benchmark_results

    def _run_single_benchmark(self, test_name: str, line_count: int) -> dict:
        """単一ベンチマークの実行"""

        # テストデータ生成
        test_text = self._generate_test_data(line_count)

        results = {
            "test_info": {
                "name": test_name,
                "line_count": line_count,
                "text_length": len(test_text),
                "text_size_mb": len(test_text) / 1024 / 1024,
            },
            "traditional_parser": {},
            "optimized_parser": {},
            "streaming_parser": {},
            "parallel_parser": {},
            "improvement_ratios": {},
        }

        # Traditional Parser テスト
        try:
            results["traditional_parser"] = self._benchmark_traditional_parser(
                test_text
            )
        except Exception as e:
            self.logger.error(f"Traditional parser test failed: {e}")
            results["traditional_parser"] = {"error": str(e)}

        # Optimized Parser テスト
        try:
            results["optimized_parser"] = self._benchmark_optimized_parser(test_text)
        except Exception as e:
            self.logger.error(f"Optimized parser test failed: {e}")
            results["optimized_parser"] = {"error": str(e)}

        # Streaming Parser テスト
        try:
            results["streaming_parser"] = self._benchmark_streaming_parser(test_text)
        except Exception as e:
            self.logger.error(f"Streaming parser test failed: {e}")
            results["streaming_parser"] = {"error": str(e)}

        # 改善率計算
        results["improvement_ratios"] = self._calculate_improvement_ratios(results)

        return results

    def _benchmark_traditional_parser(self, test_text: str) -> dict:
        """従来パーサーのベンチマーク"""

        from ...parser import Parser

        # メモリ使用量測定開始
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()

        # パーサー実行
        parser = Parser()
        nodes = parser.parse(test_text)

        parse_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory

        return {
            "parse_time_seconds": parse_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
            "nodes_count": len(nodes),
            "throughput_lines_per_second": (
                len(test_text.split("\n")) / parse_time if parse_time > 0 else 0
            ),
            "errors_count": len(parser.get_errors()),
        }

    def _benchmark_optimized_parser(self, test_text: str) -> dict:
        """最適化パーサーのベンチマーク"""

        from ...parser import Parser

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()

        # 最適化パーサー実行
        parser = Parser()
        nodes = parser.parse_optimized(test_text)

        parse_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_used = peak_memory - initial_memory

        return {
            "parse_time_seconds": parse_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
            "nodes_count": len(nodes),
            "throughput_lines_per_second": (
                len(test_text.split("\n")) / parse_time if parse_time > 0 else 0
            ),
            "errors_count": len(parser.get_errors()),
        }

    def _benchmark_streaming_parser(self, test_text: str) -> dict:
        """ストリーミングパーサーのベンチマーク"""

        from ...parser import StreamingParser

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()

        # ストリーミングパーサー実行
        parser = StreamingParser()
        nodes = list(parser.parse_streaming_from_text(test_text))

        parse_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_used = peak_memory - initial_memory

        return {
            "parse_time_seconds": parse_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
            "nodes_count": len(nodes),
            "throughput_lines_per_second": (
                len(test_text.split("\n")) / parse_time if parse_time > 0 else 0
            ),
            "errors_count": len(parser.get_errors()),
        }

    def _generate_test_data(self, line_count: int) -> str:
        """テストデータの生成"""

        if line_count in self.test_data_cache:
            return self.test_data_cache[line_count]

        lines = []

        # 多様なKumihan記法パターンを含むテストデータ
        patterns = [
            "これは通常のパラグラフです。",
            "# 太字 # このテキストは太字になります",
            "# イタリック # このテキストはイタリックになります",
            "# 見出し1 # 大きな見出し",
            "- リスト項目1",
            "- リスト項目2",
            "1. 順序付きリスト1",
            "2. 順序付きリスト2",
            "# 枠線 # 枠で囲まれたテキスト",
            "# ハイライト color=yellow # 黄色でハイライト",
            "",  # 空行
            "複数行にわたる\\n長いテキストの\\n例です。",
        ]

        for i in range(line_count):
            pattern = patterns[i % len(patterns)]
            if "項目" in pattern or "リスト" in pattern:
                lines.append(
                    pattern.replace("項目", f"項目{i+1}").replace(
                        "リスト", f"リスト{i+1}"
                    )
                )
            else:
                lines.append(f"{pattern} (行 {i+1})")

        test_text = "\n".join(lines)
        self.test_data_cache[line_count] = test_text

        return test_text

    def _calculate_improvement_ratios(self, results: dict) -> dict:
        """改善率の計算"""

        improvement = {}

        traditional = results.get("traditional_parser", {})
        optimized = results.get("optimized_parser", {})
        streaming = results.get("streaming_parser", {})

        if traditional.get("parse_time_seconds") and optimized.get(
            "parse_time_seconds"
        ):
            improvement["optimized_vs_traditional_speed"] = (
                traditional["parse_time_seconds"] / optimized["parse_time_seconds"]
            )

        if traditional.get("memory_used_mb") and optimized.get("memory_used_mb"):
            improvement["optimized_vs_traditional_memory"] = (
                traditional["memory_used_mb"] / optimized["memory_used_mb"]
            )

        if traditional.get("parse_time_seconds") and streaming.get(
            "parse_time_seconds"
        ):
            improvement["streaming_vs_traditional_speed"] = (
                traditional["parse_time_seconds"] / streaming["parse_time_seconds"]
            )

        return improvement

    def _assess_performance_goals(self, test_results: dict) -> dict:
        """Issue #727 パフォーマンス目標の達成評価"""

        assessment = {
            "goals": {
                "10k_lines_under_15s": False,
                "memory_reduction_66_percent": False,
                "100k_lines_under_180s": False,
                "10k_lines_under_30s": False,
            },
            "details": {},
        }

        # 10K行ファイル15秒以内目標
        large_test = test_results.get("large", {})
        if large_test:
            optimized_time = large_test.get("optimized_parser", {}).get(
                "parse_time_seconds", float("inf")
            )
            streaming_time = large_test.get("streaming_parser", {}).get(
                "parse_time_seconds", float("inf")
            )

            best_time = min(optimized_time, streaming_time)
            assessment["goals"]["10k_lines_under_15s"] = best_time <= 15.0
            assessment["details"]["10k_best_time"] = best_time

        # メモリ使用量66%削減目標
        if large_test:
            traditional_memory = large_test.get("traditional_parser", {}).get(
                "memory_used_mb", 0
            )
            optimized_memory = large_test.get("optimized_parser", {}).get(
                "memory_used_mb", 0
            )

            if traditional_memory > 0:
                memory_reduction = (
                    (traditional_memory - optimized_memory) / traditional_memory * 100
                )
                assessment["goals"]["memory_reduction_66_percent"] = (
                    memory_reduction >= 66.0
                )
                assessment["details"]["memory_reduction_percent"] = memory_reduction

        return assessment

    def _generate_benchmark_summary(self, benchmark_results: dict) -> dict:
        """ベンチマーク結果サマリー生成"""

        summary = {
            "overall_performance": "unknown",
            "key_achievements": [],
            "areas_for_improvement": [],
            "recommendations": [],
        }

        goals = benchmark_results.get("goal_assessment", {}).get("goals", {})

        achieved_goals = sum(1 for achieved in goals.values() if achieved)
        total_goals = len(goals)

        if achieved_goals >= total_goals * 0.8:
            summary["overall_performance"] = "excellent"
            summary["key_achievements"].append("ほぼ全ての性能目標を達成")
        elif achieved_goals >= total_goals * 0.6:
            summary["overall_performance"] = "good"
            summary["key_achievements"].append("主要な性能目標を達成")
        else:
            summary["overall_performance"] = "needs_improvement"
            summary["areas_for_improvement"].append("性能目標の達成率が低い")

        # 推奨事項
        if not goals.get("10k_lines_under_15s"):
            summary["recommendations"].append("大容量ファイル処理の更なる最適化が必要")

        if not goals.get("memory_reduction_66_percent"):
            summary["recommendations"].append("メモリ効率の改善が必要")

        return summary

    def generate_benchmark_report(self, results: dict) -> str:
        """ベンチマークレポートの生成"""

        report_lines = [
            "🔬 Kumihan-Formatter パフォーマンスベンチマークレポート",
            "=" * 60,
            f"実行日時: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['metadata']['timestamp']))}",
            f"プラットフォーム: {results['metadata']['platform']}",
            f"CPUコア数: {results['metadata']['cpu_count']}",
            "",
            "📊 テスト結果:",
        ]

        for test_name, test_data in results["tests"].items():
            info = test_data["test_info"]
            report_lines.extend(
                [
                    f"\n🔍 {info['name'].upper()} ({info['line_count']:,}行, {info['text_size_mb']:.1f}MB):",
                    f"  従来パーサー: {test_data['traditional_parser'].get('parse_time_seconds', 'N/A'):.2f}s, "
                    f"{test_data['traditional_parser'].get('memory_used_mb', 'N/A'):.1f}MB",
                    f"  最適化パーサー: {test_data['optimized_parser'].get('parse_time_seconds', 'N/A'):.2f}s, "
                    f"{test_data['optimized_parser'].get('memory_used_mb', 'N/A'):.1f}MB",
                    f"  ストリーミング: {test_data['streaming_parser'].get('parse_time_seconds', 'N/A'):.2f}s, "
                    f"{test_data['streaming_parser'].get('memory_used_mb', 'N/A'):.1f}MB",
                ]
            )

            # 改善率
            improvements = test_data.get("improvement_ratios", {})
            if improvements:
                speed_improve = improvements.get("optimized_vs_traditional_speed", 1)
                memory_improve = improvements.get("optimized_vs_traditional_memory", 1)
                report_lines.append(
                    f"  改善率: 速度 {speed_improve:.1f}x, メモリ {memory_improve:.1f}x"
                )

        # 目標達成状況
        goals = results.get("goal_assessment", {}).get("goals", {})
        report_lines.extend(
            [
                "",
                "🎯 目標達成状況:",
                f"  10K行15秒以内: {'✅' if goals.get('10k_lines_under_15s') else '❌'}",
                f"  メモリ66%削減: {'✅' if goals.get('memory_reduction_66_percent') else '❌'}",
                f"  100K行180秒以内: {'✅' if goals.get('100k_lines_under_180s') else '❌'}",
            ]
        )

        # サマリー
        summary = results.get("summary", {})
        report_lines.extend(
            [
                "",
                f"📈 総合評価: {summary.get('overall_performance', 'unknown').upper()}",
            ]
        )

        if summary.get("key_achievements"):
            report_lines.append("✨ 主な成果:")
            for achievement in summary["key_achievements"]:
                report_lines.append(f"  • {achievement}")

        if summary.get("recommendations"):
            report_lines.append("💡 推奨改善:")
            for rec in summary["recommendations"]:
                report_lines.append(f"  • {rec}")

        return "\n".join(report_lines)


# パフォーマンス監視用デコレータ
def monitor_performance(task_name: str = "処理"):
    """
    パフォーマンス監視のコンテキストマネージャー

    Args:
        task_name: タスク名

    Returns:
        PerformanceContext: パフォーマンス監視コンテキスト
    """
    return PerformanceContext(task_name)


class PerformanceContext:
    """パフォーマンス監視コンテキストマネージャー"""

    def __init__(self, task_name: str):
        self.task_name = task_name
        self.monitor = PerformanceMonitor()
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.monitor.start_monitoring(total_items=1000, initial_stage=self.task_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.stop_monitoring()

    def record_item_processed(self):
        """アイテム処理の記録"""
        if hasattr(self.monitor, "update_progress"):
            # 簡易的な進捗更新
            pass
