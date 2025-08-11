#!/usr/bin/env python3
"""
30万文字処理パフォーマンステスト（改良版）
Issue #694検証 - 実用的な大容量ファイル処理性能の実証
"""

import gc
import statistics
import sys
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import psutil

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.parser import StreamingParser, parse


class RealisticContentGenerator:
    """実用的な30万文字テストコンテンツ生成器"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.target_chars = 300000  # 30万文字

    def generate_realistic_content(self) -> str:
        """実用的なKumihan記法30万文字コンテンツを生成"""
        self.logger.info(f"Generating realistic content: target {self.target_chars} characters")

        # 実用的なコンテンツテンプレート
        content_blocks = [
            # 完全なブロック記法
            """# 見出し1 # システム設計書 第{section}章
システムの設計について詳細に説明します。

# 太字 # **重要な要件**として以下の点を考慮する必要があります。
- 性能要件: 高速処理が求められる
- 安全性要件: データの整合性を保つこと
- 運用要件: 24時間365日の稼働

# イタリック # *注意事項*として、メンテナンス時間を考慮してください。

通常のパラグラフです。この部分では詳細な説明を記述し、
複数行にわたって内容を展開します。
改行も含めて自然な文章構造を作成します。

# コードブロック #
```python
def process_data(data):
    result = []
    for item in data:
        if item.is_valid():
            result.append(item.process())
    return result
```
##

# 引用 # > この部分は重要な引用文です。
> 複数行にわたる引用も可能です。
> システム設計の原則として覚えておきましょう。

# リスト #
- 項目1: 基本機能の実装
- 項目2: テスト実装
- 項目3: ドキュメント作成
- 項目4: 性能チューニング

順序付きリスト:
1. 要件定義フェーズ
2. 設計フェーズ
3. 実装フェーズ
4. テストフェーズ
5. リリースフェーズ

""",
            """# 見出し2 # 技術仕様 第{section}章

# ハイライト # ==重要な技術仕様==について説明します。

技術的な詳細説明がここに記述されます。
システムアーキテクチャの概要から実装詳細まで、
幅広い内容をカバーします。

# 下線 # __重要な注意点__として以下を確認してください。

# 取り消し線 # ~~古い仕様~~は使用しないでください。

# コード # `configure_system()`メソッドを使用します。

詳細な技術仕様:
- API設計: RESTful APIを採用
- データベース: PostgreSQL使用
- キャッシュ: Redis使用
- 認証: JWT Token方式

# 注意 # ⚠️ セキュリティ要件を必ず満たすこと

パフォーマンス要件として、以下の基準を満たす必要があります:
- レスポンス時間: 100ms以内
- スループット: 1000req/sec以上
- 可用性: 99.9%以上

""",
            """# 見出し3 # 運用手順 第{section}章

# 情報 # ℹ️ 運用時の重要な情報をまとめています。

システムの運用手順について詳しく説明します。
日常的な運用から障害対応まで幅広くカバーします。

# 見出し4 # 日常運用手順

毎日実施する必要がある運用タスク:
1. システム状態確認
2. ログファイル確認
3. バックアップ状況確認
4. 性能監視データ確認

# 見出し5 # 障害対応手順

障害発生時の対応フロー:
- 障害検知と初期対応
- 原因調査と分析
- 復旧作業の実施
- 事後対応と改善

# 折りたたみ # 詳細ログ情報
障害調査時に確認すべきログファイル:
- application.log
- error.log
- access.log
- system.log
##

通常の運用では、これらの手順を順番に実行していきます。
マニュアルに従って正確に作業を進めることが重要です。

""",
            """# 中央寄せ #
プロジェクト概要
システム名: 大容量データ処理システム
##

大容量データの処理を効率的に行うシステムです。
ストリーミング処理により、メモリ使用量を抑制しながら
高速な処理を実現します。

# 見出し1 # データ処理フロー

データ処理の流れは以下の通りです:

1. データ受信
   - 外部システムからのデータ受信
   - フォーマット検証
   - 一時保存

2. 前処理
   - データクレンジング
   - 正規化処理
   - バリデーション

3. メイン処理
   - ビジネスロジック適用
   - 計算処理実行
   - 結果生成

4. 後処理
   - 結果検証
   - フォーマット変換
   - 出力処理

各段階で適切なエラーハンドリングを行い、
処理の継続性を保証します。

""",
        ]

        # 目標文字数まで生成
        content_parts = []
        current_chars = 0
        section_num = 1
        block_index = 0

        while current_chars < self.target_chars:
            # テンプレートを選択
            template = content_blocks[block_index % len(content_blocks)]

            # セクション番号を設定
            content_block = template.format(section=section_num)

            content_parts.append(content_block)
            current_chars += len(content_block)

            section_num += 1
            block_index += 1

            # 進捗表示
            if current_chars % 50000 == 0 and current_chars > 0:
                self.logger.debug(f"Generated {current_chars // 1000}K characters...")

        # 最終コンテンツ
        final_content = "\n".join(content_parts)

        # 正確な文字数調整
        if len(final_content) > self.target_chars:
            final_content = final_content[: self.target_chars]

        actual_chars = len(final_content)
        actual_bytes = len(final_content.encode("utf-8"))
        line_count = len(final_content.split("\n"))

        self.logger.info(
            f"Realistic content generation completed: "
            f"{actual_chars} characters, {actual_bytes} bytes, {line_count} lines"
        )

        return final_content


class FairPerformanceBenchmark:
    """公正なパフォーマンスベンチマーク実行器"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.process = psutil.Process()

    def measure_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（MB）"""
        return self.process.memory_info().rss / 1024 / 1024

    def benchmark_streaming_parser_optimized(self, content: str, runs: int = 5) -> Dict[str, Any]:
        """StreamingParser最適化ベンチマーク"""
        self.logger.info(f"Benchmarking Optimized StreamingParser: {runs} runs")

        results = []

        for run in range(runs):
            self.logger.info(f"StreamingParser run {run + 1}/{runs}")

            # メモリ測定開始
            gc.collect()
            initial_memory = self.measure_memory_usage()

            # パフォーマンス測定
            start_time = time.perf_counter()

            # StreamingParserで解析（監視機能を最小化）
            parser = StreamingParser()
            nodes = []

            # プログレスコールバックなしで実行
            for node in parser.parse_streaming_from_text(content):
                nodes.append(node)

            end_time = time.perf_counter()

            # 最終メモリ測定
            final_memory = self.measure_memory_usage()

            # 結果記録
            duration = end_time - start_time
            node_count = len(nodes)

            run_result = {
                "run": run + 1,
                "duration_seconds": duration,
                "node_count": node_count,
                "characters_per_second": len(content) / duration if duration > 0 else 0,
                "nodes_per_second": node_count / duration if duration > 0 else 0,
                "memory_growth_mb": final_memory - initial_memory,
                "error_count": len(parser.get_errors()) if hasattr(parser, "get_errors") else 0,
            }

            results.append(run_result)

            # クリーンアップ
            del parser, nodes
            gc.collect()

            self.logger.info(
                f"Run {run + 1}: {duration:.3f}s, {node_count} nodes, "
                f"{run_result['characters_per_second']:,.0f} chars/sec"
            )

        # 統計計算（最初の実行を除外してウォームアップ効果を除去）
        warm_results = results[1:] if len(results) > 1 else results

        durations = [r["duration_seconds"] for r in warm_results]
        char_rates = [r["characters_per_second"] for r in warm_results]
        node_counts = [r["node_count"] for r in warm_results]

        summary = {
            "parser_type": "StreamingParser",
            "runs": len(warm_results),
            "avg_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "median_duration": statistics.median(durations),
            "avg_chars_per_second": statistics.mean(char_rates),
            "avg_node_count": statistics.mean(node_counts),
            "avg_memory_growth_mb": statistics.mean([r["memory_growth_mb"] for r in warm_results]),
            "total_errors": sum(r["error_count"] for r in results),
            "detailed_results": results,
        }

        return summary

    def benchmark_traditional_parser(self, content: str, runs: int = 5) -> Dict[str, Any]:
        """従来Parser公正ベンチマーク"""
        self.logger.info(f"Benchmarking Traditional Parser: {runs} runs")

        results = []

        for run in range(runs):
            self.logger.info(f"Traditional Parser run {run + 1}/{runs}")

            # メモリ測定開始
            gc.collect()
            initial_memory = self.measure_memory_usage()

            # パフォーマンス測定
            start_time = time.perf_counter()

            # 従来Parserで解析
            nodes = parse(content)

            end_time = time.perf_counter()

            # 最終メモリ測定
            final_memory = self.measure_memory_usage()

            # 結果記録
            duration = end_time - start_time
            node_count = len(nodes) if nodes else 0

            run_result = {
                "run": run + 1,
                "duration_seconds": duration,
                "node_count": node_count,
                "characters_per_second": len(content) / duration if duration > 0 else 0,
                "nodes_per_second": node_count / duration if duration > 0 else 0,
                "memory_growth_mb": final_memory - initial_memory,
                "error_count": 0,
            }

            results.append(run_result)

            # クリーンアップ
            del nodes
            gc.collect()

            self.logger.info(
                f"Run {run + 1}: {duration:.3f}s, {node_count} nodes, "
                f"{run_result['characters_per_second']:,.0f} chars/sec"
            )

        # 統計計算（最初の実行を除外してウォームアップ効果を除去）
        warm_results = results[1:] if len(results) > 1 else results

        durations = [r["duration_seconds"] for r in warm_results]
        char_rates = [r["characters_per_second"] for r in warm_results]
        node_counts = [r["node_count"] for r in warm_results]

        summary = {
            "parser_type": "TraditionalParser",
            "runs": len(warm_results),
            "avg_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "median_duration": statistics.median(durations),
            "avg_chars_per_second": statistics.mean(char_rates),
            "avg_node_count": statistics.mean(node_counts),
            "avg_memory_growth_mb": statistics.mean([r["memory_growth_mb"] for r in warm_results]),
            "total_errors": 0,
            "detailed_results": results,
        }

        return summary

    def simulate_large_file_scenario(self, content: str) -> Dict[str, Any]:
        """大容量ファイルシナリオのシミュレーション"""
        self.logger.info("Simulating large file processing scenario")

        # 複数ファイル同時処理のシミュレーション
        file_sizes = [len(content) // 4, len(content) // 2, len(content)]  # 異なるサイズ
        scenario_results = {}

        for i, size in enumerate(file_sizes):
            test_content = content[:size]
            scenario_name = f"{size // 1000}K_file"

            self.logger.info(f"Testing scenario: {scenario_name}")

            # StreamingParserテスト
            start_time = time.perf_counter()
            parser = StreamingParser()
            streaming_nodes = list(parser.parse_streaming_from_text(test_content))
            streaming_duration = time.perf_counter() - start_time

            # 従来Parserテスト
            start_time = time.perf_counter()
            traditional_nodes = parse(test_content)
            traditional_duration = time.perf_counter() - start_time

            scenario_results[scenario_name] = {
                "content_size": size,
                "streaming_duration": streaming_duration,
                "traditional_duration": traditional_duration,
                "streaming_nodes": len(streaming_nodes),
                "traditional_nodes": len(traditional_nodes) if traditional_nodes else 0,
                "speedup_ratio": (
                    traditional_duration / streaming_duration if streaming_duration > 0 else 0
                ),
            }

            # クリーンアップ
            del parser, streaming_nodes, traditional_nodes
            gc.collect()

        return scenario_results


def main():
    """改良版30万文字パフォーマンステスト実行"""
    print("🚀 Issue #694 - 30万文字処理パフォーマンステスト（改良版）")
    print("=" * 65)

    logger = get_logger(__name__)

    try:
        # 1. 実用的テストコンテンツ生成
        print("📝 Step 1: 実用的30万文字テストコンテンツ生成")
        generator = RealisticContentGenerator()
        test_content = generator.generate_realistic_content()

        print(f"✅ 生成完了:")
        print(f"   文字数: {len(test_content):,} 文字")
        print(f"   バイト数: {len(test_content.encode('utf-8')):,} バイト")
        print(f"   行数: {len(test_content.split(chr(10))):,} 行")
        print()

        # 2. 公正なベンチマーク実行
        print("⚡ Step 2: 公正なパフォーマンス比較")
        benchmark = FairPerformanceBenchmark()

        # StreamingParserテスト
        print("\n🔄 StreamingParser 最適化ベンチマーク実行中...")
        streaming_results = benchmark.benchmark_streaming_parser_optimized(test_content, runs=5)

        # 従来Parserテスト
        print("\n🔄 Traditional Parser ベンチマーク実行中...")
        traditional_results = benchmark.benchmark_traditional_parser(test_content, runs=5)

        # シナリオテスト
        print("\n🔄 大容量ファイルシナリオテスト実行中...")
        scenario_results = benchmark.simulate_large_file_scenario(test_content)

        # 3. 結果分析・レポート出力
        print("\n" + "=" * 65)
        print("🏆 30万文字処理パフォーマンステスト結果（改良版）")
        print("=" * 65)

        print(f"\n📈 StreamingParser 性能:")
        print(f"  平均処理時間: {streaming_results['avg_duration']:.3f}秒")
        print(f"  最高速度: {streaming_results['min_duration']:.3f}秒")
        print(f"  中央値: {streaming_results['median_duration']:.3f}秒")
        print(f"  処理速度: {streaming_results['avg_chars_per_second']:,.0f} 文字/秒")
        print(f"  平均ノード数: {streaming_results['avg_node_count']:.0f}")
        print(f"  平均メモリ増加: {streaming_results['avg_memory_growth_mb']:.1f}MB")
        print(f"  エラー数: {streaming_results['total_errors']}")

        print(f"\n📊 Traditional Parser 性能:")
        print(f"  平均処理時間: {traditional_results['avg_duration']:.3f}秒")
        print(f"  最高速度: {traditional_results['min_duration']:.3f}秒")
        print(f"  中央値: {traditional_results['median_duration']:.3f}秒")
        print(f"  処理速度: {traditional_results['avg_chars_per_second']:,.0f} 文字/秒")
        print(f"  平均ノード数: {traditional_results['avg_node_count']:.0f}")
        print(f"  平均メモリ増加: {traditional_results['avg_memory_growth_mb']:.1f}MB")

        # 比較分析
        speedup = traditional_results["avg_duration"] / streaming_results["avg_duration"]
        throughput_ratio = (
            streaming_results["avg_chars_per_second"] / traditional_results["avg_chars_per_second"]
        )
        memory_efficiency = (
            traditional_results["avg_memory_growth_mb"] / streaming_results["avg_memory_growth_mb"]
            if streaming_results["avg_memory_growth_mb"] > 0
            else 1.0
        )

        print(f"\n🔍 比較分析結果:")
        print(f"  処理速度比較: {speedup:.2f}倍 {'高速化' if speedup > 1 else '低下'}")
        print(f"  スループット比: {throughput_ratio:.2f}倍")
        print(
            f"  メモリ効率比: {memory_efficiency:.2f}倍 {'効率的' if memory_efficiency > 1 else '非効率'}"
        )

        # Issue #694要求仕様照合
        lines_count = len(test_content.split("\n"))
        time_per_1000_lines = (streaming_results["avg_duration"] / lines_count) * 1000
        target_time = 10.0  # 1000行10秒以内

        print(f"\n🎯 Issue #694 要求仕様照合:")
        print(f"  総行数: {lines_count:,} 行")
        print(f"  1000行処理時間: {time_per_1000_lines:.3f}秒")
        print(f"  目標時間: {target_time}秒以内")
        print(f"  要求達成: {'✅ 達成' if time_per_1000_lines <= target_time else '❌ 未達成'}")

        if time_per_1000_lines <= target_time:
            performance_factor = target_time / time_per_1000_lines
            print(f"  性能優位性: {performance_factor:.0f}倍高速")

        # シナリオ結果
        print(f"\n📋 大容量ファイルシナリオテスト結果:")
        for scenario, result in scenario_results.items():
            print(f"  {scenario}:")
            print(f"    StreamingParser: {result['streaming_duration']:.3f}秒")
            print(f"    Traditional Parser: {result['traditional_duration']:.3f}秒")
            print(f"    速度比: {result['speedup_ratio']:.2f}倍")

        # 最終評価
        requirements_met = (
            time_per_1000_lines <= target_time
            and streaming_results["total_errors"] == 0
            and streaming_results["avg_memory_growth_mb"] < 100  # 100MB以下
        )

        print(f"\n🏅 総合評価: {'🌟 完全成功' if requirements_met else '⚠️ 部分成功'}")

        if requirements_met:
            print("✅ Issue #694 大容量ファイル処理パフォーマンス最適化要件を満たしています。")
            print("✅ StreamingParserは実用レベルの性能を実現しています。")
        else:
            print("⚠️ 一部要件で改善の余地があります。")

        # 実用性評価
        practical_performance = (
            streaming_results["avg_chars_per_second"] > 100000
        )  # 10万文字/秒以上
        practical_memory = streaming_results["avg_memory_growth_mb"] < 50  # 50MB以下

        print(f"\n💡 実用性評価:")
        print(f"  処理速度: {'✅ 実用的' if practical_performance else '⚠️ 要改善'}")
        print(f"  メモリ使用: {'✅ 効率的' if practical_memory else '⚠️ 要改善'}")

        return 0 if requirements_met else 1

    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
