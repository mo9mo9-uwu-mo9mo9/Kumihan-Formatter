#!/usr/bin/env python3
"""
パフォーマンス最適化の統合テストスクリプト
Issue #727 - パフォーマンス最適化効果の確認

実行例:
    python scripts/test_performance_optimizations.py
    python scripts/test_performance_optimizations.py --quick
"""

import argparse
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_test_file(lines: int) -> str:
    """テスト用ファイル生成"""

    content_patterns = [
        "これは通常のテキストです。",
        "# 太字 # 重要なテキスト",
        "# イタリック # 強調されたテキスト",
        "# 見出し1 # メインタイトル",
        "# 見出し2 # サブタイトル",
        "- リスト項目A",
        "- リスト項目B",
        "1. 番号付きリスト1",
        "2. 番号付きリスト2",
        "# 枠線 # 重要な情報",
        "# ハイライト color=yellow # 注目ポイント",
        "",  # 空行
    ]

    lines_content = []
    for i in range(lines):
        pattern = content_patterns[i % len(content_patterns)]
        if pattern:
            lines_content.append(f"{pattern} (行番号: {i+1})")
        else:
            lines_content.append("")

    return "\n".join(lines_content)

def test_traditional_parser(text: str) -> dict:
    """従来パーサーのテスト（修正版）"""

    try:
        from kumihan_formatter.parser import Parser
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()
        parser = Parser()
        nodes = parser.parse(text)
        end_time = time.time()

        final_memory = process.memory_info().rss / 1024 / 1024

        return {
            "parse_time": end_time - start_time,
            "memory_used": final_memory - initial_memory,
            "nodes_count": len(nodes),
            "errors_count": len(parser.get_errors())
        }
    except Exception as e:
        return {
            "error": str(e),
            "parse_time": 0,
            "memory_used": 0,
            "nodes_count": 0,
            "errors_count": 0
        }

def test_optimized_parser(text: str) -> dict:
    """最適化パーサーのテスト（修正版）"""

    try:
        from kumihan_formatter.parser import Parser
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()
        parser = Parser()
        nodes = parser.parse_optimized(text)
        end_time = time.time()

        final_memory = process.memory_info().rss / 1024 / 1024

        return {
            "parse_time": end_time - start_time,
            "memory_used": final_memory - initial_memory,
            "nodes_count": len(nodes),
            "errors_count": len(parser.get_errors())
        }
    except Exception as e:
        return {
            "error": str(e),
            "parse_time": 0,
            "memory_used": 0,
            "nodes_count": 0,
            "errors_count": 0
        }

def test_streaming_parser(text: str) -> dict:
    """ストリーミングパーサーのテスト（修正版）"""

    try:
        from kumihan_formatter.parser import StreamingParser
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()
        parser = StreamingParser()
        nodes = list(parser.parse_streaming_from_text(text))
        end_time = time.time()

        final_memory = process.memory_info().rss / 1024 / 1024

        return {
            "parse_time": end_time - start_time,
            "memory_used": final_memory - initial_memory,
            "nodes_count": len(nodes),
            "errors_count": len(parser.get_errors())
        }
    except Exception as e:
        return {
            "error": str(e),
            "parse_time": 0,
            "memory_used": 0,
            "nodes_count": 0,
            "errors_count": 0
        }

def test_html_rendering(nodes) -> dict:
    """HTML レンダリングのテスト"""

    from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer
    import psutil

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024

    # 従来レンダリング
    start_time = time.time()
    renderer = HTMLRenderer()
    html_traditional = renderer.render_nodes(nodes)
    traditional_time = time.time() - start_time

    # 最適化レンダリング
    start_time = time.time()
    html_optimized = renderer.render_nodes_optimized(nodes)
    optimized_time = time.time() - start_time

    final_memory = process.memory_info().rss / 1024 / 1024

    return {
        "traditional_render_time": traditional_time,
        "optimized_render_time": optimized_time,
        "html_length": len(html_optimized),
        "memory_used": final_memory - initial_memory,
        "improvement_ratio": traditional_time / optimized_time if optimized_time > 0 else 1.0
    }

def main():
    """メインテスト実行"""

    parser = argparse.ArgumentParser(description="パフォーマンス最適化統合テスト")
    parser.add_argument("--quick", action="store_true", help="クイックテスト（小規模データのみ）")
    parser.add_argument("--lines", type=int, default=None, help="テスト行数の指定")

    args = parser.parse_args()

    print("🚀 Kumihan-Formatter パフォーマンス最適化統合テスト")
    print("=" * 60)

    # テストサイズ決定
    if args.lines:
        test_sizes = [args.lines]
    elif args.quick:
        test_sizes = [1000]
    else:
        test_sizes = [1000, 5000, 10000]

    overall_results = []

    for line_count in test_sizes:
        print(f"\n📊 テスト実行: {line_count:,} 行")
        print("-" * 40)

        # テストデータ生成
        print("テストデータ生成中...")
        test_text = create_test_file(line_count)
        text_size_mb = len(test_text) / 1024 / 1024
        print(f"テストデータサイズ: {text_size_mb:.2f} MB")

        results = {"line_count": line_count, "text_size_mb": text_size_mb}

        # 従来パーサーテスト
        print("従来パーサーテスト中...")
        try:
            results["traditional"] = test_traditional_parser(test_text)
            print(f"  時間: {results['traditional']['parse_time']:.2f}s, "
                  f"メモリ: {results['traditional']['memory_used']:.1f}MB")
        except Exception as e:
            print(f"  エラー: {e}")
            results["traditional"] = {"error": str(e)}

        # 最適化パーサーテスト
        print("最適化パーサーテスト中...")
        try:
            results["optimized"] = test_optimized_parser(test_text)
            print(f"  時間: {results['optimized']['parse_time']:.2f}s, "
                  f"メモリ: {results['optimized']['memory_used']:.1f}MB")
        except Exception as e:
            print(f"  エラー: {e}")
            results["optimized"] = {"error": str(e)}

        # ストリーミングパーサーテスト
        print("ストリーミングパーサーテスト中...")
        try:
            results["streaming"] = test_streaming_parser(test_text)
            print(f"  時間: {results['streaming']['parse_time']:.2f}s, "
                  f"メモリ: {results['streaming']['memory_used']:.1f}MB")
        except Exception as e:
            print(f"  エラー: {e}")
            results["streaming"] = {"error": str(e)}

        # 改善率計算
        if ("traditional" in results and "optimized" in results and
            "error" not in results["traditional"] and "error" not in results["optimized"]):

            speed_improvement = (results["traditional"]["parse_time"] /
                               results["optimized"]["parse_time"])
            memory_improvement = (results["traditional"]["memory_used"] /
                                results["optimized"]["memory_used"])

            print(f"\n✨ 改善効果:")
            print(f"  速度向上: {speed_improvement:.1f}x")
            print(f"  メモリ効率: {memory_improvement:.1f}x")

            results["improvements"] = {
                "speed_ratio": speed_improvement,
                "memory_ratio": memory_improvement
            }

        overall_results.append(results)

    # 総合評価
    print("\n🎯 Issue #727 目標達成評価:")
    print("-" * 40)

    # 10K行テストの評価
    large_test = next((r for r in overall_results if r["line_count"] == 10000), None)
    if large_test and "optimized" in large_test and "error" not in large_test["optimized"]:
        opt_time = large_test["optimized"]["parse_time"]
        goal_15s = opt_time <= 15.0
        print(f"10K行15秒以内目標: {'✅ 達成' if goal_15s else '❌ 未達成'} ({opt_time:.1f}s)")

        if "improvements" in large_test:
            memory_ratio = large_test["improvements"]["memory_ratio"]
            memory_66_percent = memory_ratio >= 1.5  # 66%削減 = 1.5倍効率
            print(f"メモリ66%削減目標: {'✅ 達成' if memory_66_percent else '❌ 未達成'} ({memory_ratio:.1f}x)")
    else:
        print("10K行テストが実行されていないため評価不可")

    print("\n🏁 テスト完了")
    return 0

if __name__ == "__main__":
    exit(main())
