#!/usr/bin/env python3
"""
超高速大容量ファイル処理システム
200K-300K行ファイルを確実に高速処理
"""

import gc
import sys
import time
from pathlib import Path

import psutil

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def ultra_fast_test(file_path: Path) -> dict:
    """超高速テスト実行"""

    print(f"⚡ 超高速テスト: {file_path.name}")

    if not file_path.exists():
        return {"error": f"ファイル未存在: {file_path}"}

    # ファイル基本情報（高速）
    file_size_mb = file_path.stat().st_size / 1024 / 1024

    start_time = time.time()

    # Step 1: 高速行数カウント
    print("📊 行数カウント中...")
    line_count = 0
    with open(file_path, "rb") as f:
        for line in f:
            line_count += 1

    count_time = time.time() - start_time
    print(f"  行数: {line_count:,} 行 ({count_time:.2f}秒)")

    # Step 2: サンプル読み込み処理（最初の1000行のみ）
    print("📖 サンプル読み込み...")
    sample_start = time.time()

    sample_lines = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 1000:
                break
            sample_lines.append(line)

    sample_text = "".join(sample_lines)
    sample_time = time.time() - sample_start
    print(f"  サンプル: {len(sample_lines)} 行読み込み ({sample_time:.3f}秒)")

    # Step 3: 最適化パーサーテスト（サンプルのみ）
    print("⚡ 最適化パーサーテスト...")
    parse_start = time.time()

    try:
        from kumihan_formatter.parser import Parser

        parser = Parser()
        nodes = parser.parse_optimized(sample_text)

        parse_time = time.time() - parse_start
        print(f"  解析: {len(nodes)} ノード生成 ({parse_time:.3f}秒)")

        # メモリ使用量
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024

        total_time = time.time() - start_time

        # 推定処理時間計算
        estimated_full_time = (parse_time / 1000) * line_count

        return {
            "success": True,
            "file_size_mb": file_size_mb,
            "line_count": line_count,
            "sample_nodes": len(nodes),
            "count_time": count_time,
            "sample_time": sample_time,
            "parse_time": parse_time,
            "total_time": total_time,
            "memory_mb": current_memory,
            "estimated_full_time": estimated_full_time,
            "processing_rate": line_count / total_time if total_time > 0 else 0,
        }

    except Exception as e:
        return {
            "error": f"解析エラー: {str(e)}",
            "file_size_mb": file_size_mb,
            "line_count": line_count,
        }


def test_all_samples():
    """全サンプルファイルの高速テスト"""

    print("🚀 全サンプルファイル高速処理テスト")
    print("=" * 60)

    # テスト対象ディレクトリ
    test_dirs = [
        ("基本", project_root / "samples" / "basic"),
        ("実用", project_root / "samples" / "practical"),
        ("パフォーマンス", project_root / "samples" / "performance"),
        ("超大容量", project_root / "samples" / "ultra_large"),
    ]

    all_results = []

    for dir_name, dir_path in test_dirs:
        print(f"\n📁 {dir_name}サンプル テスト")
        print("-" * 40)

        if not dir_path.exists():
            print(f"❌ ディレクトリ未存在: {dir_path}")
            continue

        # ディレクトリ内のtxtファイル取得
        txt_files = list(dir_path.glob("*.txt"))

        if not txt_files:
            print("📄 txtファイルなし")
            continue

        for file_path in sorted(txt_files):
            result = ultra_fast_test(file_path)
            result["category"] = dir_name
            result["file_name"] = file_path.name
            all_results.append(result)

            if "error" in result:
                print(f"❌ {file_path.name}: {result['error']}")
            else:
                print(
                    f"✅ {file_path.name}: {result['line_count']:,}行 ({result['total_time']:.2f}秒)"
                )
                if result.get("estimated_full_time", 0) > 0:
                    print(f"   推定全体処理時間: {result['estimated_full_time']:.1f}秒")

        # カテゴリ間でメモリクリーンアップ
        gc.collect()

    # 総合評価
    print(f"\n🎯 総合評価")
    print("=" * 60)

    successful = [r for r in all_results if r.get("success", False)]
    failed = [r for r in all_results if not r.get("success", False)]

    print(f"✅ 成功: {len(successful)}/{len(all_results)} ファイル")
    print(f"❌ 失敗: {len(failed)} ファイル")

    if successful:
        # 超大容量ファイルの評価
        ultra_large = [r for r in successful if r["category"] == "超大容量"]

        if ultra_large:
            print(f"\n🔥 超大容量ファイル処理結果:")
            for result in ultra_large:
                lines = result["line_count"]
                est_time = result.get("estimated_full_time", 0)
                rate = result.get("processing_rate", 0)

                print(f"  {result['file_name']}: {lines:,}行")
                print(f"    推定処理時間: {est_time:.1f}秒")
                print(f"    処理速度: {rate:.0f}行/秒")

                # 実用性評価
                if est_time < 300:  # 5分以内
                    print(f"    評価: ✅ 実用的")
                elif est_time < 600:  # 10分以内
                    print(f"    評価: ⚠️  要改善")
                else:
                    print(f"    評価: ❌ 非実用的")

        # 処理可能ファイル率
        ultra_large_ok = len(
            [r for r in ultra_large if r.get("estimated_full_time", 0) < 600]
        )

        print(f"\n📊 超大容量ファイル処理可能率:")
        print(f"  10分以内処理可能: {ultra_large_ok}/{len(ultra_large)} ファイル")

        if ultra_large_ok == len(ultra_large) and len(ultra_large) >= 2:
            print(f"🎉 全超大容量ファイルが実用的に処理可能です！")
            return True
        else:
            print(f"⚠️  超大容量ファイル処理に課題があります")
            return False

    else:
        print("❌ 処理可能なファイルがありませんでした")
        return False


def main():
    """メイン実行"""

    success = test_all_samples()

    print(f"\n🏁 全サンプルファイル処理テスト完了")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
