# Gemini協業失敗率削減システム - 運用マニュアル

## 🎯 システム概要

Issue #891で実装した改善システムにより、Gemini協業の成功率を57.1% → 85.7%に向上。
96.9%のコスト削減を維持しながら、Claudeの作業負荷を80%削減。

## 🚀 日常運用手順

### 1. 定型MyPy修正作業

```bash
# 1. エラー確認
python3 -m mypy kumihan_formatter --strict

# 2. Gemini協業判定
python3 gemini_reports/gemini_collaboration_checker.py "MyPy修正"

# 3. Gemini実行（自動推奨の場合）
python3 gemini_reports/gemini_api_executor.py --instruction [生成された指示書] --task-id mypy_fix_$(date +%Y%m%d_%H%M%S)
```

### 2. 複雑システム新規実装

```bash
# 1. 要件明確化
python3 gemini_reports/claude_gemini_orchestrator.py --request "リアルタイム○○システム実装"

# 2. 実装・品質検証
# → 3層検証システムで自動品質保証

# 3. 動作確認
# → 実装されたシステムの動作テスト
```

## 🔍 品質監視・効果測定

### 改善効果の定期確認

```bash
# 月次分析実行
python3 tmp/gemini_improvement_analyzer.py

# 重要指標:
# - 成功率: 85%以上維持
# - コスト削減: 96%以上維持
# - Claude作業削減: 80%以上維持
```

### 失敗パターンの学習

```bash
# 失敗パターン確認
cat gemini_reports/failure_patterns.json

# 学習データ活用:
# - 自動改善提案生成
# - テンプレート精度向上
# - 品質検証強化
```

## ⚠️ トラブル対応

### よくある問題

1. **ファイル配置エラー**: 
   - 修正ファイルがtmp/に保存される
   - → システム修正済み（Phase 1で解決）

2. **品質検証失敗**:
   - MyPy/Flake8エラー
   - → 3層検証で早期検出・自動修正

3. **API制限エラー**:
   - Quota exceeded
   - → 自動リトライ・待機システム

### エスカレーション基準

- **即座にClaude引き継ぎ**: 構文エラー、セキュリティ懸念
- **追加改善検討**: 成功率80%未満継続
- **システム見直し**: コスト削減90%未満

## 📊 運用KPI

### 目標値

| 指標 | 目標 | 閾値 |
|------|------|------|
| 成功率 | 85%以上 | 80%以下で改善要 |
| コスト削減 | 96%以上 | 90%以下で見直し |
| Claude負荷削減 | 80%以上 | 70%以下で調整要 |

### 継続改善

- **週次**: 失敗パターン分析
- **月次**: 効果測定・改善検討
- **四半期**: システム全体見直し

## 🔧 保守・メンテナンス

### 定期作業

1. **API設定確認**: 月1回
2. **品質基準更新**: プロジェクト変更時
3. **テンプレート改善**: 失敗パターン分析後
4. **ドキュメント更新**: システム変更時

### バックアップ・復旧

- **設定ファイル**: gemini_reports/config.json
- **失敗学習データ**: gemini_reports/failure_patterns.json
- **実行履歴**: gemini_reports/execution_results/

---

*作成日: 2025-08-15*  
*Issue #891 - Gemini協業失敗率削減システム運用開始*