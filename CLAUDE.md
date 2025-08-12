# CLAUDE.md

> **Kumihan-Formatter** - Claude Code プロジェクト設定ファイル  
> **Status**: Development - 2025年版最適化済み

---

## 🎯 プロジェクト概要

- **言語**: 日本語メインプロジェクト
- **技術スタック**: Python 3.12+, Black, isort, mypy (strict)
- **エンコーディング**: UTF-8
- **記法**: Kumihan独自ブロック記法 (`# 装飾名 #内容##`)

## 📋 開発原則

### コア原則
1. **作業計画の事前報告**: ファイル変更・実行前に必ず計画を報告
2. **ユーザー主導**: AIは提案のみ、決定権はユーザーが保持
3. **指示の厳格遵守**: 非効率でもユーザー指示を最優先
4. **透明性の確保**: 全作業プロセスを明確に報告

### 基本ルール
- **新規Issue対応時のみ**: 適切なブランチ作成・切り替え実施
- **一時ファイル**: 全て `tmp/` 配下に出力（絶対遵守）
- **日本語使用**: コメント・レビュー・ドキュメントは日本語
- **ログ使用**: `from kumihan_formatter.core.utilities.logger import get_logger`

---

## 🔧 開発ワークフロー

### ブランチ管理
```bash
# 必須形式: {type}/issue-{番号}-{英語概要}
# 例: feat/issue-123-add-block-parser
git checkout -b feat/issue-123-description
```

### Issue・PR管理
```bash
# Issue作成（ラベル必須）
gh issue create --title "タイトル" --body "内容" \
  --label "バグ,優先度:高,難易度:普通,コンポーネント:パーサー"

# ラベル管理
# 必要なラベルが存在しない場合は自動作成を許可
# 例: gh label create "新ラベル" --description "説明" --color "color"

# PR作成
gh pr create --title "タイトル" --body "詳細説明"
```

### テスト・品質管理
```bash
# 必須実行コマンド
make lint       # Black, isort, flake8
make typecheck  # mypy strict
make test       # pytest
```

---

## 🤖 Claude ↔ Gemini協業システム

### 📊 自動判定基準

**Gemini使用判定条件（自動）:**
- **Token使用量**: 1,000トークン以上の大規模タスク
- **複雑度**: moderate以上（2時間超の作業）
- **エラー数**: 10件以上の修正が必要
- **効果スコア**: 0.6以上の改善期待値

**自動化レベル:**
- 🟢 **FULL_AUTO**: 低リスク・低コスト（$0.01以下）で自動実行
- 🟡 **SEMI_AUTO**: 中リスク時は重要変更のみ承認
- 🔴 **APPROVAL_REQUIRED**: 高リスク・高コストは必ず手動承認
- ⚫ **MANUAL_ONLY**: 効果が低い場合はClaude単独

### 🚀 Gemini活用コマンド

```bash
# mypy修正の自動判定・実行
make gemini-mypy

# 特定エラータイプの一括修正
make gemini-fix ERROR_TYPE=no-untyped-def

# 進捗・コスト確認
make gemini-status

# 設定変更
make gemini-config
```

### 📋 具体的使用場面

**🎯 Gemini推奨シナリオ:**
- Issues #831-836: 大量mypy修正（1,219エラー）
- 100ファイル以上の一括リファクタリング  
- 型注釈の全プロジェクト適用
- 複数エラータイプの同時修正

**🧠 Claude単独推奨:**
- 複雑なロジック設計・アーキテクチャ変更
- セキュリティ重要ファイルの修正
- カスタムビジネスロジック実装
- 詳細なコードレビュー

### 💰 コスト効率管理

**Token節約効果: 60-70%削減**
- **従来**: Claude単独 → 高Token消費
- **協業**: Claude（分析・計画）↔ Gemini 2.5 Flash（実行）→ $0.30/1M入力, $2.50/1M出力

**品質保証プロセス:**
1. **Claude事前分析**: リスク評価・修正計画
2. **Gemini実行**: Flash 2.5による効率的修正
3. **Claude品質レビュー**: 結果検証・承認判定
4. **統合レポート**: コスト・品質・効果測定

### ⚙️ 設定カスタマイズ

```python
# 自動化設定例
coordinator.set_automation_preferences({
    "thresholds": {
        "min_tokens_for_gemini": 1500,    # Gemini使用最小Token数
        "max_cost_auto_approval": 0.02,   # 自動承認最大コスト
        "min_benefit_score": 0.7,         # 最小効果スコア
        "complexity_threshold": "moderate" # 複雑度閾値
    }
})
```

### 🔍 監視・品質管理

**自動品質チェック:**
- mypy strict mode適合性
- pre-commit hooks通過
- テスト全件通過
- セキュリティスキャン

**進捗監視:**
```bash
# 実行統計表示
python3 postbox/workflow/dual_agent_coordinator.py --stats

# コスト追跡
cat postbox/monitoring/cost_tracking.json

# 品質レポート
make gemini-report
```

#### 🎯 統合品質管理システム

**Claude ↔ Gemini協業での統一品質保証:**

```bash
# 包括的品質チェック (7項目評価)
make gemini-quality-check

# 品質ゲートチェック (段階別基準)
make gemini-quality-gate GATE_TYPE=pre_commit   # 0.8以上
make gemini-quality-gate GATE_TYPE=pre_push     # 0.85以上
make gemini-quality-gate GATE_TYPE=production   # 0.9以上

# 品質統合ワークフロー (事前→修正→事後チェック)
make gemini-integrated-workflow

# 詳細品質レポート生成
make gemini-quality-report FORMAT=html    # HTML形式
make gemini-quality-report FORMAT=json    # JSON形式

# リアルタイム品質監視
make gemini-quality-monitor
```

**品質基準統一:**
- **総合スコア**: 0.7以上（最低基準）
- **型チェック**: 0.8以上（mypy strict必須）
- **セキュリティ**: 0.9以上（脆弱性ゼロ目標）
- **エラー数制限**: 10件以下
- **フォーマット**: Black完全準拠

**自動アラート:**
- 品質スコア急低下検出
- エラー数閾値超過通知
- 連続的品質劣化警告
- セキュリティリスク即時通知

---

## 📝 コーディング標準

### Python コードスタイル
- **フォーマット**: Black (line-length=88)
- **インポート**: isort設定に従う
- **型注釈**: mypy strict mode必須
- **ログ**: プロジェクト標準ロガー使用

### ファイル出力規則
```python
# 正しい実装パターン
import os
output_path = "tmp/" + filename
os.makedirs("tmp", exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)
```

### エラーハンドリング
```python
# 推奨パターン
from kumihan_formatter.core.utilities.logger import get_logger
logger = get_logger(__name__)

try:
    # 処理
    pass
except Exception as e:
    logger.error(f"エラー詳細: {e}")
    raise
```

---

## 🎨 Kumihan記法仕様

### ブロック記法（推奨）
```
# 太字 #重要なテキスト##
# イタリック #強調テキスト##
# 見出し1 #メインタイトル##
# ハイライト #注目ポイント##
# 色指定 color="#FF0000" #赤色テキスト##
```

### 構造要素
- **見出し**: `# 見出し1-5 #タイトル##`
- **リスト**: `# リスト #項目1|項目2|項目3##`
- **目次**: `# 目次 #自動生成##`
- **リンク**: `# リンク url="https://..." #表示テキスト##`

---

## 📊 プロジェクト構造

### 主要コンポーネント
- **パーサー**: `kumihan_formatter/core/` - 記法解析エンジン
- **レンダラー**: `kumihan_formatter/core/rendering/` - HTML出力
- **CLI**: `kumihan_formatter/cli.py` - コマンドライン interface
- **設定**: `kumihan_formatter/config/` - 設定管理

### 重要ディレクトリ
```
kumihan_formatter/
├── core/                 # コア機能
│   ├── block_parser/     # ブロック解析
│   ├── rendering/        # レンダリング
│   └── utilities/        # 共通ユーティリティ
├── commands/             # CLI コマンド
└── config/              # 設定管理
```

---

## 🔍 品質・性能指標

### CLAUDE.md サイズ管理
- **推奨**: 150行/8KB以下（品質重視）
- **警告**: 250行/12KB（見直し推奨）
- **クリティカル**: 400行/20KB（即座対応必須）

### 監視コマンド
```bash
make claude-check         # CLAUDE.md品質チェック
make performance-test     # 性能テスト実行
make code-quality        # 総合品質評価
```

---

## 📚 ドキュメント・リンク

### 開発者向け
- [アーキテクチャ設計](docs/dev/architecture.md)
- [記法完全仕様](docs/specs/notation.md)
- [機能仕様詳細](docs/specs/functional.md)

### ユーザー向け
- [利用ガイド](docs/user/user-guide.md)
- [Claude活用法](docs/claude/reference.md)

---

## ⚙️ 重要な実行時注意事項

### 禁止事項
- ❌ 日本語ブランチ名（システム的に拒否）
- ❌ プロジェクトルート直下への一時ファイル出力
- ❌ 英語でのレビュー・コメント
- ❌ 未承認でのファイル作成・変更

### 必須事項
- ✅ 作業前の計画報告
- ✅ tmp/ 配下での一時ファイル管理
- ✅ 適切なラベル付きIssue作成
- ✅ 品質チェック（lint/typecheck）の実行

---

*🎯 Claude Code最適化済み - 2025年8月版*