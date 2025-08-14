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
5. **🤖 Gemini協業優先**: Token節約・コスト効率化のため積極活用

### 基本ルール
- **新規Issue対応時のみ**: 適切なブランチ作成・切り替え実施
- **一時ファイル**: 全て `tmp/` 配下に出力（絶対遵守）
- **日本語使用**: コメント・レビュー・ドキュメントは日本語
- **ログ使用**: `from kumihan_formatter.core.utilities.logger import get_logger`

### 🤖 Gemini活用指針（**必須実行**）
- **自動判定優先**: 1000トークン以上・定型作業はGemini実行
- **品質保証徹底**: 3層検証（構文→品質→Claude承認）必須
- **フェイルセーフ活用**: Gemini失敗時は即座にClaude代替
- **学習・改善**: 実行結果を蓄積し継続的品質向上
- **📋 作業レポート**: `gemini_reports/` に自動記録（外部非公開）

---

## 🔧 開発ワークフロー

### ブランチ管理
```bash
# 必須形式: {type}/issue-{番号}-{英語概要}
git checkout -b feat/issue-123-description
```

### Issue・PR管理
```bash
# Issue作成（ラベル必須）
gh issue create --title "タイトル" --body "内容" \
  --label "バグ,優先度:高,難易度:普通,コンポーネント:パーサー"

# PR作成
gh pr create --title "タイトル" --body "詳細説明"
```

### テスト・品質管理
```bash
make lint       # Black, isort, flake8, mypy
make test       # pytest
```

#### 品質管理基盤 (Issue #831対応済み)
- **設定統一**: pre-commit ↔ mypy 完全統一（pyproject.toml基準）
- **現状**: 73件エラー（段階的解決計画策定済み）
- **後続対応**: Issue #832(unreachable), #833(return-value)で段階的改善

---

## 👑 Claude-Gemini 役割分担体制

> **上司Claude・部下Gemini** - 明確な責任分担によるToken節約とコスト効率化

### Claude（上司・管理者）責任範囲
- **🎯 戦略・設計**: プロジェクト全体アーキテクチャ・新機能設計・要求解析
- **🛡️ 品質保証**: コードレビュー・最終承認・複雑なデバッグ・品質責任  
- **👥 コミュニケーション**: ユーザー対話・進捗報告・意思決定・問題解決

### Gemini（部下・実装者）責任範囲  
- **⚡ 実装作業**: 具体的コード修正・型注釈追加・定型バグ修正・コード整形
- **📦 大量処理**: 複数ファイル一括処理・テンプレート生成・繰り返し作業
- **✅ 品質準拠**: Claude指示厳格遵守・品質基準通過・構文エラー防止

### 💰 Token節約戦略（目標: 99%削減）
- **自動判定**: 1000トークン以上 + simple/moderate → Gemini優先
- **コスト効率**: Claude($15/$75) → Gemini($0.30/$2.50) = **99%削減目標**
- **品質保証**: 3層検証（構文→品質→Claude承認）でリスク管理

---

## 🤖 協業システム実行指針

### Gemini推奨ケース（自動実行）
```python
# 型注釈修正（no-untyped-def等）
def function(param) -> None:          # ❌ 修正前
def function(param: Any) -> None:     # ✅ 修正後

# 単純バグ修正・コード整形
make gemini-mypy TARGET_FILES="*.py"  # 一括処理
```

### Claude専任ケース（直接実行）  
- **新機能設計・実装** - アーキテクチャレベル判断
- **複雑デバッグ・問題解決** - 高度な分析・推論
- **ユーザー要求対応** - コミュニケーション・戦略判断

### 自動化レベル設定
- **FULL_AUTO**: simple + 低リスク → 即座自動実行
- **SEMI_AUTO**: moderate + 中リスク → 承認後実行  
- **APPROVAL_REQUIRED**: complex + 高リスク → 事前承認必須
- **MANUAL_ONLY**: critical + 最高リスク → Claude専任

**詳細ガイド**: [docs/claude/gemini-collaboration.md](docs/claude/gemini-collaboration.md)

---

## 🛡️ 品質保証システム（3層検証体制）

### Layer 1: 構文検証（自動）
- AST解析による構文エラー検出、型注釈パターン自動修正、禁止構文の事前検証

### Layer 2: 品質検証（自動）
```bash
make lint        # Black, isort, flake8 通過必須
make mypy        # strict mode 通過必須  
make test        # 既存テスト全通過必須
```

### Layer 3: Claude最終承認（手動）
- **コードレビュー**: Gemini成果物の詳細確認
- **品質責任**: 最終的な品質保証・承認
- **統合確認**: 全体システムとの整合性検証

### 🔄 フェイルセーフ機能
- Gemini実行失敗時: 自動的にClaude代替実行
- 品質基準未達時: 自動的な追加修正指示
- エラー時: 詳細ログ記録・学習データ化

### 📊 品質監視
- **リアルタイム監視**: `postbox/monitoring/` システム
- **品質履歴追跡**: 改善トレンド分析
- **コスト・品質バランス**: ROI最適化

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

### 基本記法
- **ブロック記法**: `# 装飾名 #内容##` （太字・イタリック・見出し等）
- **構造要素**: 見出し・リスト・目次・リンク対応
- **詳細仕様**: [記法完全仕様](docs/specs/notation.md)

---

## 📊 プロジェクト構造

### 主要コンポーネント
- **パーサー**: `core/` - 記法解析エンジン（block_parser, utilities含む）
- **レンダラー**: `core/rendering/` - HTML出力・テンプレート処理
- **CLI**: `cli.py + commands/` - コマンドライン interface  
- **設定**: `config/` - 設定管理・品質基準

---

## 🔍 品質・性能指標

### CLAUDE.md サイズ管理
- **推奨**: 150行/8KB以下（品質重視）
- **警告**: 200行/10KB（見直し推奨）
- **クリティカル**: 250行/12KB（即座対応必須）

### 監視・ドキュメント
- **監視**: `make claude-check` / `make code-quality` （品質・性能評価）
- **開発者向け**: [アーキテクチャ](docs/dev/architecture.md) / [Gemini協業](docs/claude/gemini-collaboration.md)  
- **記法・仕様**: [記法仕様](docs/specs/notation.md) / [機能仕様](docs/specs/functional.md)
- **ユーザー**: [利用ガイド](docs/user/user-guide.md) / [Claude活用法](docs/claude/reference.md)

---

## ⚙️ 重要な実行時注意事項

### 禁止事項
- ❌ 日本語ブランチ名（システム的に拒否）
- ❌ プロジェクトルート直下への一時ファイル出力
- ❌ 英語でのレビュー・コメント
- ❌ 未承認でのファイル作成・変更
- ❌ **Gemini品質基準未達成でのマージ**（3層検証必須）
- ❌ **自動判定システムの無視**（Token節約機会の逸失）

### 必須事項
- ✅ 作業前の計画報告
- ✅ tmp/ 配下での一時ファイル管理
- ✅ 適切なラベル付きIssue作成
- ✅ 品質チェック（lint/typecheck）の実行
- ✅ **🤖 Gemini協業の必須実行**（コスト削減目標99%）
- ✅ **Gemini実行時3層検証**（構文→品質→Claude承認）
- ✅ **Token使用量1000以上時Gemini検討**（コスト効率優先）
- ✅ **📋 協業レポート自動生成**（gemini_reports/ 格納）

### 🤖 Gemini協業時の特別注意事項
- **品質責任**: 部下成果物でもClaude最終責任
- **フェイルセーフ**: 実行失敗時は即座代替実行
- **継続改善**: 結果蓄積・学習データ化・品質向上

---

*🎯 Claude Code最適化済み - 2025年8月版*