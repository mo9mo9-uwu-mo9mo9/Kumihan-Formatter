# Kumihan-Formatter トラブルシューティングガイド

> **包括的問題解決ガイド** - Kumihan-Formatter運用時の問題診断・解決手順

---

## 📋 概要

このガイドでは、Kumihan-Formatter の運用中に発生する可能性のある問題の診断・解決方法を体系的に説明します。

### 対象範囲
- **基本問題**: インストール・設定・実行エラー
- **Phase 4関連**: セキュリティ・ログ・監視機能の問題
- **パフォーマンス問題**: 処理速度・メモリ・リソース問題
- **運用問題**: 監視・バックアップ・アップグレード問題

---

## 🔍 診断の基本手順

問題発生時は以下の順序で診断を進めてください：

### 1. 環境確認
```bash
# Python バージョン確認
python3 --version

# パッケージ確認
pip list | grep kumihan

# システム状態確認
make test
```

### 2. ログ確認
```bash
# 構造化ログ確認
tail -f tmp/structured_*.log

# 監査ログ確認
tail -f tmp/audit_logs/*.jsonl

# エラーログ検索
grep -r "ERROR\|CRITICAL" tmp/
```

### 3. 基本診断コマンド実行
```bash
# 品質チェック
make lint

# 包括的品質確認
make gemini-quality-check

# システム診断
python3 -c "
from kumihan_formatter.core.utilities.logger import get_logger
logger = get_logger('troubleshooting')
logger.info('診断テスト実行中')
print('✅ ロガー正常動作')
"
```

---

## 🚨 一般的な問題と解決

### インストール・環境問題

#### 問題: 依存関係エラー
```
ModuleNotFoundError: No module named 'kumihan_formatter'
```

**解決手順:**
```bash
# 1. 仮想環境確認
which python3
pip list

# 2. 再インストール
pip uninstall kumihan-formatter
pip install -e .

# 3. 依存関係確認
pip install -r requirements-dev.txt
```

#### 問題: Python バージョン不一致
```
SyntaxError: invalid syntax (Python 3.8 required)
```

**解決手順:**
```bash
# 1. Python バージョン確認
python3 --version

# 2. pyenv 使用時
pyenv versions
pyenv local 3.12

# 3. 仮想環境再作成
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 設定関連問題

#### 問題: CLAUDE.md サイズ警告
```
💡 WARNING: Warning limit exceeded. Review recommended.
```

**解決手順:**
```bash
# 1. サイズ確認
make claude-check

# 2. 内容最適化
python3 scripts/claude_optimizer.py --optimize

# 3. セクション整理
python3 scripts/claude_optimizer.py --reorganize
```

#### 問題: 設定ファイル破損
```
ConfigurationError: Invalid configuration format
```

**解決手順:**
```bash
# 1. バックアップから復旧
cp CLAUDE.md.backup CLAUDE.md

# 2. 構文チェック
python3 -c "
import yaml
with open('config.yaml', 'r') as f:
    yaml.safe_load(f)
"

# 3. デフォルト設定リセット
python3 scripts/config_reset.py --reset-defaults
```

---

## 🛡️ Phase 4 関連問題

### セキュリティ機能問題

#### 問題: 入力検証エラー
```
SecurityError: Input validation failed - potential threat detected
```

**診断手順:**
```bash
# 1. セキュリティログ確認
tail -n 100 tmp/audit_logs/security_*.jsonl

# 2. 入力パターン分析
python3 -c "
from kumihan_formatter.core.security.input_validation import InputValidator
validator = InputValidator()
test_input = 'your_problematic_input'
result = validator.validate(test_input)
print(f'検証結果: {result}')
"

# 3. セキュリティレベル調整
python3 scripts/security_config.py --level medium
```

**解決方法:**
```bash
# 安全な入力パターンに修正
# または設定で例外パターンを追加
python3 scripts/security_whitelist.py --add-pattern "allowed_pattern"
```

#### 問題: 暗号化ログ問題
```
CryptographyError: Failed to encrypt log data
```

**診断・解決:**
```bash
# 1. 暗号化キー確認
python3 -c "
import os
key_path = os.getenv('ENCRYPTION_KEY_PATH', 'tmp/.encryption_key')
print(f'キーファイル: {key_path}')
print(f'存在確認: {os.path.exists(key_path)}')
"

# 2. キー再生成
python3 scripts/generate_encryption_key.py --regenerate

# 3. ログ暗号化テスト
python3 scripts/test_log_encryption.py
```

### 構造化ログ問題

#### 問題: ログ出力なし
```
WARNING: No structured logs found in tmp/
```

**診断手順:**
```bash
# 1. ログディレクトリ確認
ls -la tmp/
ls -la tmp/audit_logs/

# 2. 権限確認
chmod 755 tmp/
chmod 644 tmp/*.log

# 3. ログ設定確認
python3 -c "
from kumihan_formatter.core.utilities.logger import get_logger
logger = get_logger('test')
logger.info('テストログ出力')
"
```

**解決方法:**
```bash
# ログディレクトリ再作成
mkdir -p tmp/audit_logs
chmod 755 tmp tmp/audit_logs

# ログ設定リセット
python3 scripts/reset_logging_config.py
```

#### 問題: ログファイル肥大化
```
ERROR: Log file size exceeded 1GB limit
```

**解決手順:**
```bash
# 1. ログサイズ確認
du -h tmp/*.log
du -h tmp/audit_logs/

# 2. 古いログのアーカイブ
python3 scripts/log_archiver.py --archive-older-than 30

# 3. ログローテーション設定
python3 scripts/setup_log_rotation.py --daily --max-size 100MB
```

---

## ⚡ パフォーマンス問題

### 処理速度問題

#### 問題: 変換処理の異常な遅延
```
ProcessingTimeout: Conversion took longer than expected (>300s)
```

**診断手順:**
```bash
# 1. パフォーマンステスト実行
make test-performance

# 2. プロファイリング実行
python3 -m cProfile -o tmp/profile.stats scripts/performance_test.py

# 3. メモリ使用量確認
python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'メモリ使用量: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

**解決方法:**
```bash
# 並列処理設定調整
python3 scripts/optimize_parallel_processing.py --workers 4

# キャッシュクリア
python3 scripts/clear_performance_cache.py

# 大容量ファイル分割処理
python3 scripts/split_large_files.py --chunk-size 1000
```

#### 問題: メモリリーク
```
MemoryError: Unable to allocate memory
```

**診断・解決:**
```bash
# 1. メモリ使用量監視
python3 scripts/memory_monitor.py --duration 300

# 2. ガベージコレクション強制実行
python3 -c "
import gc
gc.collect()
print(f'オブジェクト数: {len(gc.get_objects())}')
"

# 3. メモリ制限設定
ulimit -m 1048576  # 1GB制限
python3 your_script.py
```

### リソース不足問題

#### 問題: ディスク容量不足
```
DiskSpaceError: Insufficient disk space for operation
```

**解決手順:**
```bash
# 1. 容量確認
df -h .
du -sh tmp/

# 2. 一時ファイル削除
make deep-clean

# 3. ログアーカイブ
python3 scripts/archive_old_logs.py --compress

# 4. 容量監視設定
python3 scripts/setup_disk_monitoring.py --threshold 85
```

---

## 🛡️ セキュリティ問題

### 脅威検知問題

#### 問題: セキュリティ警告過多
```
SecurityAlert: High number of threat detections (50/hour)
```

**診断手順:**
```bash
# 1. 脅威ログ分析
tail -n 200 tmp/audit_logs/security_*.jsonl | jq '.threat_type' | sort | uniq -c

# 2. 誤検知パターン確認
python3 scripts/security_analyzer.py --analyze-false-positives

# 3. セキュリティ設定確認
python3 scripts/security_config_check.py
```

**解決方法:**
```bash
# セキュリティレベル調整
python3 scripts/adjust_security_sensitivity.py --level balanced

# 許可パターン追加
python3 scripts/security_whitelist.py --add-safe-patterns
```

#### 問題: SSL/TLS証明書エラー
```
SSLError: Certificate verification failed
```

**解決手順:**
```bash
# 1. 証明書確認
openssl x509 -in cert.pem -text -noout

# 2. 証明書更新
python3 scripts/update_certificates.py --renew

# 3. 証明書検証テスト
python3 scripts/test_ssl_connection.py --verify
```

---

## 📊 ログ・監視問題

### 監視システム問題

#### 問題: メトリクス収集失敗
```
MonitoringError: Failed to collect system metrics
```

**診断・解決:**
```bash
# 1. 監視サービス状態確認
python3 scripts/monitoring_health_check.py

# 2. メトリクス収集テスト
python3 -c "
from kumihan_formatter.core.monitoring.metrics_collector import MetricsCollector
collector = MetricsCollector()
metrics = collector.collect()
print(f'収集メトリクス数: {len(metrics)}')
"

# 3. 監視サービス再起動
python3 scripts/restart_monitoring.py
```

#### 問題: ダッシュボード表示異常
```
DashboardError: Unable to render monitoring dashboard
```

**解決手順:**
```bash
# 1. ダッシュボードデータ確認
ls -la tmp/monitoring_data/

# 2. ダッシュボード再生成
make quality-dashboard

# 3. データ整合性チェック
python3 scripts/validate_dashboard_data.py
```

---

## ⚙️ 設定関連問題

### 設定競合問題

#### 問題: 設定値の不整合
```
ConfigurationConflict: Conflicting settings detected
```

**診断・解決:**
```bash
# 1. 設定整合性チェック
python3 scripts/config_validator.py --check-conflicts

# 2. 設定優先順位確認
python3 scripts/config_hierarchy.py --show-precedence

# 3. 設定統合
python3 scripts/merge_configurations.py --resolve-conflicts
```

---

## 🔧 復旧手順

### 緊急時復旧手順

#### システム全体復旧
```bash
# 1. バックアップから復旧
python3 scripts/emergency_restore.py --from-backup

# 2. 設定ファイル再初期化
python3 scripts/reset_all_configs.py --force

# 3. システム再構築
make clean
make setup
make test
```

#### データベース復旧
```bash
# 1. データ整合性チェック
python3 scripts/data_integrity_check.py

# 2. 破損データ修復
python3 scripts/repair_corrupted_data.py

# 3. インデックス再構築
python3 scripts/rebuild_indexes.py
```

---

## 🛡️ 予防策

### 定期メンテナンス

#### 日次チェックリスト
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Kumihan-Formatter 日次ヘルスチェック ==="
echo "実行日時: $(date)"

# 1. システム状態確認
make test > tmp/daily_test_$(date +%Y%m%d).log 2>&1

# 2. ログサイズ確認
du -sh tmp/ > tmp/log_usage_$(date +%Y%m%d).txt

# 3. セキュリティスキャン
python3 scripts/security_scan.py --daily >> tmp/security_scan_$(date +%Y%m%d).log

# 4. パフォーマンス測定
make test-performance > tmp/performance_$(date +%Y%m%d).log 2>&1

# 5. 設定整合性チェック
python3 scripts/config_validator.py >> tmp/config_check_$(date +%Y%m%d).log

echo "✅ 日次チェック完了"
```

#### 週次メンテナンス
```bash
# weekly_maintenance.sh

# 1. ログアーカイブ
python3 scripts/archive_weekly_logs.py

# 2. データベース最適化
python3 scripts/optimize_database.py

# 3. セキュリティ更新
python3 scripts/update_security_definitions.py

# 4. パフォーマンス最適化
python3 scripts/optimize_performance.py

# 5. バックアップ実行
python3 scripts/create_backup.py --full
```

### 監視アラート設定

#### 重要メトリクスの監視
```python
# monitoring_alerts.py
ALERT_THRESHOLDS = {
    'memory_usage': 85,      # メモリ使用率 85%
    'disk_usage': 80,        # ディスク使用率 80%
    'error_rate': 5,         # エラー率 5%
    'response_time': 10,     # レスポンス時間 10秒
    'security_threats': 10   # セキュリティ脅威 10件/時間
}

def setup_alerts():
    from kumihan_formatter.core.monitoring.alert_manager import AlertManager
    alert_manager = AlertManager()
    
    for metric, threshold in ALERT_THRESHOLDS.items():
        alert_manager.add_threshold_alert(
            metric=metric,
            threshold=threshold,
            notification_method='email'
        )
```

---

## 📞 エスカレーション手順

### サポートレベル

#### Level 1: 自動復旧 (0-5分)
- **対象**: 一時的な障害・リソース問題
- **対応**: システム内蔵の自動復旧機能
- **アクション**: ログ記録・自動リトライ・フェイルオーバー

#### Level 2: 運用者対応 (5-30分)
- **対象**: 設定問題・認証問題・環境依存問題
- **対応**: このトラブルシューティングガイドによる手動対応
- **アクション**: 診断・設定調整・サービス再起動

#### Level 3: システム管理者 (30分-2時間)
- **対象**: インフラ問題・セキュリティ問題・データ整合性問題
- **対応**: 専門知識による深い分析・修復
- **アクション**: システム分析・構成変更・データ復旧

#### Level 4: 開発チーム (2時間以上)
- **対象**: バグ・設計問題・新機能要求
- **対応**: ソースコード修正・システム拡張
- **アクション**: バグ修正・機能追加・アーキテクチャ変更

### 問題報告テンプレート

```
## 問題報告

**発生日時**: YYYY-MM-DD HH:MM:SS
**重要度**: [High/Medium/Low]
**カテゴリ**: [性能/セキュリティ/機能/設定]

### 症状
[具体的な症状・エラーメッセージ]

### 再現手順
1. [手順1]
2. [手順2]
3. [手順3]

### 環境情報
```bash
python3 --version
pip list | grep kumihan
uname -a
```

### 実施した対応
[試行した解決方法]

### 添付ファイル
- tmp/latest_error.log
- tmp/system_status.json
- 関連するスクリーンショット
```

---

## 🔍 診断ツール

### 包括的診断スクリプト

```python
#!/usr/bin/env python3
# comprehensive_diagnostic.py

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

def run_comprehensive_diagnostic():
    """包括的システム診断実行"""
    
    print("🔍 Kumihan-Formatter 包括的診断開始")
    print(f"📅 実行時刻: {datetime.now()}")
    print("=" * 60)
    
    results = {}
    
    # 1. 環境確認
    print("\n📊 1/8: 環境確認")
    results['environment'] = check_environment()
    
    # 2. 依存関係確認
    print("\n📦 2/8: 依存関係確認")
    results['dependencies'] = check_dependencies()
    
    # 3. 設定確認
    print("\n⚙️ 3/8: 設定確認")
    results['configuration'] = check_configuration()
    
    # 4. ログ確認
    print("\n📝 4/8: ログ確認")
    results['logs'] = check_logs()
    
    # 5. セキュリティ確認
    print("\n🛡️ 5/8: セキュリティ確認")
    results['security'] = check_security()
    
    # 6. パフォーマンス確認
    print("\n⚡ 6/8: パフォーマンス確認")
    results['performance'] = check_performance()
    
    # 7. 監視確認
    print("\n📊 7/8: 監視確認")
    results['monitoring'] = check_monitoring()
    
    # 8. 統合テスト
    print("\n🧪 8/8: 統合テスト")
    results['integration'] = run_integration_tests()
    
    # 結果保存
    report_path = f"tmp/diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('tmp', exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ 診断完了: {report_path}")
    return results

if __name__ == "__main__":
    run_comprehensive_diagnostic()
```

---

## 📚 関連資料

### 参考ドキュメント
- [運用ガイド](deployment_guide.md)
- [監視設定](monitoring_setup.md)
- [Claude協業トラブルシューティング](../claude/troubleshooting.md)

### 有用なコマンド集
```bash
# システム状態確認
make gemini-quality-check       # 総合品質チェック
make quality-full-check         # 完全品質チェック
make tech-debt-check           # 技術的負債チェック

# ログ・監視
tail -f tmp/structured_*.log   # リアルタイムログ
make quality-dashboard         # 品質ダッシュボード
python3 scripts/log_analyzer.py # ログ分析

# パフォーマンス
make test-performance          # パフォーマンステスト
python3 scripts/profiler.py   # プロファイリング
make clean                     # キャッシュクリア

# セキュリティ
python3 scripts/security_scan.py  # セキュリティスキャン
python3 scripts/audit_checker.py  # 監査チェック
```

---

*🔧 最終更新: 2025-08-19 | バージョン: 2.0*  
*重大な問題が解決しない場合は、システム管理者または開発チームまでエスカレーションしてください。*