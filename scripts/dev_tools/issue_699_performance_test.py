#!/usr/bin/env python3
"""
Issue #699 パフォーマンステスト実行スクリプト
大容量・複雑なサンプルファイルでIssue #727最適化効果を検証

実行例:
    python scripts/issue_699_performance_test.py
    python scripts/issue_699_performance_test.py --detailed
"""

import argparse
import sys
import time
import psutil
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_sample_file(file_path: Path, test_name: str) -> dict:
    """サンプルファイルのパフォーマンステスト"""
    
    print(f"\n📊 {test_name} テスト実行")
    print(f"ファイル: {file_path.name}")
    print("-" * 50)
    
    if not file_path.exists():
        return {"error": f"ファイルが存在しません: {file_path}"}
    
    # ファイル情報
    file_size_mb = file_path.stat().st_size / 1024 / 1024
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    line_count = len(content.split('\n'))
    
    print(f"📄 ファイル情報:")
    print(f"  サイズ: {file_size_mb:.2f} MB")
    print(f"  行数: {line_count:,} 行")
    print(f"  文字数: {len(content):,} 文字")
    
    results = {
        "file_info": {
            "size_mb": file_size_mb,
            "line_count": line_count,
            "char_count": len(content)
        }
    }
    
    try:
        # 従来パーサーテスト
        print(f"\n🔄 従来パーサーテスト...")
        results["traditional"] = test_traditional_parser(content)
        print(f"  時間: {results['traditional']['parse_time']:.2f}s")
        print(f"  メモリ: {results['traditional']['memory_used']:.1f}MB")
        print(f"  ノード数: {results['traditional']['nodes_count']:,}")
        
    except Exception as e:
        print(f"  エラー: {e}")
        results["traditional"] = {"error": str(e)}
    
    try:
        # 最適化パーサーテスト
        print(f"\n⚡ 最適化パーサーテスト...")
        results["optimized"] = test_optimized_parser(content)
        print(f"  時間: {results['optimized']['parse_time']:.2f}s")
        print(f"  メモリ: {results['optimized']['memory_used']:.1f}MB")
        print(f"  ノード数: {results['optimized']['nodes_count']:,}")
        
    except Exception as e:
        print(f"  エラー: {e}")
        results["optimized"] = {"error": str(e)}
    
    try:
        # ストリーミングパーサーテスト
        print(f"\n🌊 ストリーミングパーサーテスト...")
        results["streaming"] = test_streaming_parser(content)
        print(f"  時間: {results['streaming']['parse_time']:.2f}s")
        print(f"  メモリ: {results['streaming']['memory_used']:.1f}MB")
        print(f"  ノード数: {results['streaming']['nodes_count']:,}")
        
    except Exception as e:
        print(f"  エラー: {e}")
        results["streaming"] = {"error": str(e)}
    
    # 改善率計算
    if ("traditional" in results and "optimized" in results and 
        "error" not in results["traditional"] and "error" not in results["optimized"]):
        
        speed_improvement = (results["traditional"]["parse_time"] / 
                           results["optimized"]["parse_time"])
        memory_improvement = (results["traditional"]["memory_used"] / 
                            results["optimized"]["memory_used"]) if results["optimized"]["memory_used"] > 0 else 1.0
        
        print(f"\n✨ Issue #727 最適化効果:")
        print(f"  速度向上: {speed_improvement:.1f}x")
        print(f"  メモリ効率: {memory_improvement:.1f}x")
        
        results["improvements"] = {
            "speed_ratio": speed_improvement,
            "memory_ratio": memory_improvement
        }
    
    return results

def test_traditional_parser(text: str) -> dict:
    """従来パーサーのテスト"""
    
    try:
        from kumihan_formatter.parser import Parser
        
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
    """最適化パーサーのテスト"""
    
    try:
        from kumihan_formatter.parser import Parser
        
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
    """ストリーミングパーサーのテスト"""
    
    try:
        from kumihan_formatter.parser import StreamingParser
        
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

def main():
    """メインテスト実行"""
    
    parser = argparse.ArgumentParser(description="Issue #699 パフォーマンステスト")
    parser.add_argument("--detailed", action="store_true", help="詳細レポート出力")
    
    args = parser.parse_args()
    
    print("🚨 Issue #699 パフォーマンステスト実行")
    print("Issue #727最適化効果の検証")
    print("=" * 60)
    
    # テスト対象サンプルファイル
    samples_dir = project_root / "samples" / "performance"
    test_files = [
        (samples_dir / "10_large_document_10k.txt", "大容量文書 (10K行)"),
        (samples_dir / "11_complex_nested_5k.txt", "複雑ネスト (5K行)"),
        (samples_dir / "12_heavy_decoration_7k.txt", "重装飾 (7K行)")
    ]
    
    all_results = []
    
    for file_path, test_name in test_files:
        results = test_sample_file(file_path, test_name)
        results["test_name"] = test_name
        results["file_path"] = str(file_path)
        all_results.append(results)
    
    # 総合評価
    print(f"\n🎯 Issue #699 総合評価")
    print("=" * 60)
    
    successful_tests = [r for r in all_results if "improvements" in r]
    
    if successful_tests:
        avg_speed_improvement = sum(r["improvements"]["speed_ratio"] for r in successful_tests) / len(successful_tests)
        avg_memory_improvement = sum(r["improvements"]["memory_ratio"] for r in successful_tests) / len(successful_tests)
        
        print(f"✅ テスト成功: {len(successful_tests)}/{len(all_results)} ファイル")
        print(f"📈 平均速度向上: {avg_speed_improvement:.1f}x")
        print(f"🧠 平均メモリ効率: {avg_memory_improvement:.1f}x")
        
        # Issue #699要求の検証
        print(f"\n🔍 Issue #699要求検証:")
        large_file_results = [r for r in successful_tests if "10k" in r["file_path"].lower()]
        if large_file_results:
            large_result = large_file_results[0]
            speed_ok = large_result["improvements"]["speed_ratio"] >= 10  # 10倍以上の高速化
            memory_ok = large_result["improvements"]["memory_ratio"] >= 2  # 2倍以上のメモリ効率
            
            print(f"  大容量処理高速化: {'✅ 達成' if speed_ok else '❌ 未達成'}")
            print(f"  メモリ効率改善: {'✅ 達成' if memory_ok else '❌ 未達成'}")
        
        # 詳細レポート
        if args.detailed:
            print(f"\n📋 詳細結果:")
            for result in all_results:
                print(f"\n{result['test_name']}:")
                if "file_info" in result:
                    print(f"  ファイル: {result['file_info']['line_count']:,}行, {result['file_info']['size_mb']:.1f}MB")
                if "improvements" in result:
                    print(f"  改善: 速度{result['improvements']['speed_ratio']:.1f}x, メモリ{result['improvements']['memory_ratio']:.1f}x")
    else:
        print("❌ 全テストでエラーが発生しました")
        for result in all_results:
            if "traditional" in result and "error" in result["traditional"]:
                print(f"  {result['test_name']}: {result['traditional']['error']}")
    
    print(f"\n🏁 Issue #699 パフォーマンステスト完了")
    return 0

if __name__ == "__main__":
    exit(main())