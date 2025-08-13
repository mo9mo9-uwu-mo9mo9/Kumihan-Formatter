#!/usr/bin/env python3
"""
Quality Dashboard Runner
Makefile構文問題回避用の独立実行スクリプト
"""

import sys
import os
import webbrowser

# パス設定
sys.path.append('postbox')

try:
    from quality.dashboard.metrics_collector import QualityMetricsCollector
    from quality.dashboard.dashboard_generator import QualityDashboardGenerator

    print('📊 メトリクス収集中...')
    collector = QualityMetricsCollector()
    metrics = collector.collect_all_metrics()

    print('🎨 ダッシュボード生成中...')
    generator = QualityDashboardGenerator()
    dashboard_path = generator.generate_dashboard(metrics)

    # tmp/ 配下にコピー
    os.makedirs('tmp', exist_ok=True)
    if dashboard_path.startswith('postbox'):
        import shutil
        target_path = f'tmp/{dashboard_path.split("/")[-1]}'
        shutil.copy2(dashboard_path, target_path)
        dashboard_path = target_path

    print(f'✅ ダッシュボード完成: {dashboard_path}')

    # ブラウザで開く
    webbrowser.open(f'file://{os.path.abspath(dashboard_path)}')

except Exception as e:
    print(f'⚠️ ダッシュボード生成エラー: {e}')
    sys.exit(1)
