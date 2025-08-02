#!/usr/bin/env python3
"""
Kumihan-Formatter パフォーマンスベンチマークスクリプト
Issue #727 - パフォーマンス最適化の効果測定

使用方法:
    python scripts/performance_benchmark.py
    python scripts/performance_benchmark.py --test-size large
    python scripts/performance_benchmark.py --output-report benchmark_results.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kumihan_formatter.core.utilities.performance_metrics import PerformanceBenchmark
from kumihan_formatter.core.utilities.logger import get_logger


def main():
    """メインエントリーポイント"""
    
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter パフォーマンスベンチマーク"
    )
    parser.add_argument(
        "--test-size",
        choices=["small", "medium", "large", "extra_large", "all"],
        default="all",
        help="テストサイズの指定"
    )
    parser.add_argument(
        "--output-report",
        type=str,
        help="レポート出力ファイルパス (JSON形式)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細ログ出力"
    )
    
    args = parser.parse_args()
    
    # ロガー設定
    logger = get_logger(__name__)
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🚀 Kumihan-Formatter パフォーマンスベンチマーク開始")
    
    try:
        # ベンチマーク実行
        benchmark = PerformanceBenchmark()
        
        if args.test_size == "all":
            results = benchmark.run_comprehensive_benchmark()
        else:
            # 個別テストサイズの場合の実装は省略（簡略化）
            results = benchmark.run_comprehensive_benchmark()
        
        # レポート生成
        report_text = benchmark.generate_benchmark_report(results)
        print("\n" + report_text)
        
        # 結果保存
        if args.output_report:
            output_path = Path(args.output_report)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 ベンチマーク結果を保存: {output_path}")
        
        # Issue #727 目標達成チェック
        goals = results.get("goal_assessment", {}).get("goals", {})
        achieved_count = sum(1 for achieved in goals.values() if achieved)
        total_count = len(goals)
        
        if achieved_count == total_count:
            logger.info("🎉 全ての性能目標を達成しました！")
            return 0
        elif achieved_count >= total_count * 0.8:
            logger.info(f"✅ 性能目標の大部分を達成 ({achieved_count}/{total_count})")
            return 0
        else:
            logger.warning(f"⚠️ 性能目標の達成率が低いです ({achieved_count}/{total_count})")
            return 1
            
    except Exception as e:
        logger.error(f"❌ ベンチマーク実行中にエラーが発生: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())