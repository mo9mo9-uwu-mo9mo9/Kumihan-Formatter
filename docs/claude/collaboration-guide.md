# Claude-Gemini協業システム運用ガイド

## 📋 概要

Claude-Gemini協業システムは、Claude（PM/Manager）とGemini（Coder）の明確な役割分担により、Token削減90%以上とコスト効率化を実現する開発支援システムです。

## 🎯 システム構成

### 役割分担
```
Claude (PM/Manager)           Gemini-2.5-flash (Coder)
┌─────────────────────┐    ┌────────────────────────┐
│ • 要件分析・設計    │ →  │ • 実装・コード生成     │
│ • 作業指示書作成    │    │ • 型注釈・docstring    │
│ • 品質管理・調整    │ ←  │ • 基本構文チェック     │
│ • エラー修正・承認  │    │ • モジュール化設計     │
└─────────────────────┘    └────────────────────────┘
```

### 品質保証3層検証
- **Layer 1**: Gemini自動構文チェック
- **Layer 2**: MyPy/Flake8/Black品質検証
- **Layer 3**: Claude最終レビュー・承認

## 🚀 使用方法

### 1. 初期設定

```bash
# 1. 依存ライブラリインストール
pip install google-generativeai

# 2. Gemini API キー設定
python gemini_reports/api_config.py --setup

# 3. 接続テスト
python gemini_reports/gemini_api_executor.py --test
```

### 2. 基本的な使用方法

```bash
# 要件分析のみ実行
python -m gemini_reports.claude_gemini_orchestrator --analyze "実装内容"

# 完全協業実行
python -m gemini_reports.claude_gemini_orchestrator --request "実装内容"

# 統計情報確認
python -m gemini_reports.claude_gemini_orchestrator --stats
```

### 3. タスク適性判定

#### Gemini適性が高いタスク
- MyPy型注釈修正
- Flake8/Black整形
- 定型的なバグ修正
- 複数ファイル一括処理
- テンプレート実装

#### Claude専任が適切なタスク
- アーキテクチャ設計
- 複雑なアルゴリズム実装
- 新機能設計
- 要件の曖昧なタスク

## 📊 効果測定

### Token削減効果
```
従来（Claude単独）: 25,000-40,000 Token
協業後: 1,500-3,000 Token
削減率: 94-96%
```

### コスト削減効果
```
Claude: $75/1M出力Token
Gemini: $2.50/1M出力Token
削減率: 96.7%
```

### 時間短縮効果
```
従来: 60-90分
協業後: 12-15分
短縮率: 80-85%
```

## ⚙️ 設定オプション

### API設定 (`gemini_reports/api_config.py`)
```python
# 環境変数設定
export GEMINI_API_KEY="your_api_key_here"

# 設定ファイル使用
python gemini_reports/api_config.py --set-key "your_key" --method file
```

### 実行レベル調整
```python
# claude_gemini_orchestrator.py内で調整可能
self.max_retries = 3           # リトライ回数
self.quota_retry_delay = 60    # クォータ制限時待機
self.retry_delays = [1, 5, 15] # リトライ間隔
```

## 🔄 ワークフロー

### 標準的な実行フロー
1. **要件分析** (Claude): タスクの複雑度・適性判定
2. **作業指示書作成** (Claude): 詳細な実装指示
3. **実装実行** (Gemini): API経由での実装
4. **品質レビュー** (Claude): 3層検証・最終調整

### 失敗時の対応フロー
1. **自動リトライ**: 最大3回の自動再試行
2. **エラー分析**: 原因別の対応策実行
3. **フェイルセーフ**: Claude代替実行
4. **学習データ化**: 改善のための記録

## 📁 ファイル構成

```
gemini_reports/
├── api_config.py                    # API設定管理
├── claude_gemini_orchestrator.py    # メインオーケストレーター
├── gemini_api_executor.py          # Gemini API実行エンジン
├── work_instructions/              # 作業指示書保存
├── execution_results/              # 実行結果保存
└── orchestration_log.json         # 実行ログ
```

## 🎯 ベストプラクティス

### 効果的な指示の書き方
```bash
# Good: 具体的で明確
python -m gemini_reports.claude_gemini_orchestrator --request \
  "core/parser.pyのMyPy型注釈エラー5件を修正。no-untyped-def対応"

# Avoid: 曖昧で複雑
python -m gemini_reports.claude_gemini_orchestrator --request \
  "システム全体を見直して品質を向上させて"
```

### 大規模タスクの分割
```bash
# 段階的実行
1. python -m gemini_reports.claude_gemini_orchestrator --request "MyPy修正のみ"
2. python -m gemini_reports.claude_gemini_orchestrator --request "Flake8修正のみ" 
3. python -m gemini_reports.claude_gemini_orchestrator --request "Black整形のみ"
```

## 🔍 監視・デバッグ

### ログレベル調整
```python
import logging
logging.getLogger('gemini_reports').setLevel(logging.DEBUG)
```

### 統計監視
```bash
# 定期的な成功率確認
python -m gemini_reports.claude_gemini_orchestrator --stats

# エラー詳細確認
python gemini_reports/gemini_api_executor.py --stats
```

## 📞 サポート・問題報告

### 問題発生時の確認項目
1. **API キー設定確認**: `python gemini_reports/api_config.py --status`
2. **接続テスト実行**: `python gemini_reports/gemini_api_executor.py --test`
3. **ログ確認**: 実行時のエラーメッセージ
4. **統計確認**: 成功率・エラー分布

### よくある問題と解決法
- **APIクォータ制限**: 時間をおいて再実行
- **ネットワークエラー**: 接続環境確認
- **認証エラー**: APIキー再設定

詳細なトラブルシューティングは [troubleshooting.md](troubleshooting.md) を参照してください。

---

*Updated: 2025-08-15 | Version: 1.0*