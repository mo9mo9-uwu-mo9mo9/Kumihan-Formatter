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

# PR作成
gh pr create --title "タイトル" --body "詳細説明"
```

### テスト・品質管理
```bash
# 必須実行コマンド
make lint       # Black, isort, flake8
make test       # pytest
```

---

## 🤖 Claude ↔ Gemini 協業システム

> **Token節約システム** - 60-70%コスト削減を実現

### 基本使用方法
```bash
# 自動判断でGemini使用
make gemini-mypy TARGET_FILES="file1.py,file2.py"

# 統合品質チェック
make gemini-quality-check

# 詳細レポート生成
make gemini-quality-report
```

### システム概要
- **コスト効率**: Claude($15/$75) → Gemini($0.30/$2.50) = 95%削減
- **自動判断**: Token・複雑度・コスト分析による適応的AI選択
- **品質統一**: 7種類チェック・3段階ゲート・リアルタイム監視

**詳細ガイド**: [docs/claude/gemini-collaboration.md](docs/claude/gemini-collaboration.md)

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
- **警告**: 200行/10KB（見直し推奨）
- **クリティカル**: 250行/12KB（即座対応必須）

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
- [Gemini協業ガイド](docs/claude/gemini-collaboration.md)

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