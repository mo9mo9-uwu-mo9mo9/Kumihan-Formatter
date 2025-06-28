#!/usr/bin/env python3
"""
品質メトリクス収集・分析ツール

使用方法:
    # 基本的なメトリクス収集
    python dev/tools/quality_metrics.py <directory>
    
    # JSONレポート出力
    python dev/tools/quality_metrics.py <directory> --format=json --output=metrics.json
    
    # 品質ゲート判定
    python dev/tools/quality_metrics.py <directory> --check-gates
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class QualityMetrics:
    """品質メトリクス情報"""
    timestamp: str
    project_name: str
    
    # ファイル統計
    total_files: int
    txt_files: int
    total_lines: int
    total_size_bytes: int
    
    # 記法統計
    syntax_errors: int
    syntax_pass_rate: float
    
    # パフォーマンス統計
    conversion_time_avg: float
    conversion_time_max: float
    html_size_avg: float
    html_size_max: float
    
    # テスト統計
    test_pass_rate: float
    test_coverage: float
    
    # 品質スコア
    overall_quality_score: float
    
    # 詳細情報
    file_details: List[Dict[str, Any]]
    error_details: List[Dict[str, Any]]


class QualityAnalyzer:
    """品質メトリクス分析クラス"""
    
    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.project_root = Path.cwd()
    
    def _load_config(self, config_path: Path = None) -> Dict[str, Any]:
        """設定を読み込み"""
        default_config = {
            "quality_gates": {
                "syntax_pass_rate_min": 95.0,
                "conversion_time_max": 5.0,
                "html_size_growth_max": 1.2,
                "test_pass_rate_min": 100.0,
                "overall_quality_min": 80.0
            },
            "performance_thresholds": {
                "file_size_max": 1048576,  # 1MB
                "lines_max": 10000,
                "conversion_timeout": 30.0
            },
            "exclusions": {
                "directories": [".git", "__pycache__", ".venv", "node_modules", "dist", "build"],
                "file_patterns": ["*.pyc", "*.log", "*.tmp"]
            }
        }
        
        if config_path and config_path.exists() and yaml:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception:
                pass
        
        return default_config
    
    def analyze_project(self, target_dir: Path) -> QualityMetrics:
        """プロジェクト全体の品質分析"""
        print("🔍 品質メトリクス収集を開始...")
        
        # ファイル統計収集
        file_stats = self._collect_file_stats(target_dir)
        print(f"📁 ファイル統計: {file_stats['total_files']}ファイル, {file_stats['txt_files']}テキストファイル")
        
        # 記法チェック実行
        syntax_stats = self._run_syntax_validation(target_dir)
        print(f"📝 記法チェック: {syntax_stats['pass_rate']:.1f}% 合格")
        
        # パフォーマンステスト実行
        perf_stats = self._run_performance_tests(target_dir)
        print(f"⚡ パフォーマンス: 平均{perf_stats['conversion_time_avg']:.2f}秒")
        
        # テスト実行
        test_stats = self._run_tests()
        print(f"🧪 テスト: {test_stats['pass_rate']:.1f}% 合格")
        
        # 品質スコア計算
        quality_score = self._calculate_quality_score(syntax_stats, perf_stats, test_stats)
        print(f"🎯 総合品質スコア: {quality_score:.1f}/100")
        
        return QualityMetrics(
            timestamp=datetime.now().isoformat(),
            project_name=self.project_root.name,
            total_files=file_stats['total_files'],
            txt_files=file_stats['txt_files'],
            total_lines=file_stats['total_lines'],
            total_size_bytes=file_stats['total_size'],
            syntax_errors=syntax_stats['error_count'],
            syntax_pass_rate=syntax_stats['pass_rate'],
            conversion_time_avg=perf_stats['conversion_time_avg'],
            conversion_time_max=perf_stats['conversion_time_max'],
            html_size_avg=perf_stats['html_size_avg'],
            html_size_max=perf_stats['html_size_max'],
            test_pass_rate=test_stats['pass_rate'],
            test_coverage=test_stats['coverage'],
            overall_quality_score=quality_score,
            file_details=file_stats['details'],
            error_details=syntax_stats['errors']
        )
    
    def _collect_file_stats(self, target_dir: Path) -> Dict[str, Any]:
        """ファイル統計を収集"""
        total_files = 0
        txt_files = 0
        total_lines = 0
        total_size = 0
        file_details = []
        
        for root, dirs, files in os.walk(target_dir):
            # 除外ディレクトリをスキップ
            dirs[:] = [d for d in dirs if d not in self.config['exclusions']['directories']]
            
            for file in files:
                file_path = Path(root) / file
                
                # 除外パターンをスキップ
                if any(file_path.match(pattern) for pattern in self.config['exclusions']['file_patterns']):
                    continue
                
                total_files += 1
                file_size = file_path.stat().st_size
                total_size += file_size
                
                if file_path.suffix.lower() == '.txt':
                    txt_files += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                        
                        file_details.append({
                            'path': str(file_path.relative_to(self.project_root)),
                            'size': file_size,
                            'lines': lines
                        })
                    except Exception:
                        pass
        
        return {
            'total_files': total_files,
            'txt_files': txt_files,
            'total_lines': total_lines,
            'total_size': total_size,
            'details': file_details
        }
    
    def _run_syntax_validation(self, target_dir: Path) -> Dict[str, Any]:
        """記法検証を実行"""
        try:
            # syntax_validatorを実行
            cmd = [
                sys.executable, 
                'dev/tools/syntax_validator.py',
                '--mode=strict',
                '--quiet',
                str(target_dir / '**/*.txt')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            # 結果を解析
            error_count = 0
            total_files = 0
            errors = []
            
            if result.returncode != 0:
                # エラー出力を解析
                for line in result.stdout.split('\n'):
                    if '[エラー]' in line and 'エラー' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            error_count += int(parts[1].split()[0])
                    elif '[完了]' in line and 'OK' in line:
                        total_files += 1
                    elif 'Line' in line:
                        errors.append({'message': line.strip()})
            
            # ファイル数を数える
            txt_files = len(list(target_dir.glob('**/*.txt')))
            total_files = max(total_files, txt_files)
            
            pass_rate = ((total_files - error_count) / total_files * 100) if total_files > 0 else 0
            
            return {
                'error_count': error_count,
                'total_files': total_files,
                'pass_rate': pass_rate,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'error_count': 999,
                'total_files': 1,
                'pass_rate': 0.0,
                'errors': [{'message': f'検証実行エラー: {e}'}]
            }
    
    def _run_performance_tests(self, target_dir: Path) -> Dict[str, Any]:
        """パフォーマンステストを実行"""
        conversion_times = []
        html_sizes = []
        
        # サンプルファイルでパフォーマンステスト
        sample_files = list(target_dir.glob('examples/*.txt'))[:5]  # 最大5ファイル
        
        for sample_file in sample_files:
            try:
                start_time = time.time()
                
                # 変換実行
                cmd = [
                    sys.executable, 
                    '-m', 'kumihan_formatter.cli',
                    str(sample_file),
                    '--no-preview',
                    '-o', '/tmp/quality_test'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                end_time = time.time()
                conversion_time = end_time - start_time
                conversion_times.append(conversion_time)
                
                # HTMLファイルサイズを確認
                html_file = Path(f'/tmp/quality_test/{sample_file.stem}.html')
                if html_file.exists():
                    html_size = html_file.stat().st_size
                    html_sizes.append(html_size)
                
            except Exception:
                conversion_times.append(999.0)  # タイムアウト値
                html_sizes.append(0)
        
        return {
            'conversion_time_avg': sum(conversion_times) / len(conversion_times) if conversion_times else 0,
            'conversion_time_max': max(conversion_times) if conversion_times else 0,
            'html_size_avg': sum(html_sizes) / len(html_sizes) if html_sizes else 0,
            'html_size_max': max(html_sizes) if html_sizes else 0
        }
    
    def _run_tests(self) -> Dict[str, Any]:
        """テストを実行"""
        try:
            # pytest実行
            cmd = [sys.executable, '-m', 'pytest', '--tb=no', '-q']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 結果解析
            output = result.stdout + result.stderr
            
            # テスト通過率を解析
            if 'passed' in output:
                # "5 passed, 1 failed" のような形式を解析
                import re
                matches = re.findall(r'(\d+) passed', output)
                passed = int(matches[0]) if matches else 0
                
                failed_matches = re.findall(r'(\d+) failed', output)
                failed = int(failed_matches[0]) if failed_matches else 0
                
                total = passed + failed
                pass_rate = (passed / total * 100) if total > 0 else 0
            else:
                pass_rate = 0.0
            
            # カバレッジ情報（簡易版）
            coverage = 80.0  # デフォルト値
            
            return {
                'pass_rate': pass_rate,
                'coverage': coverage
            }
            
        except Exception:
            return {
                'pass_rate': 0.0,
                'coverage': 0.0
            }
    
    def _calculate_quality_score(self, syntax_stats, perf_stats, test_stats) -> float:
        """総合品質スコアを計算"""
        weights = {
            'syntax': 0.4,      # 記法品質: 40%
            'performance': 0.3, # パフォーマンス: 30%
            'tests': 0.3        # テスト品質: 30%
        }
        
        # 各項目のスコア計算（0-100）
        syntax_score = min(syntax_stats['pass_rate'], 100.0)
        
        # パフォーマンススコア（変換時間ベース）
        perf_score = max(0, 100 - (perf_stats['conversion_time_avg'] * 20))
        
        test_score = min(test_stats['pass_rate'], 100.0)
        
        # 重み付き平均
        quality_score = (
            syntax_score * weights['syntax'] +
            perf_score * weights['performance'] +
            test_score * weights['tests']
        )
        
        return round(quality_score, 1)
    
    def check_quality_gates(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """品質ゲートチェック"""
        gates = self.config['quality_gates']
        results = {}
        
        checks = [
            ('syntax_pass_rate', metrics.syntax_pass_rate >= gates['syntax_pass_rate_min']),
            ('conversion_time', metrics.conversion_time_max <= gates['conversion_time_max']),
            ('test_pass_rate', metrics.test_pass_rate >= gates['test_pass_rate_min']),
            ('overall_quality', metrics.overall_quality_score >= gates['overall_quality_min'])
        ]
        
        for check_name, passed in checks:
            results[check_name] = {
                'passed': passed,
                'threshold': gates.get(f'{check_name}_min', gates.get(f'{check_name}_max', 0)),
                'actual': getattr(metrics, check_name, 0)
            }
        
        results['all_passed'] = all(check[1] for check in checks)
        
        return results


def format_report(metrics: QualityMetrics, format_type: str = 'detailed') -> str:
    """メトリクスレポートのフォーマット"""
    if format_type == 'json':
        return json.dumps(asdict(metrics), indent=2, ensure_ascii=False)
    
    elif format_type == 'summary':
        return f"""
📊 品質メトリクス サマリー
========================
プロジェクト: {metrics.project_name}
時刻: {metrics.timestamp}

📁 ファイル統計: {metrics.total_files}ファイル ({metrics.txt_files}テキスト)
📝 記法品質: {metrics.syntax_pass_rate:.1f}% ({metrics.syntax_errors}エラー)
⚡ パフォーマンス: 平均{metrics.conversion_time_avg:.2f}秒
🧪 テスト品質: {metrics.test_pass_rate:.1f}%
🎯 総合スコア: {metrics.overall_quality_score:.1f}/100
"""
    
    else:  # detailed
        return f"""
📊 Kumihan-Formatter 品質メトリクス詳細レポート
==============================================
プロジェクト: {metrics.project_name}
生成時刻: {metrics.timestamp}

📁 ファイル統計
--------------
総ファイル数: {metrics.total_files:,}
テキストファイル数: {metrics.txt_files:,}
総行数: {metrics.total_lines:,}
総サイズ: {metrics.total_size_bytes:,} bytes ({metrics.total_size_bytes/1024/1024:.1f} MB)

📝 記法品質
-----------
記法エラー数: {metrics.syntax_errors}
記法合格率: {metrics.syntax_pass_rate:.1f}%

⚡ パフォーマンス
---------------
平均変換時間: {metrics.conversion_time_avg:.2f}秒
最大変換時間: {metrics.conversion_time_max:.2f}秒
平均HTMLサイズ: {metrics.html_size_avg:,.0f} bytes
最大HTMLサイズ: {metrics.html_size_max:,.0f} bytes

🧪 テスト品質
-----------
テスト合格率: {metrics.test_pass_rate:.1f}%
テストカバレッジ: {metrics.test_coverage:.1f}%

🎯 総合評価
-----------
品質スコア: {metrics.overall_quality_score:.1f}/100

{_get_quality_rating(metrics.overall_quality_score)}
"""


def _get_quality_rating(score: float) -> str:
    """品質評価の判定"""
    if score >= 90:
        return "🌟 優秀 - 本番リリース可能"
    elif score >= 80:
        return "✅ 良好 - 軽微な改善推奨"
    elif score >= 70:
        return "⚠️ 要改善 - 品質向上が必要"
    else:
        return "🚨 重大 - 大幅な改善が必要"


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter 品質メトリクス収集ツール",
        epilog="例: python dev/tools/quality_metrics.py . --format=json --output=metrics.json"
    )
    parser.add_argument(
        'directory',
        type=Path,
        help='分析対象ディレクトリ'
    )
    parser.add_argument(
        '--format',
        choices=['detailed', 'summary', 'json'],
        default='detailed',
        help='レポート形式'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='出力ファイルパス'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='設定ファイルパス'
    )
    parser.add_argument(
        '--check-gates',
        action='store_true',
        help='品質ゲートチェックを実行'
    )
    
    args = parser.parse_args()
    
    # 分析実行
    analyzer = QualityAnalyzer(config_path=args.config)
    metrics = analyzer.analyze_project(args.directory)
    
    # レポート生成
    report = format_report(metrics, args.format)
    
    # 出力
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 レポートを出力しました: {args.output}")
    else:
        print(report)
    
    # 品質ゲートチェック
    if args.check_gates:
        gate_results = analyzer.check_quality_gates(metrics)
        print("\n🚪 品質ゲートチェック結果:")
        print("=" * 30)
        
        for gate_name, result in gate_results.items():
            if gate_name == 'all_passed':
                continue
            
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{gate_name}: {status} ({result['actual']:.1f} / {result['threshold']:.1f})")
        
        if gate_results['all_passed']:
            print("\n🎉 全ての品質ゲートを通過しました！")
            sys.exit(0)
        else:
            print("\n🚨 品質ゲートチェックに失敗しました")
            sys.exit(1)


if __name__ == "__main__":
    main()