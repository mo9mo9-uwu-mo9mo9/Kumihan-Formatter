#!/usr/bin/env python3
"""
300K行ファイルの完全処理テスト実行
全処理を確実に完了させる
"""

import sys
import time
import psutil
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def complete_300k_test():
    """300K行ファイルの完全処理テスト"""
    
    print("🚀 300K行ファイル完全処理テスト開始")
    print("=" * 60)
    
    # 300K行ファイル
    file_path = project_root / "samples" / "ultra_large" / "41_ultra_large_300k.txt"
    
    if not file_path.exists():
        print(f"❌ ファイルが存在しません: {file_path}")
        return False
    
    # ファイル情報
    file_size_mb = file_path.stat().st_size / 1024 / 1024
    with open(file_path, 'rb') as f:
        line_count = sum(1 for _ in f)
    
    print(f"📄 ファイル情報:")
    print(f"  ファイル: {file_path.name}")
    print(f"  サイズ: {file_size_mb:.1f} MB")
    print(f"  行数: {line_count:,} 行")
    
    # メモリ監視開始
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    print(f"\n⚡ 最適化パーサーで完全処理開始...")
    print(f"初期メモリ: {initial_memory:.1f} MB")
    
    try:
        from kumihan_formatter.parser import Parser
        
        start_time = time.time()
        
        # ファイル読み込み
        print("📖 ファイル読み込み中...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        read_time = time.time() - start_time
        current_memory = process.memory_info().rss / 1024 / 1024
        print(f"  読み込み完了: {read_time:.1f}秒")
        print(f"  メモリ使用量: {current_memory:.1f} MB")
        
        # パーサー初期化
        print("🔧 パーサー初期化中...")
        parser = Parser()
        
        # 最適化解析実行
        print("⚡ 最適化解析実行中...")
        parse_start = time.time()
        
        nodes = parser.parse_optimized(content)
        
        parse_time = time.time() - parse_start
        total_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"\n🎉 300K行ファイル完全処理成功！")
        print("=" * 60)
        print(f"📊 処理結果:")
        print(f"  総処理時間: {total_time:.1f}秒 ({total_time/60:.1f}分)")
        print(f"  解析時間: {parse_time:.1f}秒")
        print(f"  生成ノード数: {len(nodes):,}")
        print(f"  エラー数: {len(parser.get_errors())}")
        print(f"  最終メモリ: {final_memory:.1f} MB")
        print(f"  メモリ増加: {final_memory - initial_memory:.1f} MB")
        print(f"  処理速度: {line_count / parse_time:.0f} 行/秒")
        
        # パフォーマンス評価
        print(f"\n🎯 パフォーマンス評価:")
        success_criteria = []
        
        # 10分以内処理
        if total_time <= 600:
            print(f"  ✅ 10分以内処理: {total_time/60:.1f}分")
            success_criteria.append(True)
        else:
            print(f"  ❌ 10分以内処理: {total_time/60:.1f}分")
            success_criteria.append(False)
        
        # メモリ効率
        memory_per_line = (final_memory - initial_memory) / line_count * 1000
        if memory_per_line < 1.0:  # 1KB/行以下
            print(f"  ✅ メモリ効率: {memory_per_line:.3f} KB/行")
            success_criteria.append(True)
        else:
            print(f"  ⚠️  メモリ効率: {memory_per_line:.3f} KB/行")
            success_criteria.append(False)
        
        # エラーゼロ
        if len(parser.get_errors()) == 0:
            print(f"  ✅ エラーゼロ: 完全処理")
            success_criteria.append(True)
        else:
            print(f"  ⚠️  エラー発生: {len(parser.get_errors())}件")
            success_criteria.append(False)
        
        # 総合判定
        success_rate = (sum(success_criteria) / len(success_criteria)) * 100
        print(f"\n🏆 総合評価: {success_rate:.0f}%")
        
        if success_rate >= 66:  # 2/3以上で合格
            print("🎉 300K行ファイル処理テスト合格！")
            return True
        else:
            print("⚠️  300K行ファイル処理に改善余地があります")
            return False
        
    except Exception as e:
        print(f"❌ 処理エラー: {str(e)}")
        return False

def main():
    """メイン実行"""
    
    success = complete_300k_test()
    
    print(f"\n🏁 300K行ファイル完全処理テスト完了")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())