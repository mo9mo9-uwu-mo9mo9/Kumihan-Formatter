#!/usr/bin/env python3
"""
大容量ファイル処理パフォーマンステスト
Issue #694対応 - ストリーミングパーサーの性能測定

目標:
- 1000行ファイル: 10秒以内
- メモリ使用量: 一定（ファイルサイズに依存しない）
- 10MBファイル対応
"""

import time
import tracemalloc
from pathlib import Path
import tempfile
import sys
from typing import Dict, Any

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from kumihan_formatter.parser import StreamingParser, Parser, parse_with_streaming
from kumihan_formatter.core.utilities.logger import get_logger


class PerformanceTestSuite:
    """パフォーマンステスト実行クラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.results = []
    
    def generate_test_file(self, line_count: int, content_type: str = "mixed") -> str:
        """テスト用ファイルを生成"""
        print(f"📝 テストファイル生成中: {line_count}行 ({content_type}形式)")
        
        content_lines = []
        
        if content_type == "simple":
            # シンプルなテキスト
            for i in range(line_count):
                content_lines.append(f"これは{i+1}行目のテキストです。")
        
        elif content_type == "mixed":
            # 記法が混在したテキスト
            for i in range(line_count):
                line_type = i % 10
                if line_type == 0:
                    content_lines.append(f"# 見出し{i//10 + 1} # 見出しです")
                elif line_type == 1:
                    content_lines.append(f"# 太字 # **重要な内容{i}**です")
                elif line_type == 2:
                    content_lines.append(f"- リスト項目{i}")
                elif line_type == 3:
                    content_lines.append(f"{i+1}. 順序付きリスト項目")
                elif line_type == 4:
                    content_lines.append(f"# ハイライト # この内容{i}は注目すべきです")
                elif line_type == 5:
                    content_lines.append("")  # 空行
                else:
                    content_lines.append(f"通常のテキスト行{i}。詳細な説明文章がここに続きます。")
        
        elif content_type == "complex":
            # 複雑な記法を多用したテキスト  
            for i in range(line_count):
                line_type = i % 20
                if line_type == 0:
                    content_lines.append(f"# 見出し1 # メインタイトル{i//20 + 1}")
                elif line_type == 1:
                    content_lines.append(f"# 見出し2 # サブタイトル{i}")
                elif line_type == 2:
                    content_lines.append(f"# 太字 イタリック 下線 # ***重要事項{i}***")
                elif line_type == 3:
                    content_lines.append(f"# ハイライト color:red # 警告{i}: 注意が必要です")
                elif line_type == 4:
                    content_lines.append(f"- ネストしたリスト項目{i}")
                elif line_type == 5:
                    content_lines.append(f"  - サブ項目{i}-1")
                elif line_type == 6:
                    content_lines.append(f"  - サブ項目{i}-2")
                elif line_type == 7:
                    content_lines.append(f"{i+1}. 順序付きリスト")
                elif line_type == 8:
                    content_lines.append(f"# 枠線 # 囲み内容{i}")
                elif line_type == 9:
                    content_lines.append(f"追加説明文{i}")
                elif line_type == 10:
                    content_lines.append("##")
                elif line_type == 11:
                    content_lines.append(f"# コード # `sample_code_{i}()`")
                elif line_type == 12:
                    content_lines.append(f"# 引用 # > 引用テキスト{i}")
                else:
                    content_lines.append(f"段落{i}: 長いテキスト内容がここに記述されます。この内容は複数行にわたって継続する場合があります。")
        
        return "\n".join(content_lines)
    
    def measure_memory_usage(self, func, *args, **kwargs) -> tuple[Any, float, float]:
        """メモリ使用量を測定しながら関数を実行"""
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        end_memory = tracemalloc.get_traced_memory()[0]
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        memory_used_mb = (peak_memory - start_memory) / 1024 / 1024
        execution_time = end_time - start_time
        
        return result, execution_time, memory_used_mb
    
    def test_parser_performance(self, test_content: str, parser_type: str, line_count: int) -> Dict[str, Any]:
        """パーサーのパフォーマンスをテスト"""
        print(f"🔬 {parser_type}パーサーテスト開始: {line_count}行")
        
        try:
            if parser_type == "streaming":
                def parse_func():
                    parser = StreamingParser()
                    return list(parser.parse_streaming_from_text(test_content))
            
            elif parser_type == "traditional":
                def parse_func():
                    parser = Parser()
                    return parser.parse(test_content)
            
            elif parser_type == "auto":
                def parse_func():
                    return parse_with_streaming(test_content)
            
            else:
                raise ValueError(f"Unknown parser type: {parser_type}")
            
            result, execution_time, memory_used = self.measure_memory_usage(parse_func)
            
            # 結果集計
            test_result = {
                'parser_type': parser_type,
                'line_count': line_count,
                'execution_time': execution_time,
                'memory_used_mb': memory_used,
                'nodes_created': len(result) if result else 0,
                'lines_per_second': line_count / execution_time if execution_time > 0 else 0,
                'success': True,
                'error_message': None
            }
            
            print(f"✅ {parser_type}: {execution_time:.2f}s, {memory_used:.1f}MB, {len(result)}ノード")
            
        except Exception as e:
            test_result = {
                'parser_type': parser_type,
                'line_count': line_count,
                'execution_time': float('inf'),
                'memory_used_mb': 0,
                'nodes_created': 0,
                'lines_per_second': 0,
                'success': False,
                'error_message': str(e)
            }
            
            print(f"❌ {parser_type}: エラー - {e}")
        
        return test_result
    
    def run_comprehensive_test(self):
        """包括的なパフォーマンステスト実行"""
        print("🚀 大容量ファイル処理パフォーマンステスト開始")
        print("=" * 60)
        
        # テストケース定義
        test_cases = [
            (100, "simple"),      # 小規模
            (500, "mixed"),       # 中規模  
            (1000, "mixed"),      # 目標ケース
            (2000, "mixed"),      # 大規模
            (1000, "complex"),    # 複雑な記法
        ]
        
        parser_types = ["traditional", "streaming", "auto"]
        
        for line_count, content_type in test_cases:
            print(f"\n📊 テストケース: {line_count}行 ({content_type})")
            print("-" * 40)
            
            # テストファイル生成
            test_content = self.generate_test_file(line_count, content_type)
            file_size_mb = len(test_content.encode('utf-8')) / 1024 / 1024
            
            print(f"ファイルサイズ: {file_size_mb:.2f}MB")
            
            # 各パーサーでテスト実行
            case_results = []
            for parser_type in parser_types:
                result = self.test_parser_performance(test_content, parser_type, line_count)
                result['content_type'] = content_type
                result['file_size_mb'] = file_size_mb
                case_results.append(result)
                self.results.append(result)
            
            # ケース別結果サマリー
            self.print_case_summary(case_results)
    
    def print_case_summary(self, case_results: list):
        """テストケースの結果サマリーを表示"""
        print("\n📈 ケース結果サマリー:")
        
        for result in case_results:
            status = "✅" if result['success'] else "❌"
            if result['success']:
                print(f"  {status} {result['parser_type']:12}: "
                      f"{result['execution_time']:6.2f}s, "
                      f"{result['memory_used_mb']:6.1f}MB, "
                      f"{result['lines_per_second']:8.0f}行/秒")
            else:
                print(f"  {status} {result['parser_type']:12}: エラー - {result['error_message']}")
    
    def print_final_summary(self):
        """最終結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("🎯 最終テスト結果サマリー")
        print("=" * 60)
        
        # 目標達成状況チェック
        target_case = next((r for r in self.results 
                           if r['line_count'] == 1000 and r['parser_type'] == 'streaming'), None)
        
        if target_case and target_case['success']:
            target_time = target_case['execution_time']
            target_memory = target_case['memory_used_mb']
            
            print(f"\n🎯 目標達成状況:")
            print(f"  1000行ファイル処理時間: {target_time:.2f}s (目標: 10秒以内)")
            print(f"  メモリ使用量: {target_memory:.1f}MB")
            
            if target_time <= 10.0:
                print("  ✅ 処理時間目標達成！")
            else:
                print("  ❌ 処理時間目標未達成")
        
        # パーサー別平均性能
        print(f"\n📊 パーサー別平均性能:")
        for parser_type in ["traditional", "streaming", "auto"]:
            parser_results = [r for r in self.results 
                            if r['parser_type'] == parser_type and r['success']]
            
            if parser_results:
                avg_time = sum(r['execution_time'] for r in parser_results) / len(parser_results)
                avg_memory = sum(r['memory_used_mb'] for r in parser_results) / len(parser_results)
                avg_speed = sum(r['lines_per_second'] for r in parser_results) / len(parser_results)
                
                print(f"  {parser_type:12}: {avg_time:6.2f}s平均, "
                      f"{avg_memory:6.1f}MB平均, {avg_speed:8.0f}行/秒平均")
        
        # 最適な設定の推奨
        print(f"\n💡 推奨設定:")
        
        streaming_results = [r for r in self.results 
                           if r['parser_type'] == 'streaming' and r['success']]
        traditional_results = [r for r in self.results 
                             if r['parser_type'] == 'traditional' and r['success']]
        
        if streaming_results and traditional_results:
            streaming_avg = sum(r['execution_time'] for r in streaming_results) / len(streaming_results)
            traditional_avg = sum(r['execution_time'] for r in traditional_results) / len(traditional_results)
            
            if streaming_avg < traditional_avg:
                improvement = ((traditional_avg - streaming_avg) / traditional_avg) * 100
                print(f"  ストリーミングパーサーが{improvement:.1f}%高速です")
                print(f"  200行以上のファイルではストリーミングパーサーを推奨")
            else:
                print(f"  小規模ファイルでは従来パーサーが適しています")


def main():
    """メイン関数"""
    print("Issue #694 大容量ファイル処理パフォーマンステスト")
    print("Kumihan-Formatter ストリーミングパーサー性能検証")
    print("=" * 60)
    
    # テスト実行
    test_suite = PerformanceTestSuite()
    
    try:
        test_suite.run_comprehensive_test()
        test_suite.print_final_summary()
        
        print("\n🏁 パフォーマンステスト完了")
        print("詳細はログを確認してください。")
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())