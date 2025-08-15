# Claude-Gemini協業システム トラブルシューティングガイド

## 🚨 よくある問題と解決法

### 1. API接続エラー

#### 問題: `ConnectionError` / `NetworkError`
```
❌ Gemini API実行失敗: NetworkError: Unable to connect
```

**原因と解決法:**
- **ネットワーク接続**: インターネット接続確認
- **ファイアウォール**: 企業ネットワークの制限確認
- **プロキシ設定**: 必要に応じてプロキシ設定

```bash
# 接続テスト
python gemini_reports/gemini_api_executor.py --test

# ネットワーク確認
curl -I https://generativelanguage.googleapis.com/
```

#### 問題: `401 Unauthorized`
```
❌ API接続失敗: 401 Unauthorized
```

**解決法:**
```bash
# APIキー再設定
python gemini_reports/api_config.py --setup

# 設定状況確認
python gemini_reports/api_config.py --status
```

### 2. APIクォータ制限

#### 問題: `429 Quota Exceeded`
```
❌ クォータ制限エラー: 429 You exceeded your current quota
```

**自動対応:**
- システムが自動的に60秒待機してリトライ
- 最大3回の自動再試行

**手動対応:**
```bash
# 現在の統計確認
python gemini_reports/gemini_api_executor.py --stats

# しばらく待ってから再実行
sleep 300  # 5分待機
python -m gemini_reports.claude_gemini_orchestrator --request "タスク内容"
```

**根本解決:**
- Google AI Studio でクォータ確認
- 有料プランへのアップグレード検討

### 3. レスポンス解析エラー

#### 問題: コードブロック抽出失敗
```
❌ Geminiレスポンスからコードを抽出できませんでした
```

**原因:**
- Geminiが期待した形式で回答していない
- マークダウン記法の問題

**解決法:**
1. **フェイルセーフ機能**: 自動的に代替抽出を実行
2. **手動確認**: 生成されたレスポンスを確認
```bash
# デバッグログ有効化
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# 実行コマンド
"
```

### 4. 実装ファイル作成エラー

#### 問題: `PermissionError` / `FileNotFoundError`
```
❌ ファイル作成失敗: PermissionError: Permission denied
```

**解決法:**
```bash
# 権限確認
ls -la tmp/
chmod 755 tmp/

# ディレクトリ作成
mkdir -p tmp/
```

#### 問題: 構文エラー
```
⚠️ 構文チェック失敗: SyntaxError
```

**自動対応:**
- システムが構文エラーを検出・記録
- Claude品質レビューで修正

**手動確認:**
```bash
# 生成ファイルの構文チェック
python -m py_compile tmp/generated_file.py
```

### 5. オーケストレーション失敗

#### 問題: `ExecutionStatus.FAILED`
```
🎯 最終結果: failed
❌ Gemini API実装失敗
```

**診断手順:**
1. **ログ確認**: 詳細なエラーメッセージを確認
2. **統計確認**: 成功率とエラー分布を分析
3. **段階実行**: タスクを分割して再実行

```bash
# 詳細統計
python -m gemini_reports.claude_gemini_orchestrator --stats

# 要件分析のみ実行
python -m gemini_reports.claude_gemini_orchestrator --analyze "タスク内容"
```

### 6. パフォーマンス問題

#### 問題: 実行時間が長い
```
実行時間: 300秒 (通常の10倍)
```

**原因と対応:**
- **APIレスポンス遅延**: リトライ回数確認
- **大量データ処理**: タスク分割検討
- **ネットワーク遅延**: 接続環境確認

```bash
# リトライ統計確認
python gemini_reports/gemini_api_executor.py --stats

# タスク分割実行
python -m gemini_reports.claude_gemini_orchestrator --request "ファイル1のみ修正"
python -m gemini_reports.claude_gemini_orchestrator --request "ファイル2のみ修正"
```

## 🔧 高度なトラブルシューティング

### ログレベル調整

```python
# デバッグログ有効化
import logging
logging.getLogger('gemini_reports').setLevel(logging.DEBUG)

# 実行
from gemini_reports.claude_gemini_orchestrator import ClaudeGeminiOrchestrator
orchestrator = ClaudeGeminiOrchestrator()
```

### 設定ファイル確認

```bash
# 設定確認
cat gemini_reports/orchestration_log.json | jq '.[-1]'  # 最新実行ログ
cat gemini_reports/api_config.json  # API設定（存在する場合）
```

### 手動API実行

```python
# 手動テスト
import asyncio
from gemini_reports.gemini_api_executor import GeminiAPIExecutor

async def test():
    executor = GeminiAPIExecutor()
    result = await executor.test_connection()
    print(result)

asyncio.run(test())
```

## 📊 監視・メンテナンス

### 定期監視項目

```bash
# 日次監視スクリプト例
#!/bin/bash
echo "=== Claude-Gemini協業システム監視 ==="
echo "日時: $(date)"
echo ""

echo "📊 統計情報:"
python -m gemini_reports.claude_gemini_orchestrator --stats
echo ""

echo "🔧 API接続テスト:"
python gemini_reports/gemini_api_executor.py --test
echo ""

echo "⚙️ 設定状況:"
python gemini_reports/api_config.py --status
```

### パフォーマンス最適化

```python
# 設定調整例（claude_gemini_orchestrator.py）
class ClaudeGeminiOrchestrator:
    def __init__(self):
        # リトライ設定調整
        self.max_retries = 5  # リトライ回数増加
        self.retry_delays = [1, 3, 10, 30, 60]  # 段階的待機時間
        
        # タイムアウト設定
        self.api_timeout = 120  # API タイムアウト延長
```

### ログローテーション

```bash
# ログファイル管理
find gemini_reports/ -name "*.json" -mtime +30 -delete  # 30日以上のログ削除
find gemini_reports/execution_results/ -name "*.json" -mtime +7 -delete  # 実行結果7日保持
```

## 🆘 エスカレーション手順

### Level 1: 自動復旧
- システム内蔵のリトライ・フェイルセーフ機能
- 最大3回の自動再試行
- エラータイプ別の自動対応

### Level 2: 手動対応
- エラーログ確認・分析
- 設定調整・再実行
- タスク分割・段階実行

### Level 3: システム管理者
- API設定・認証問題
- インフラ・ネットワーク問題
- パフォーマンス調整

### Level 4: 開発チーム
- バグ・機能改善
- 新機能追加
- アーキテクチャ変更

## 📞 サポート情報

### ログ収集方法
問題報告時に以下の情報を収集：

```bash
# 基本情報
python --version
pip list | grep google-generativeai

# 設定状況
python gemini_reports/api_config.py --status

# 最新統計
python -m gemini_reports.claude_gemini_orchestrator --stats
python gemini_reports/gemini_api_executor.py --stats

# 最新実行ログ
tail -n 50 gemini_reports/orchestration_log.json
```

### 既知の制限事項
- **APIクォータ**: Free Tierは1日15リクエスト制限
- **ファイルサイズ**: 1ファイル最大8KB推奨
- **同時実行**: 1プロセスのみ対応
- **対応言語**: Python のみ

---

*Updated: 2025-08-15 | Version: 1.0*  
*問題が解決しない場合は開発チームまでご連絡ください*