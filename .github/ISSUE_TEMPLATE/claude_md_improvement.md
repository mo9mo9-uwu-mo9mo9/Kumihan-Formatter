---
name: CLAUDE.md改善提案
about: Claude Code公式ドキュメントの推奨事項に基づくCLAUDE.mdの改善
title: 'CLAUDE.md改善: プロジェクト固有の開発情報追加'
labels: 'enhancement, documentation, claude-code'
assignees: ''

---

## 📋 概要

Claude Code公式ドキュメントの推奨事項に基づき、現在のCLAUDE.mdにプロジェクト固有の開発情報を追加する提案です。AI運用5原則は最重要事項として維持しつつ、実用的な開発情報を充実させます。

## 🔍 現状の課題

1. **不足している具体的な開発情報**
   - ビルド・テスト・リントコマンドが記載されていない
   - コーディングスタイル（インデント、命名規則など）の具体的な指定がない
   - プロジェクトアーキテクチャの説明がない

2. **構造の改善余地**
   - 詳細を別ファイルに委ねすぎており、CLAUDE.md自体に実用的な情報が少ない
   - Claude Codeが素早く参照できる情報が不足

## ✅ 改善提案

### 1. よく使うコマンドセクションの追加

```markdown
## よく使うコマンド

### 開発用コマンド
- `make test` - テスト実行（pyproject.toml統一設定使用）
- `make lint` - リンターチェック（black, isort, flake8）
- `make format` - コードフォーマット適用
- `make coverage` - カバレッジ付きテスト実行
- `make pre-commit` - コミット前品質チェック（カバレッジ100%必須）

### CLI使用例
- `python -m kumihan_formatter convert input.txt` - ファイル変換
- `python -m kumihan_formatter sample` - サンプル生成
- `python -m kumihan_formatter check-syntax input.txt` - 構文チェック
```

### 2. コーディング規約セクションの追加

```markdown
## コーディング規約

### Python
- **バージョン**: Python 3.12以上
- **インデント**: スペース4つ
- **行長**: 88文字（Black設定）
- **フォーマッター**: Black, isort
- **型チェック**: mypy strict mode

### 命名規則
- 変数・関数: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE_CASE
- プライベート: 先頭に_

### インポート順
1. 標準ライブラリ
2. サードパーティ
3. ローカルモジュール
（isortで自動整理）
```

### 3. プロジェクト構造セクションの追加

```markdown
## プロジェクト構造

### 主要ディレクトリ
- `/kumihan_formatter` - メインパッケージ
  - `/cli.py` - CLIエントリポイント
  - `/parser.py` - 解析統括
  - `/renderer.py` - レンダリング統括
  - `/core/` - 核心機能モジュール群
  - `/templates/` - HTMLテンプレート
- `/tests/` - テストコード
- `/docs/` - ドキュメント
- `/examples/` - サンプルファイル

### 記法仕様
- 基本記法: `;;;装飾名;;; 内容 ;;;`
- 改行処理: 入力改行をそのまま反映
- エンコーディング: UTF-8（BOM付きも対応）
```

### 4. 開発フローセクションの追加

```markdown
## 開発フロー

### 新機能追加時
1. Issueでタスクを確認
2. featureブランチ作成: `feat/issue-番号`
3. 実装とテスト追加
4. `make pre-commit`で品質チェック
5. PRを作成（テンプレート使用）

### デバッグ
- ログレベル: `--debug`オプション使用
- エラートレース: `--traceback`オプション
```

## 📝 実装方針

1. **AI運用5原則は最上位に維持**
   - 現在の`<law>`タグ内の5原則はそのまま最重要事項として配置

2. **実用情報の追加**
   - 上記の4セクションをCLAUDE.mdに追加
   - Claude Codeが即座に参照できる具体的な情報を記載

3. **既存の構造を活かす**
   - インポートセクションは維持（詳細情報への参照）
   - リリース方針セクションも維持

## 🎯 期待される効果

- Claude Codeがプロジェクト固有のコマンドや規約を即座に理解
- 開発効率の向上
- 新規開発者のオンボーディング改善

## 📌 関連情報

- [Claude Code公式ドキュメント - プロジェクトメモリ](https://docs.anthropic.com/ja/docs/claude-code/memory#プロジェクトメモリを設定する)
- 現在のCLAUDE.mdバージョン: 0.5.0
