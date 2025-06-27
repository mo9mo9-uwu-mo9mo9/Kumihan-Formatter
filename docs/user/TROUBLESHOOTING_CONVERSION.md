# 📝 変換・エンコーディングのトラブルシューティング

> **文字化け・構文エラー・ファイル関連の問題を解決**

[← トラブルシューティング目次に戻る](TROUBLESHOOTING.md)

---

## 📋 変換・エンコーディング問題一覧

- [テキストファイルが文字化けして読み込めない](#-症状-テキストファイルが文字化けして読み込めない)
- [コンソール・コマンドプロンプトで日本語が文字化け](#-症状-コンソールコマンドプロンプトで日本語が文字化け)
- [Kumihan記法エラー / 構文エラー](#-症状-kumihan記法エラー--構文エラー)
- [`FileNotFoundError` / ファイルが見つからない](#-症状-filenotfounderror--ファイルが見つからない)
- [`PermissionError` / `Access denied`](#-症状-permissionerror--access-denied)

---

## ❌ **症状**: テキストファイルが文字化けして読み込めない

### 🔍 **原因**
- ファイルがUTF-8以外の文字コードで保存されている
- BOM（Byte Order Mark）付きUTF-8で保存されている
- 古いエディタで作成されたファイル

### ✅ **解決方法**

#### **Step 1: 推奨テキストエディタの使用**

**Windows推奨エディタ:**
- **Visual Studio Code**: UTF-8自動検出・保存
- **Notepad++**: 文字コード表示・変換機能
- **サクラエディタ**: 日本語対応・無料

**macOS推奨エディタ:**
- **Visual Studio Code**: クロスプラットフォーム
- **CotEditor**: 日本語特化・軽量
- **Sublime Text**: 高機能・高速

**⚠️ 非推奨エディタ:**
- Windows標準「メモ帳」（文字コード問題多数）
- 古いバージョンのWordPad

#### **Step 2: UTF-8での保存方法**

**Visual Studio Code:**
1. ファイルを開く
2. 画面下部の文字コード表示をクリック
3. 「UTF-8で保存」を選択

**Notepad++:**
1. 「エンコード」メニュー → 「UTF-8（BOMなし）に変換」
2. Ctrl+S で保存

**メモ帳（Windows）:**
1. 「名前を付けて保存」
2. 「文字コード」で「UTF-8」を選択
3. 保存

#### **Step 3: BOM問題の解決**

BOM付きファイルの確認・修正：
```bash
# BOMの確認（コマンドライン）
file -bi your_file.txt

# BOM付きの場合 "charset=utf-8-bom" と表示される
# BOMなしの場合 "charset=utf-8" と表示される
```

**BOM除去方法:**
```bash
# Windows (PowerShell)
Get-Content -Path "input.txt" -Encoding UTF8 | Set-Content -Path "output.txt" -Encoding UTF8NoBOM

# macOS/Linux
sed '1s/^\xEF\xBB\xBF//' input.txt > output.txt
```

---

## ❌ **症状**: コンソール・コマンドプロンプトで日本語が文字化け

### 🔍 **原因**
- コンソールの文字コード設定が日本語に対応していない
- フォント設定が日本語文字に対応していない
- 古いコマンドプロンプトを使用している

### ✅ **解決方法**

#### **Windows コマンドプロンプト:**
```cmd
# 文字コードをUTF-8に設定
chcp 65001

# 確認
chcp
# 結果: アクティブ コード ページ: 65001 が表示されればOK
```

**恒久的な設定:**
1. レジストリエディタを開く
2. `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Command Processor`
3. 新しい文字列値 `Autorun` を作成
4. 値に `chcp 65001` を設定

#### **Windows PowerShell（推奨）:**
```powershell
# PowerShellはデフォルトでUTF-8対応
# 文字コード確認
[Console]::OutputEncoding

# 必要に応じて設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

#### **macOS Terminal:**
```bash
# 文字コード確認
locale

# 日本語UTF-8設定（通常は自動設定済み）
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
```

#### **フォント設定:**

**Windows:**
- コマンドプロンプトのタイトルバー右クリック → プロパティ
- フォント → 「MS ゴシック」または「Consolas」
- サイズ → 12pt以上推奨

**macOS:**
- Terminal → 環境設定 → プロファイル → フォント
- 「Menlo」、「SF Mono」、「Hiragino Sans」推奨

---

## ❌ **症状**: Kumihan記法エラー / 構文エラー

### 🔍 **原因**
- マーカー `;;;` の書き間違い
- 閉じマーカーの未記述
- 無効なキーワードの使用
- ネストエラー

### ✅ **解決方法**

#### **Step 1: 記法エラーチェッカーの使用**

```bash
# 構文チェック（実装予定機能）
python -m kumihan_formatter check-syntax your_file.txt

# 詳細エラー表示
python -m kumihan_formatter check-syntax your_file.txt --verbose

# 修正提案付き
python -m kumihan_formatter check-syntax your_file.txt --suggest-fixes
```

**手動チェック項目:**
- [ ] すべての `;;;` が行頭にある
- [ ] すべてのブロックが `;;;` で閉じられている  
- [ ] キーワードが正しく記述されている
- [ ] 空ブロックがない

#### **Step 2: よくある記法エラーと修正方法**

**❌ 間違った記法:**
```text
# 閉じマーカーなし
;;;太字
重要な情報

# マーカーが行頭にない
　;;;太字;;;

# 無効なキーワード
;;;太文字
内容
;;;

# 空ブロック
;;;太字
;;;

# color指定の位置間違い
;;;ハイライト color=#ff0000+太字
内容
;;;
```

**✅ 正しい記法:**
```text
# 正しい閉じマーカー
;;;太字
重要な情報
;;;

# 行頭からのマーカー
;;;太字;;;

# 正しいキーワード
;;;太字
内容
;;;

# 内容があるブロック
;;;太字
重要な情報
;;;

# color指定は最後
;;;太字+ハイライト color=#ff0000
内容
;;;
```

#### **Step 3: デバッグ用の最小コード作成**

問題の特定のため、最小限のテストファイルを作成：

**test_minimal.txt:**
```text
;;;見出し1
テストタイトル
;;;

これは普通のテキストです。

;;;太字
重要な情報
;;;
```

```bash
# 最小ファイルでテスト
python -m kumihan_formatter test_minimal.txt

# エラーが出る場合、行ごとに確認
```

---

## ❌ **症状**: `FileNotFoundError` / ファイルが見つからない

### 🔍 **原因**
- ファイルパスの間違い
- ファイル名に使用できない文字が含まれている
- 作業ディレクトリの間違い

### ✅ **解決方法**

#### **Step 1: ファイルパスの確認**

```bash
# 現在のディレクトリ確認
pwd                    # macOS/Linux
cd                     # Windows

# ファイル存在確認
ls -la your_file.txt   # macOS/Linux
dir your_file.txt      # Windows

# ワイルドカードで検索
ls *.txt               # macOS/Linux
dir *.txt              # Windows
```

#### **Step 2: ファイル名の注意点**

**推奨ファイル名:**
- `document.txt` ✅
- `my_scenario_v1.txt` ✅
- `test-file.txt` ✅

**避けるべき文字:**
- スペースを含む名前: `my file.txt` ❌
- 日本語文字: `私のファイル.txt` ❌  
- 特殊文字: `file<>|.txt` ❌

**スペース含みファイルの対処:**
```bash
# クォートで囲む
python -m kumihan_formatter "my file.txt"

# ファイル名変更（推奨）
mv "my file.txt" "my_file.txt"
```

#### **Step 3: 絶対パスでの指定**

```bash
# 絶対パスで実行
# Windows
python -m kumihan_formatter "C:\Users\Username\Documents\file.txt"

# macOS
python -m kumihan_formatter "/Users/username/Documents/file.txt"

# 相対パスの確認
python -m kumihan_formatter "./folder/file.txt"
```

---

## ❌ **症状**: `PermissionError` / `Access denied`

### 🔍 **原因**
- ファイルが他のアプリケーションで開かれている
- 読み取り専用属性が設定されている
- ディレクトリの書き込み権限がない
- ウイルス対策ソフトの誤検知

### ✅ **解決方法**

#### **Step 1: ファイルの使用状況確認**
- Word、Excel、テキストエディタでファイルが開かれていないか確認
- すべて閉じてから変換を実行

#### **Step 2: ファイル属性の確認・変更**

**Windows:**
```cmd
# ファイル属性確認
attrib your_file.txt

# 読み取り専用解除
attrib -R your_file.txt

# 権限確認（PowerShell）
Get-Acl your_file.txt | Format-List
```

**macOS:**
```bash
# 権限確認
ls -la your_file.txt

# 権限変更
chmod 644 your_file.txt

# 所有者確認
stat your_file.txt
```

#### **Step 3: 管理者権限での実行**

**Windows:**
1. コマンドプロンプトを「管理者として実行」
2. プロジェクトディレクトリに移動
3. 変換コマンドを実行

**macOS:**
```bash
# sudo権限で実行（通常は不要）
sudo python -m kumihan_formatter your_file.txt

# 所有者変更が必要な場合
sudo chown $USER:$USER your_file.txt
```

---

## 🔧 **予防策・ベストプラクティス**

### **ファイル作成時の注意点**
- **文字コード**: UTF-8（BOMなし）で保存
- **ファイル名**: 英数字・ハイフン・アンダースコアのみ
- **フォルダ**: 深すぎる階層を避ける（最大5階層）
- **バックアップ**: 重要ファイルは必ずバックアップ

### **推奨ディレクトリ構造**
```
project/
├── main.txt           ← メインファイル
├── backup/            ← バックアップ
│   └── main_backup.txt
├── images/            ← 画像
│   └── *.jpg
└── dist/             ← 出力先
    └── main.html
```

---

## 📞 **サポートが必要な場合**

以下の情報を含めて報告してください：

```
## 変換・エンコーディング問題報告

### ファイル情報
- ファイル名: [ファイル名]
- ファイルサイズ: [サイズ]
- 文字コード: [UTF-8/Shift_JIS/など]
- 使用エディタ: [エディタ名とバージョン]

### エラー詳細
[エラーメッセージの完全コピー]

### ファイル内容（問題部分の抜粋）
```
[問題のある記法の部分]
```

### 試した解決方法
- [ ] UTF-8で再保存
- [ ] 記法チェック
- [ ] 最小ファイルでテスト
```

---

## 📚 関連リソース

- **[トラブルシューティング目次](TROUBLESHOOTING.md)** - 他の問題も確認
- **[記法リファレンス](SYNTAX_REFERENCE.md)** - 正しい記法を確認
- **[よくある質問](FAQ.md)** - 記法関連のFAQ

---

**文字化け・記法エラーが解決することを願っています！ 📝✨**