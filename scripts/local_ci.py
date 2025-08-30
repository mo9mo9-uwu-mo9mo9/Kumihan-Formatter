#!/usr/bin/env python3
"""
ローカルCI/CDシステム - Issue #1239: 品質保証システム再構築
GitHub Actions代替のローカル自動化システム
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class LocalCI:
    """ローカルCI/CDシステム"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.results_dir = self.project_dir / "tmp" / "ci_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # CI/CDパイプライン設定
        self.pipeline_config = {
            'stages': [
                {
                    'name': 'setup',
                    'commands': ['make setup'],
                    'timeout': 120,
                    'continue_on_failure': False
                },
                {
                    'name': 'quality-check',
                    'commands': ['make quality-check'],
                    'timeout': 300,
                    'continue_on_failure': False
                },
                {
                    'name': 'test-unit',
                    'commands': ['make test-unit'],
                    'timeout': 180,
                    'continue_on_failure': False
                },
                {
                    'name': 'quality-monitoring',
                    'commands': ['python3 scripts/quality_monitor.py'],
                    'timeout': 120,
                    'continue_on_failure': True
                },
                {
                    'name': 'security-scan',
                    'commands': ['python3 scripts/security_check.py || true'],
                    'timeout': 60,
                    'continue_on_failure': True
                }
            ]
        }
    
    def run_pipeline(self, stages: Optional[List[str]] = None) -> Dict:
        """CI/CDパイプライン実行"""
        print("🚀 ローカルCI/CDパイプライン開始")
        print("=" * 50)
        
        start_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_duration': 0,
            'stages': [],
            'overall_status': 'unknown',
            'summary': {}
        }
        
        stages_to_run = stages or [stage['name'] for stage in self.pipeline_config['stages']]
        
        for stage_config in self.pipeline_config['stages']:
            if stage_config['name'] not in stages_to_run:
                continue
            
            stage_result = self._run_stage(stage_config)
            results['stages'].append(stage_result)
            
            # ステージ失敗時の処理
            if stage_result['status'] == 'failed' and not stage_config.get('continue_on_failure', False):
                print(f"❌ パイプライン中断: {stage_config['name']} で失敗")
                results['overall_status'] = 'failed'
                break
        else:
            # 全ステージ完了
            failed_stages = [s for s in results['stages'] if s['status'] == 'failed']
            results['overall_status'] = 'failed' if failed_stages else 'passed'
        
        results['pipeline_duration'] = round(time.time() - start_time, 2)
        results['summary'] = self._generate_summary(results)
        
        # 結果保存
        self._save_results(results)
        self._print_summary(results)
        
        return results
    
    def _run_stage(self, stage_config: Dict) -> Dict:
        """個別ステージ実行"""
        stage_name = stage_config['name']
        print(f"\n🔄 ステージ実行中: {stage_name}")
        print("-" * 30)
        
        start_time = time.time()
        stage_result = {
            'name': stage_name,
            'status': 'unknown',
            'duration': 0,
            'commands': stage_config['commands'],
            'outputs': [],
            'errors': []
        }
        
        for command in stage_config['commands']:
            print(f"  実行中: {command}")
            
            try:
                result = subprocess.run(
                    command.split() if isinstance(command, str) else command,
                    capture_output=True,
                    text=True,
                    timeout=stage_config.get('timeout', 300),
                    cwd=self.project_dir
                )
                
                stage_result['outputs'].append({
                    'command': command,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                })
                
                if result.returncode != 0:
                    stage_result['errors'].append(f"Command failed: {command}")
                    if not stage_config.get('continue_on_failure', False):
                        stage_result['status'] = 'failed'
                        break
                
            except subprocess.TimeoutExpired:
                stage_result['errors'].append(f"Command timeout: {command}")
                stage_result['status'] = 'failed'
                break
            except Exception as e:
                stage_result['errors'].append(f"Command error: {command} - {str(e)}")
                stage_result['status'] = 'failed'
                break
        
        if stage_result['status'] == 'unknown':
            stage_result['status'] = 'passed' if not stage_result['errors'] else 'failed'
        
        stage_result['duration'] = round(time.time() - start_time, 2)
        
        status_icon = "✅" if stage_result['status'] == 'passed' else "❌"
        print(f"  {status_icon} {stage_name}: {stage_result['status']} ({stage_result['duration']}s)")
        
        return stage_result
    
    def _generate_summary(self, results: Dict) -> Dict:
        """結果サマリー生成"""
        stages = results['stages']
        passed_stages = [s for s in stages if s['status'] == 'passed']
        failed_stages = [s for s in stages if s['status'] == 'failed']
        
        return {
            'total_stages': len(stages),
            'passed_stages': len(passed_stages),
            'failed_stages': len(failed_stages),
            'success_rate': round((len(passed_stages) / len(stages)) * 100, 1) if stages else 0,
            'total_duration': results['pipeline_duration'],
            'avg_stage_duration': round(results['pipeline_duration'] / len(stages), 2) if stages else 0
        }
    
    def _save_results(self, results: Dict):
        """結果保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 詳細結果保存
        detailed_path = self.results_dir / f"ci_detailed_{timestamp}.json"
        with open(detailed_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # サマリー保存
        summary_path = self.results_dir / "ci_latest_summary.json"
        summary_data = {
            'timestamp': results['timestamp'],
            'overall_status': results['overall_status'],
            'pipeline_duration': results['pipeline_duration'],
            'summary': results['summary'],
            'stage_results': [
                {
                    'name': stage['name'],
                    'status': stage['status'],
                    'duration': stage['duration']
                } for stage in results['stages']
            ]
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 結果保存:")
        print(f"  詳細: {detailed_path}")
        print(f"  サマリー: {summary_path}")
    
    def _print_summary(self, results: Dict):
        """サマリー表示"""
        print("\n" + "=" * 60)
        print("🏁 ローカルCI/CDパイプライン完了")
        print("=" * 60)
        
        summary = results['summary']
        status_icon = "✅" if results['overall_status'] == 'passed' else "❌"
        
        print(f"{status_icon} 総合結果: {results['overall_status'].upper()}")
        print(f"⏱️  実行時間: {results['pipeline_duration']}秒")
        print(f"📊 ステージ結果: {summary['passed_stages']}/{summary['total_stages']} 成功 ({summary['success_rate']}%)")
        
        print("\n📋 ステージ別結果:")
        for stage in results['stages']:
            status_icon = "✅" if stage['status'] == 'passed' else "❌"
            print(f"  {status_icon} {stage['name']:<20} {stage['status']:<8} ({stage['duration']}s)")
            
            if stage['errors']:
                for error in stage['errors'][:3]:  # 最初の3つのエラーのみ表示
                    print(f"      ⚠️  {error}")
        
        # 推奨事項
        if results['overall_status'] == 'failed':
            print("\n💡 推奨対応:")
            failed_stages = [s for s in results['stages'] if s['status'] == 'failed']
            for stage in failed_stages:
                print(f"  - {stage['name']}: ログを確認して問題を修正してください")
        
        return results
    
    def generate_dashboard(self) -> str:
        """品質ダッシュボード生成"""
        print("📊 品質ダッシュボード生成中...")
        
        # 最新のCI結果取得
        summary_path = self.results_dir / "ci_latest_summary.json"
        ci_data = {}
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                ci_data = json.load(f)
        
        # 品質メトリクス取得
        quality_files = sorted((self.project_dir / "tmp" / "quality_metrics").glob("quality_report_*.json"))
        quality_data = {}
        if quality_files:
            with open(quality_files[-1], 'r', encoding='utf-8') as f:
                quality_data = json.load(f)
        
        # HTMLダッシュボード生成
        html_content = self._generate_dashboard_html(ci_data, quality_data)
        
        dashboard_path = self.project_dir / "tmp" / "dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ ダッシュボード生成完了: {dashboard_path}")
        return str(dashboard_path)
    
    def _generate_dashboard_html(self, ci_data: Dict, quality_data: Dict) -> str:
        """HTMLダッシュボード生成"""
        
        # CI/CD状況
        ci_status = ci_data.get('overall_status', 'unknown')
        ci_icon = "✅" if ci_status == 'passed' else "❌" if ci_status == 'failed' else "⚪"
        ci_duration = ci_data.get('pipeline_duration', 0)
        
        # 品質スコア
        quality_score = quality_data.get('quality_score', {})
        score_percentage = quality_score.get('percentage', 0)
        grade = quality_score.get('grade', 'N/A')
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan-Formatter 品質ダッシュボード</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #3498db; }}
        .status-good {{ color: #27ae60; }}
        .status-warning {{ color: #f39c12; }}
        .status-error {{ color: #e74c3c; }}
        .progress-bar {{ width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: #3498db; transition: width 0.3s; }}
        .timestamp {{ text-align: center; color: #7f8c8d; margin-top: 20px; }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Kumihan-Formatter 品質ダッシュボード</h1>
            <p>Issue #1239: 品質保証システム再構築</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-title">CI/CDステータス</div>
                <div class="metric-value {'status-good' if ci_status == 'passed' else 'status-error'}">{ci_icon} {ci_status.upper()}</div>
                <p>実行時間: {ci_duration}秒</p>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">総合品質スコア</div>
                <div class="metric-value">{score_percentage}% (Grade {grade})</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {score_percentage}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">mypy エラー数</div>
                <div class="metric-value">{quality_data.get('metrics', {}).get('code', {}).get('mypy_results', {}).get('error_count', 'N/A')}</div>
                <p>目標: ≤150</p>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">import文数</div>
                <div class="metric-value">{quality_data.get('metrics', {}).get('code', {}).get('imports', {}).get('total_imports', 'N/A')}</div>
                <p>目標: ≤300</p>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">テストカバレッジ</div>
                <div class="metric-value">{quality_data.get('metrics', {}).get('test', {}).get('coverage', {}).get('coverage_percent', 'N/A')}%</div>
                <p>目標: ≥10%</p>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">ビルド時間</div>
                <div class="metric-value">{quality_data.get('metrics', {}).get('performance', {}).get('build_time', {}).get('duration_seconds', 'N/A')}秒</div>
                <p>目標: ≤60秒</p>
            </div>
        </div>
        
        {"<div class='recommendations'><h3>💡 推奨改善事項</h3><ul>" + "".join(f"<li>{rec}</li>" for rec in quality_data.get('recommendations', [])) + "</ul></div>" if quality_data.get('recommendations') else ""}
        
        <div class="timestamp">
            最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def watch_mode(self, interval: int = 300):
        """監視モード（定期実行）"""
        print(f"👁️  監視モード開始 - {interval}秒間隔で実行")
        
        try:
            while True:
                print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - 定期チェック実行")
                self.run_pipeline(['quality-check', 'quality-monitoring'])
                self.generate_dashboard()
                
                print(f"⏰ 次回実行まで {interval} 秒待機...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 監視モード終了")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ローカルCI/CDシステム")
    parser.add_argument('--stages', nargs='+', help='実行するステージを指定')
    parser.add_argument('--dashboard', action='store_true', help='ダッシュボードのみ生成')
    parser.add_argument('--watch', type=int, metavar='SECONDS', help='監視モード（指定秒数間隔で実行）')
    
    args = parser.parse_args()
    
    ci = LocalCI()
    
    if args.dashboard:
        dashboard_path = ci.generate_dashboard()
        print(f"🌐 ダッシュボード: file://{Path(dashboard_path).absolute()}")
    elif args.watch:
        ci.watch_mode(args.watch)
    else:
        result = ci.run_pipeline(args.stages)
        
        # ダッシュボード自動生成
        dashboard_path = ci.generate_dashboard()
        print(f"\n🌐 ダッシュボード: file://{Path(dashboard_path).absolute()}")
        
        # 終了コード設定
        sys.exit(0 if result['overall_status'] == 'passed' else 1)


if __name__ == "__main__":
    main()