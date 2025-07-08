# 記法ツール使用ガイド

Kumihan-Formatterの記法チェック・自動修正ツールの使用方法について説明します。

## 🛠️ 利用可能ツール

### 1. syntax_validator.py（基本版）
記法エラーの検証のみを行います。

```bash
# 基本的な使用方法
python tools/dev/tools/syntax_validator.py examples/*.txt

# 単一ファイル
python tools/dev/tools/syntax_validator.py examples/01-quickstart.txt
```

### 2. syntax_fixer.py（推奨版）
検証・プレビュー・自動修正の全機能を提供します。

```bash
# 記法エラーの検証のみ
python tools/dev/tools/syntax_fixer.py examples/*.txt

# 修正内容のプレビュー（ファイル変更なし）
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix --preview

# 自動修正の実行（ファイル変更あり）
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix
```

## 📱 macOS D&D制限について

**問題**: macOSではセキュリティ制限により、.commandファイルへのD&D機能が正常に動作しない場合があります。

**解決方法**: コマンドラインでの直接実行を推奨します。

### コマンドライン実行例

```bash
# プロジェクトルートディレクトリで実行

# 1. 記法エラーの検証
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt

# 2. 修正内容のプレビュー
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix --preview

# 3. 自動修正の実行
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix

# 4. 静かなモード（詳細出力を抑制）
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix --quiet
```

## 🎯 使用パターン

### 開発ワークフロー

1. **エラー発見**: 記法問題の確認
   ```bash
   python tools/dev/tools/syntax_fixer.py examples/elements/item-template.txt
   ```

2. **修正確認**: 修正内容の事前確認
   ```bash
   python tools/dev/tools/syntax_fixer.py examples/elements/item-template.txt --fix --preview
   ```

3. **自動修正**: 実際のファイル修正
   ```bash
   python tools/dev/tools/syntax_fixer.py examples/elements/item-template.txt --fix
   ```

### バッチ処理

```bash
# 全テンプレートファイルを一括処理
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix

# 全サンプルファイルを一括処理
python tools/dev/tools/syntax_fixer.py examples/*.txt --fix --preview

# 特定パターンのファイルのみ
python tools/dev/tools/syntax_fixer.py examples/*template*.txt --fix
```

## 🔧 技術詳細

### 自動修正される問題

1. **不完全ブロック構造**
   - 見出しブロックの閉じマーカー不備
   - ブロック終了マーカー (`;;;`) の欠落

2. **連続マーカー統合**
   - `;;;keyword1;;; ;;;keyword2;;;` → `;;;keyword1+keyword2;;;`

3. **不要な空マーカー削除**
   - 冗長な空 `;;;` 行の除去

### 出力形式

#### 検証モード
```
❌ examples/item-template.txt: 3 エラー
✅ examples/02-basic.txt: OK
```

#### プレビューモード
```
📋 差分プレビュー: examples/item-template.txt
--- examples/item-template.txt (修正前)
+++ examples/item-template.txt (修正後)
@@ -10,3 +10,2 @@
 基本情報
-;;;
-;;;
+;;;
```

#### 修正モード
```
🔧 examples/item-template.txt: 3 箇所修正

📊 修正結果サマリー
   - 処理ファイル数: 1
   - 修正したファイル数: 1
   - 総修正箇所数: 3
```

## 💡 トラブルシューティング

### よくある問題

#### 1. 仮想環境エラー
```bash
# 仮想環境をアクティベート
source .venv/bin/activate
# または
source venv/bin/activate
```

#### 2. モジュール未見つけエラー
```bash
# プロジェクトルートディレクトリにいることを確認
pwd
# /Users/username/GitHub/Kumihan-Formatter であることを確認
```

#### 3. パーミッションエラー
```bash
# .commandファイルに実行権限を付与
chmod +x 記法ツール/*.command
```

### ファイルパス指定

```bash
# 絶対パス
python tools/dev/tools/syntax_fixer.py /path/to/file.txt --fix

# 相対パス（プロジェクトルートから）
python tools/dev/tools/syntax_fixer.py examples/01-quickstart.txt --fix

# ワイルドカード
python tools/dev/tools/syntax_fixer.py examples/elements/*.txt --fix
```

## 📈 効果

- **開発効率**: 手動修正作業の自動化
- **トークン節約**: 90%以上のトークン消費量削減
- **品質向上**: 一貫性のある記法修正
- **クロスプラットフォーム**: Windows/macOS/Linux対応

## 🔗 関連ドキュメント

- [SPEC.md](../../SPEC.md) - Kumihan記法仕様
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - 開発ガイドライン
- [CLI_REFERENCE.md](../user/CLI_REFERENCE.md) - CLI全般リファレンス
