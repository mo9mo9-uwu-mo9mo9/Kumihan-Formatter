#!/usr/bin/env python3
"""
品質監視システム - Issue #1239: 品質保証システム再構築
コード品質・テスト品質・パフォーマンス指標の総合監視
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class QualityMonitor:
    """品質監視システム"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.src_dir = self.project_dir / "kumihan_formatter"
        self.metrics_dir = self.project_dir / "tmp" / "quality_metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # 品質基準（Issue #1239目標値）
        self.targets = {
            'mypy_errors': 150,    # 現在186から段階的削減
            'import_count': 300,   # 現在423から削減
            'test_coverage': 10,   # 現在6%から段階的向上
            'build_time': 60,      # 秒
            'type_coverage': 95    # %
        }
    
    def collect_code_metrics(self) -> Dict:
        """コード品質メトリクス収集"""
        print("📊 コード品質メトリクス収集中...")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'git_commit': self._get_git_commit(),
            'files': self._count_files(),
            'lines_of_code': self._count_lines_of_code(),
            'imports': self._analyze_imports(),
            'mypy_results': self._run_mypy_analysis(),
            'complexity': self._analyze_complexity()
        }
        
        return metrics
    
    def collect_test_metrics(self) -> Dict:
        """テスト品質メトリクス収集"""
        print("🧪 テスト品質メトリクス収集中...")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'coverage': self._get_test_coverage(),
            'test_count': self._count_tests(),
            'test_duration': self._measure_test_duration(),
            'test_results': self._run_test_analysis()
        }
        
        return metrics
    
    def collect_performance_metrics(self) -> Dict:
        """パフォーマンスメトリクス収集"""
        print("⚡ パフォーマンスメトリクス収集中...")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'build_time': self._measure_build_time(),
            'lint_time': self._measure_lint_time(),
            'memory_usage': self._estimate_memory_usage(),
            'file_sizes': self._analyze_file_sizes()
        }
        
        return metrics
    
    def generate_quality_report(self) -> Dict:
        """総合品質レポート生成"""
        print("📋 総合品質レポート生成中...")
        
        code_metrics = self.collect_code_metrics()
        test_metrics = self.collect_test_metrics()
        perf_metrics = self.collect_performance_metrics()
        
        # 品質スコア計算
        quality_score = self._calculate_quality_score(
            code_metrics, test_metrics, perf_metrics
        )
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'quality_score': quality_score,
            'targets': self.targets,
            'metrics': {
                'code': code_metrics,
                'test': test_metrics,
                'performance': perf_metrics
            },
            'recommendations': self._generate_recommendations(
                code_metrics, test_metrics, perf_metrics
            )
        }
        
        # レポート保存
        report_path = self.metrics_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ レポート保存: {report_path}")
        return report
    
    def _get_git_commit(self) -> Optional[str]:
        """現在のGitコミットハッシュ取得"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def _count_files(self) -> Dict:
        """ファイル数統計"""
        py_files = list(self.src_dir.glob("**/*.py"))
        test_files = list(self.project_dir.glob("tests/**/*.py"))
        
        return {
            'python_files': len(py_files),
            'test_files': len(test_files),
            'total_files': len(py_files) + len(test_files)
        }
    
    def _count_lines_of_code(self) -> Dict:
        """コード行数統計"""
        total_lines = 0
        code_lines = 0
        
        for py_file in self.src_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    code_lines += len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            except Exception:
                continue
        
        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_ratio': ((total_lines - code_lines) / total_lines * 100) if total_lines > 0 else 0
        }
    
    def _analyze_imports(self) -> Dict:
        """import分析"""
        try:
            result = subprocess.run(['grep', '-r', '^import\\|^from', str(self.src_dir), '--include=*.py'], 
                                  capture_output=True, text=True)
            import_lines = result.stdout.count('\n') if result.returncode == 0 else 0
            
            py_files = len(list(self.src_dir.glob("**/*.py")))
            avg_imports = import_lines / py_files if py_files > 0 else 0
            
            return {
                'total_imports': import_lines,
                'avg_imports_per_file': round(avg_imports, 1),
                'target_compliance': import_lines <= self.targets['import_count']
            }
        except Exception:
            return {'total_imports': 0, 'avg_imports_per_file': 0, 'target_compliance': True}
    
    def _run_mypy_analysis(self) -> Dict:
        """mypy解析実行"""
        try:
            result = subprocess.run(['python3', '-m', 'mypy', str(self.src_dir), '--ignore-missing-imports'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            
            error_count = result.stderr.count('error:') + result.stdout.count('error:')
            
            return {
                'error_count': error_count,
                'target_compliance': error_count <= self.targets['mypy_errors'],
                'improvement_needed': max(0, error_count - self.targets['mypy_errors'])
            }
        except Exception:
            return {'error_count': 999, 'target_compliance': False, 'improvement_needed': 999}
    
    def _analyze_complexity(self) -> Dict:
        """複雑度分析（簡易版）"""
        total_classes = 0
        total_functions = 0
        
        for py_file in self.src_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_classes += content.count('class ')
                    total_functions += content.count('def ')
            except Exception:
                continue
        
        return {
            'total_classes': total_classes,
            'total_functions': total_functions,
            'avg_functions_per_file': round(total_functions / max(1, len(list(self.src_dir.glob("**/*.py")))), 1)
        }
    
    def _get_test_coverage(self) -> Dict:
        """テストカバレッジ取得"""
        try:
            result = subprocess.run(['python3', '-m', 'pytest', '--cov=kumihan_formatter', '--cov-report=term-missing'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            
            # カバレッジパーセンテージを抽出（簡易実装）
            lines = result.stdout.split('\n')
            coverage_line = None
            for line in lines:
                if 'TOTAL' in line and '%' in line:
                    coverage_line = line
                    break
            
            if coverage_line:
                # "TOTAL    123    45    67%"のような形式から67を抽出
                parts = coverage_line.split()
                for part in parts:
                    if '%' in part:
                        coverage = int(part.replace('%', ''))
                        return {
                            'coverage_percent': coverage,
                            'target_compliance': coverage >= self.targets['test_coverage']
                        }
            
            return {'coverage_percent': 0, 'target_compliance': False}
        except Exception:
            return {'coverage_percent': 0, 'target_compliance': False}
    
    def _count_tests(self) -> Dict:
        """テスト数統計"""
        test_files = list(self.project_dir.glob("tests/**/*.py"))
        
        total_tests = 0
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_tests += content.count('def test_')
            except Exception:
                continue
        
        return {
            'test_files': len(test_files),
            'total_tests': total_tests,
            'avg_tests_per_file': round(total_tests / max(1, len(test_files)), 1)
        }
    
    def _measure_test_duration(self) -> Dict:
        """テスト実行時間測定"""
        try:
            start_time = time.time()
            result = subprocess.run(['python3', '-m', 'pytest', 'tests/unit', '-q'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            duration = time.time() - start_time
            
            return {
                'duration_seconds': round(duration, 2),
                'performance_rating': 'fast' if duration < 10 else 'moderate' if duration < 30 else 'slow'
            }
        except Exception:
            return {'duration_seconds': 999, 'performance_rating': 'unknown'}
    
    def _run_test_analysis(self) -> Dict:
        """テスト実行結果分析"""
        try:
            result = subprocess.run(['python3', '-m', 'pytest', 'tests/', '--tb=no', '-q'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            
            output = result.stdout + result.stderr
            
            # 簡易パース
            passed = output.count(' PASSED') if 'PASSED' in output else 0
            failed = output.count(' FAILED') if 'FAILED' in output else 0
            skipped = output.count(' SKIPPED') if 'SKIPPED' in output else 0
            
            return {
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'success_rate': round((passed / max(1, passed + failed)) * 100, 1)
            }
        except Exception:
            return {'passed': 0, 'failed': 0, 'skipped': 0, 'success_rate': 0}
    
    def _measure_build_time(self) -> Dict:
        """ビルド時間測定"""
        try:
            start_time = time.time()
            result = subprocess.run(['make', 'lint'], capture_output=True, text=True, cwd=self.project_dir)
            duration = time.time() - start_time
            
            return {
                'duration_seconds': round(duration, 2),
                'target_compliance': duration <= self.targets['build_time']
            }
        except Exception:
            return {'duration_seconds': 999, 'target_compliance': False}
    
    def _measure_lint_time(self) -> Dict:
        """lint実行時間測定"""
        try:
            start_time = time.time()
            subprocess.run(['python3', '-m', 'black', '--check', str(self.src_dir)], 
                          capture_output=True, cwd=self.project_dir)
            black_time = time.time() - start_time
            
            start_time = time.time()
            subprocess.run(['python3', '-m', 'mypy', str(self.src_dir), '--ignore-missing-imports'], 
                          capture_output=True, cwd=self.project_dir)
            mypy_time = time.time() - start_time
            
            return {
                'black_time': round(black_time, 2),
                'mypy_time': round(mypy_time, 2),
                'total_time': round(black_time + mypy_time, 2)
            }
        except Exception:
            return {'black_time': 0, 'mypy_time': 0, 'total_time': 0}
    
    def _estimate_memory_usage(self) -> Dict:
        """メモリ使用量推定"""
        try:
            total_size = 0
            file_count = 0
            
            for py_file in self.src_dir.glob("**/*.py"):
                total_size += py_file.stat().st_size
                file_count += 1
            
            return {
                'source_size_kb': round(total_size / 1024, 1),
                'avg_file_size_kb': round((total_size / file_count) / 1024, 1) if file_count > 0 else 0
            }
        except Exception:
            return {'source_size_kb': 0, 'avg_file_size_kb': 0}
    
    def _analyze_file_sizes(self) -> Dict:
        """ファイルサイズ分析"""
        sizes = []
        large_files = []
        
        for py_file in self.src_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    line_count = len(f.readlines())
                    sizes.append(line_count)
                    
                    if line_count > 500:  # 500行を超える大きなファイル
                        large_files.append({
                            'file': str(py_file.relative_to(self.project_dir)),
                            'lines': line_count
                        })
            except Exception:
                continue
        
        return {
            'avg_file_size_lines': round(sum(sizes) / len(sizes), 1) if sizes else 0,
            'max_file_size_lines': max(sizes) if sizes else 0,
            'large_files_count': len(large_files),
            'large_files': large_files[:5]  # 上位5件
        }
    
    def _calculate_quality_score(self, code_metrics: Dict, test_metrics: Dict, perf_metrics: Dict) -> Dict:
        """品質スコア計算"""
        score = 0
        max_score = 0
        
        # コード品質スコア (40点満点)
        max_score += 40
        if code_metrics.get('mypy_results', {}).get('target_compliance', False):
            score += 20
        if code_metrics.get('imports', {}).get('target_compliance', False):
            score += 20
        
        # テスト品質スコア (40点満点)
        max_score += 40
        if test_metrics.get('coverage', {}).get('target_compliance', False):
            score += 20
        test_success_rate = test_metrics.get('test_results', {}).get('success_rate', 0)
        score += min(20, int(test_success_rate / 5))  # 100%で20点
        
        # パフォーマンススコア (20点満点)
        max_score += 20
        if perf_metrics.get('build_time', {}).get('target_compliance', False):
            score += 20
        
        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 1) if max_score > 0 else 0,
            'grade': self._get_grade(score / max_score * 100 if max_score > 0 else 0)
        }
    
    def _get_grade(self, percentage: float) -> str:
        """品質グレード判定"""
        if percentage >= 90: return 'A'
        elif percentage >= 80: return 'B'
        elif percentage >= 70: return 'C'
        elif percentage >= 60: return 'D'
        else: return 'F'
    
    def _generate_recommendations(self, code_metrics: Dict, test_metrics: Dict, perf_metrics: Dict) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []
        
        # コード品質推奨
        mypy_errors = code_metrics.get('mypy_results', {}).get('error_count', 0)
        if mypy_errors > self.targets['mypy_errors']:
            recommendations.append(f"mypy エラーを {mypy_errors - self.targets['mypy_errors']} 個削減してください")
        
        imports = code_metrics.get('imports', {}).get('total_imports', 0)
        if imports > self.targets['import_count']:
            recommendations.append(f"import文を {imports - self.targets['import_count']} 個削減してください")
        
        # テスト品質推奨
        coverage = test_metrics.get('coverage', {}).get('coverage_percent', 0)
        if coverage < self.targets['test_coverage']:
            recommendations.append(f"テストカバレッジを {self.targets['test_coverage'] - coverage}% 向上してください")
        
        # パフォーマンス推奨
        build_time = perf_metrics.get('build_time', {}).get('duration_seconds', 0)
        if build_time > self.targets['build_time']:
            recommendations.append(f"ビルド時間を {build_time - self.targets['build_time']} 秒短縮してください")
        
        if not recommendations:
            recommendations.append("すべての品質目標を達成しています！ 🎉")
        
        return recommendations
    
    def print_summary(self, report: Dict):
        """サマリー表示"""
        print("\n" + "=" * 60)
        print("🛡️ Kumihan-Formatter 品質監視レポート")
        print("=" * 60)
        
        quality_score = report['quality_score']
        print(f"📊 総合品質スコア: {quality_score['score']}/{quality_score['max_score']} ({quality_score['percentage']}%) - グレード{quality_score['grade']}")
        
        print("\n📋 主要指標:")
        code = report['metrics']['code']
        test = report['metrics']['test']
        perf = report['metrics']['performance']
        
        print(f"  🔍 mypy エラー: {code.get('mypy_results', {}).get('error_count', 'N/A')} (目標: ≤{self.targets['mypy_errors']})")
        print(f"  📦 import文: {code.get('imports', {}).get('total_imports', 'N/A')} (目標: ≤{self.targets['import_count']})")
        print(f"  🧪 テストカバレッジ: {test.get('coverage', {}).get('coverage_percent', 'N/A')}% (目標: ≥{self.targets['test_coverage']}%)")
        print(f"  ⚡ ビルド時間: {perf.get('build_time', {}).get('duration_seconds', 'N/A')}秒 (目標: ≤{self.targets['build_time']}秒)")
        
        print("\n💡 推奨改善事項:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📁 レポート保存先: tmp/quality_metrics/")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="品質監視システム")
    parser.add_argument('--code', action='store_true', help='コード品質メトリクスのみ収集')
    parser.add_argument('--test', action='store_true', help='テスト品質メトリクスのみ収集')
    parser.add_argument('--perf', action='store_true', help='パフォーマンスメトリクスのみ収集')
    parser.add_argument('--full', action='store_true', help='全メトリクス収集（デフォルト）')
    
    args = parser.parse_args()
    
    monitor = QualityMonitor()
    
    if args.code:
        metrics = monitor.collect_code_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    elif args.test:
        metrics = monitor.collect_test_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    elif args.perf:
        metrics = monitor.collect_performance_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:  # デフォルトは全体レポート
        report = monitor.generate_quality_report()
        monitor.print_summary(report)


if __name__ == "__main__":
    main()