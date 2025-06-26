# 🔧 Kumihan-Formatter トラブルシューティングガイド

> **初心者の自己解決率80%を目指す包括的なトラブルシューティングガイド**
>
> 問題解決の **症状 → 原因 → 解決法** の順で整理しています。目次から該当する症状を探してください。

---

## 📋 目次

### 🚨 **緊急度：高（変換できない）**
- [Python環境の問題](#-python環境の問題)
- [エンコーディング・文字化け問題](#-エンコーディング文字化け問題)
- [変換エラーの詳細対処](#-変換エラーの詳細対処)

### ⚠️ **緊急度：中（操作に支障）**
- [Windows固有の問題](#️-windows固有の問題)
- [macOS固有の問題](#-macos固有の問題)
- [ファイル・権限関連の問題](#-ファイル権限関連の問題)

### 💡 **緊急度：低（予防・最適化）**
- [デバッグ手法](#-デバッグ手法)
- [予防的対策](#-予防的対策)
- [よくある質問（FAQ）](#-よくある質問faq)

### 🆘 **最終手段**
- [完全リセット手順](#-完全リセット手順)
- [サポート連絡方法](#-サポート連絡方法)

---

## 🐍 Python環境の問題

### ❌ **症状**: `Python not found` / `python: command not found`

#### 🔍 **原因**
- Pythonがインストールされていない
- PATHが正しく設定されていない
- 間違ったPythonバージョンを使用している

#### ✅ **解決方法**

##### **Step 1: Pythonバージョン確認**
```bash
# コマンドプロンプト/ターミナルで実行
python --version
python3 --version
```

**期待される結果**: `Python 3.9.x` 以上

##### **Step 2: Pythonインストール（未インストールの場合）**

**Windows:**
1. [Python公式サイト](https://www.python.org/downloads/) からダウンロード
2. **重要**: インストール時に「Add Python to PATH」をチェック ✅
3. インストール後、コマンドプロンプトを再起動
4. `python --version` で確認

**macOS:**
```bash
# Option 1: 公式インストーラー
# https://www.python.org/downloads/ からダウンロード

# Option 2: Homebrewを使用（推奨）
brew install python
```

##### **Step 3: PATH設定の修正**

**Windows（手動PATH設定）:**
1. 「環境変数の編集」を検索して開く
2. 「システム環境変数」→「Path」→「編集」
3. 以下のパスを追加:
   - `C:\Users\[ユーザー名]\AppData\Local\Programs\Python\Python39\`
   - `C:\Users\[ユーザー名]\AppData\Local\Programs\Python\Python39\Scripts\`
4. コマンドプロンプトを再起動

**macOS（Zsh設定）:**
```bash
# ~/.zshrcファイルに追加
echo 'export PATH="/usr/local/bin/python3:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### ❌ **症状**: `Virtual environment not found` / 仮想環境エラー

#### 🔍 **原因**
- 初回セットアップが未実行
- `.venv`フォルダが破損・削除されている
- Python環境の変更（バージョンアップ等）

#### ✅ **解決方法**

##### **Step 1: 初回セットアップの実行**
```bash
# Windows
WINDOWS\初回セットアップ.bat

# macOS
MAC/初回セットアップ.command
```

##### **Step 2: 手動での仮想環境作成**
```bash
# 現在のフォルダでターミナル/コマンドプロンプトを開く
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux  
source .venv/bin/activate

# 依存関係のインストール
pip install -e .
```

##### **Step 3: 仮想環境の確認**
```bash
# 仮想環境がアクティブかチェック
python --version
pip list | grep kumihan
```

### ❌ **症状**: `pip: command not found` / pipエラー

#### 🔍 **原因**
- pipがインストールされていない
- 古いPythonバージョン
- 仮想環境が正しくアクティベートされていない

#### ✅ **解決方法**

##### **Step 1: pipの確認・インストール**
```bash
# pipバージョン確認
pip --version

# pipがない場合の手動インストール
python -m ensurepip --upgrade
```

##### **Step 2: pipの更新**
```bash
# pipを最新に更新
python -m pip install --upgrade pip
```

##### **Step 3: 仮想環境での実行確認**
```bash
# 仮想環境内でのpip確認
which pip  # macOS/Linux
where pip  # Windows
```

---

## 📝 エンコーディング・文字化け問題

### ❌ **症状**: テキストファイルが文字化けして読み込めない

#### 🔍 **原因**
- ファイルがUTF-8でない文字コードで保存されている
- BOM（Byte Order Mark）付きUTF-8での保存
- エディタの設定が適切でない

#### ✅ **解決方法**

##### **Step 1: 推奨テキストエディタの使用**

**Windows推奨エディタ:**
1. **VSCode（最推奨）**
   - 無料、高機能、UTF-8デフォルト
   - ダウンロード: https://code.visualstudio.com/
   
2. **Notepad++（軽量）**
   - 文字コード変換機能あり
   - ダウンロード: https://notepad-plus-plus.org/

3. **サクラエディタ（日本語特化）**
   - 日本語環境に最適化
   - 文字コード自動判定機能

**macOS推奨エディタ:**
1. **VSCode（最推奨）**
2. **CotEditor（macOS専用）**
   - Mac App Storeから無料ダウンロード
   - 軽量でUTF-8対応良好

##### **Step 2: UTF-8での保存方法**

**VSCodeでの保存:**
1. ファイルを開く
2. 画面右下の「エンコーディング」をクリック
3. 「UTF-8で保存」を選択
4. `Ctrl+S`（Windows）/ `Cmd+S`（macOS）で保存

**メモ帳での保存（Windows）:**
1. 「ファイル」→「名前を付けて保存」
2. 「エンコード」を「UTF-8」に変更
3. **注意**: 「UTF-8（BOM付き）」は選択しない

**CotEditorでの保存（macOS）:**
1. 「フォーマット」→「エンコーディング」→「UTF-8」
2. `Cmd+S`で保存

##### **Step 3: BOM問題の解決**

**BOM付きUTF-8の確認方法:**
```bash
# macOS/Linux
file -bi ファイル名.txt

# 結果に "charset=utf-8" と表示されればOK
# "charset=utf-8-bom" と表示される場合は要修正
```

**BOM除去方法:**
```bash
# macOS/Linuxでの一括BOM除去
sed -i '1s/^\xEF\xBB\xBF//' ファイル名.txt
```

### ❌ **症状**: コンソール・コマンドプロンプトで日本語が文字化け

#### 🔍 **原因**
- コンソールの文字コード設定
- フォント設定の問題
- 地域設定の問題

#### ✅ **解決方法**

##### **Windows コマンドプロンプト:**
```bash
# セッション単位での設定変更
chcp 65001

# 永続的な設定変更（管理者権限で実行）
reg add HKLM\SOFTWARE\Microsoft\Command^ Processor /v Autorun /t REG_SZ /d "chcp 65001"
```

##### **Windows PowerShell（推奨）:**
```powershell
# PowerShellでのエンコーディング設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

##### **macOS Terminal:**
```bash
# ~/.zshrcまたは~/.bashrcに追加
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8

# 設定の反映
source ~/.zshrc  # Zshの場合
source ~/.bashrc # Bashの場合
```

##### **フォント設定:**

**Windows:**
- コマンドプロンプトのプロパティ → フォント → 「MS ゴシック」または「Consolas」

**macOS:**
- Terminal → 環境設定 → プロファイル → フォント → 「SF Mono」または「Menlo」

---

## ⚙️ 変換エラーの詳細対処

### ❌ **症状**: Kumihan記法エラー / 構文エラー

#### 🔍 **原因**
- 記法の書き方が間違っている
- 閉じマーカー`;;;`の不足
- 無効なキーワードの使用

#### ✅ **解決方法**

##### **Step 1: 記法エラーチェッカーの使用**
```bash
# 仮想環境をアクティベート後
python -m kumihan_formatter.cli check-syntax ファイル名.txt
```

**出力例:**
```
🔍 1 ファイルで 2 個の記法エラーが見つかりました:

📁 sample.txt
  ❌ Line 5: 未知のキーワードです: '太文字'
     Context: ;;;太文字
     💡 Suggestion: もしかして: 太字

  ⚠️ Line 12: ブロックが ;;; で閉じられていません
     Context: ;;;見出し1
     💡 Suggestion: ブロックの最後に ;;; を追加してください
```

##### **Step 2: よくある記法エラーと修正方法**

**1. 間違ったキーワード:**
```text
❌ 間違い:
;;;太文字
内容
;;;

✅ 正しい:
;;;太字
内容
;;;
```

**2. 閉じマーカーの不足:**
```text
❌ 間違い:
;;;見出し1
タイトル

✅ 正しい:
;;;見出し1
タイトル
;;;
```

**3. マーカーの位置間違い:**
```text
❌ 間違い:
これは ;;;太字 文字;;; です。

✅ 正しい（ブロック記法）:
;;;太字
文字
;;;

✅ 正しい（リスト内記法）:
- ;;;太字;;; 文字
```

**4. 複合記法の間違い:**
```text
❌ 間違い:
;;;太字、見出し1
内容
;;;

✅ 正しい:
;;;太字+見出し1
内容
;;;
```

##### **Step 3: デバッグ用の最小コード作成**
```text
# debug-minimal.txt
;;;見出し1
テスト見出し
;;;

通常の段落です。

;;;太字
太字のテスト
;;;
```

このファイルで変換をテストし、段階的に内容を追加して問題箇所を特定します。

### ❌ **症状**: `FileNotFoundError` / ファイルが見つからない

#### 🔍 **原因**
- ファイルパスの指定間違い
- ファイル名の日本語・特殊文字
- 作業ディレクトリの問題

#### ✅ **解決方法**

##### **Step 1: ファイルパスの確認**
```bash
# 現在のディレクトリ確認
pwd          # macOS/Linux
cd           # Windows

# ファイル一覧表示
ls           # macOS/Linux  
dir          # Windows

# ファイルの存在確認
ls -la *.txt # macOS/Linux
dir *.txt    # Windows
```

##### **Step 2: ファイル名の注意点**

**避けるべき文字:**
- 日本語スペース（全角空白）
- 特殊文字: `<>:"/|?*`
- 先頭・末尾のスペース

**推奨ファイル名パターン:**
```text
✅ 良い例:
sample.txt
scenario_001.txt
my-scenario.txt

❌ 悪い例:
サンプル　ファイル.txt（全角スペース）
scenario<1>.txt（特殊文字）
 sample.txt （先頭スペース）
```

##### **Step 3: 絶対パスでの指定**
```bash
# Windows例
python -m kumihan_formatter.cli "C:\Users\ユーザー名\Documents\sample.txt"

# macOS例
python -m kumihan_formatter.cli "/Users/ユーザー名/Documents/sample.txt"
```

### ❌ **症状**: `PermissionError` / `Access denied`

#### 🔍 **原因**
- ファイルが他のアプリで開かれている
- 読み取り専用ファイル
- ディスク容量不足
- 管理者権限の問題

#### ✅ **解決方法**

##### **Step 1: ファイルの使用状況確認**
1. **Word、Excel、メモ帳等でファイルを開いていないか確認**
2. **すべてのエディタ・ビューアを閉じる**
3. **OneDrive、Dropbox等の同期中でないか確認**

##### **Step 2: ファイル属性の確認・変更**

**Windows:**
```bash
# ファイル属性確認
attrib ファイル名.txt

# 読み取り専用解除
attrib -R ファイル名.txt
```

**macOS:**
```bash
# ファイル権限確認
ls -la ファイル名.txt

# 書き込み権限追加
chmod 644 ファイル名.txt
```

##### **Step 3: 管理者権限での実行**

**Windows:**
1. コマンドプロンプトを「管理者として実行」
2. または PowerShellを「管理者として実行」

**macOS:**
```bash
# sudo使用（パスワード入力が必要）
sudo python -m kumihan_formatter.cli sample.txt
```

---

## 🪟 Windows固有の問題

### ❌ **症状**: Windows Defender / ウイルス対策ソフトの警告

#### 🔍 **原因**
- batファイルがマルウェアと誤認される
- Pythonスクリプトの実行がブロックされる
- リアルタイム保護による干渉

#### ✅ **解決方法**

##### **Step 1: Windows Defenderの除外設定**
1. **Windows設定 → 更新とセキュリティ → Windows セキュリティ**
2. **ウイルスと脅威の防止 → 設定の管理**
3. **除外の追加または削除 → 除外を追加**
4. **フォルダ** → Kumihan-Formatterフォルダ全体を指定

##### **Step 2: 実行ポリシーの確認・変更**
```powershell
# 現在の実行ポリシー確認
Get-ExecutionPolicy

# 実行ポリシーの変更（管理者権限で実行）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

##### **Step 3: 代替実行方法**
```bash
# PowerShellでの直接実行（batファイル回避）
python -m kumihan_formatter.cli sample.txt -o output/
```

### ❌ **症状**: 長いパス名 / パスが長すぎるエラー

#### 🔍 **原因**
- Windowsの260文字パス制限
- 深いフォルダ階層
- 日本語による文字数増加

#### ✅ **解決方法**

##### **Step 1: 長いパス名のサポート有効化**
```bash
# 管理者権限のコマンドプロンプトで実行
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1
```

##### **Step 2: 短いパスでの回避**
```bash
# デスクトップに移動して実行
cd %USERPROFILE%\Desktop
python -m kumihan_formatter.cli sample.txt
```

##### **Step 3: ネットワークドライブの活用**
```bash
# 短い文字のドライブにマッピング
subst K: "C:\Users\長い名前のユーザー\Documents\プロジェクト\"
cd K:\
```

---

## 🍎 macOS固有の問題

### ❌ **症状**: Gatekeeper / アプリケーションが開けない警告

#### 🔍 **原因**
- 未署名のcommandファイル
- macOSのセキュリティ設定
- ダウンロードファイルの検疫属性

#### ✅ **解決方法**

##### **Step 1: 検疫属性の削除**
```bash
# Kumihan-Formatterフォルダで実行
xattr -dr com.apple.quarantine .
```

##### **Step 2: 実行権限の付与**
```bash
# すべての.commandファイルに実行権限付与
chmod +x MAC/*.command
```

##### **Step 3: セキュリティ設定の調整**
1. **システム環境設定 → セキュリティとプライバシー**
2. **「ダウンロードしたアプリケーションの実行許可」**
3. **「App Storeと確認済みの開発元からのアプリケーションを許可」**

##### **Step 4: 個別ファイルの許可**
```bash
# 初回実行時に表示される「開く」を選択
# または、Controlキー + クリック → 「開く」
```

### ❌ **症状**: SIP（System Integrity Protection）関連エラー

#### 🔍 **原因**
- システムディレクトリへの書き込み
- 保護されたファイルの変更
- rootkitとの誤認

#### ✅ **解決方法**

##### **Step 1: ユーザーディレクトリでの実行**
```bash
# ホームディレクトリまたはDocumentsで実行
cd ~/Documents/Kumihan-Formatter
python -m kumihan_formatter.cli sample.txt
```

##### **Step 2: Homebrewでの Python使用**
```bash
# システムPythonではなくHomebrewのPythonを使用
brew install python
which python3  # /usr/local/bin/python3 を確認
```

---

## 📁 ファイル・権限関連の問題

### ❌ **症状**: ファイルが作成されない / 出力フォルダにファイルがない

#### 🔍 **原因**
- 出力ディレクトリの権限不足
- ディスク容量不足
- ファイル名の衝突
- プロセスの途中終了

#### ✅ **解決方法**

##### **Step 1: 詳細ログでの実行**
```bash
# 詳細ログを有効にして実行
python -m kumihan_formatter.cli sample.txt -o output/ --verbose
```

##### **Step 2: ディスク容量の確認**
```bash
# Windows
dir C:\ /-c

# macOS/Linux
df -h
```

##### **Step 3: 権限確認と修正**
```bash
# macOS/Linux
ls -la output/
chmod 755 output/
chmod 644 output/*
```

##### **Step 4: 一時ディレクトリでのテスト**
```bash
# Windows
python -m kumihan_formatter.cli sample.txt -o %TEMP%\test_output

# macOS/Linux
python -m kumihan_formatter.cli sample.txt -o /tmp/test_output
```

---

## 🔍 デバッグ手法

### 🕵️ **段階的問題切り分け手順**

#### **Level 1: 環境確認**
```bash
# Python環境の基本確認
python --version
pip --version
which python  # macOS/Linux
where python  # Windows

# Kumihan-Formatterの確認
python -c "import kumihan_formatter; print('OK')"
```

#### **Level 2: 最小限ファイルでのテスト**
```text
# test-minimal.txt（最小限のテストファイル）
;;;見出し1
テスト
;;;

これは通常の段落です。
```

```bash
# 最小限ファイルでの変換テスト
python -m kumihan_formatter.cli test-minimal.txt -o test-output/
```

#### **Level 3: 記法チェック**
```bash
# 構文エラーの詳細確認
python -m kumihan_formatter.cli check-syntax 問題のファイル.txt
```

#### **Level 4: 詳細デバッグ**
```bash
# 詳細ログでの実行
python -m kumihan_formatter.cli 問題のファイル.txt --verbose --debug
```

### 📊 **ログファイルの確認方法**

#### **ログファイルの場所**
```bash
# Windows
%APPDATA%\kumihan-formatter\logs\

# macOS
~/Library/Logs/kumihan-formatter/

# Linux
~/.local/share/kumihan-formatter/logs/
```

#### **ログの読み方**
```text
[2024-06-26 10:30:00] INFO: 変換開始: sample.txt
[2024-06-26 10:30:01] DEBUG: 1行目を処理中: ;;;見出し1
[2024-06-26 10:30:01] WARNING: 不明なキーワード検出: 太文字
[2024-06-26 10:30:01] ERROR: 構文エラー 5行目: 閉じマーカーなし
[2024-06-26 10:30:02] INFO: 変換完了: 16ブロック処理
```

### 🐛 **エラーメッセージの解読**

#### **一般的なエラーパターン**

**1. `ModuleNotFoundError: No module named 'kumihan_formatter'`**
```bash
# 解決方法: 仮想環境の確認とインストール
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
pip install -e .
```

**2. `UnicodeDecodeError: 'utf-8' codec can't decode`**
```bash
# 解決方法: ファイルエンコーディングの確認・変換
file -bi ファイル名.txt     # macOS/Linux
iconv -f SHIFT_JIS -t UTF-8 古いファイル.txt > 新しいファイル.txt
```

**3. `OSError: [Errno 28] No space left on device`**
```bash
# 解決方法: ディスク容量の確保
du -sh /tmp/*     # macOS/Linux
dir C:\temp /s    # Windows
```

---

## 🛡️ 予防的対策

### 🏗️ **推奨環境構築**

#### **最適なディレクトリ構造**
```text
Kumihan-Formatter/
├── projects/           # プロジェクトファイル
│   ├── scenario1.txt
│   └── scenario2.txt
├── output/            # 変換結果
├── backup/            # バックアップ
└── templates/         # テンプレート
```

#### **推奨ファイル命名規則**
```text
✅ 推奨:
scenario_001.txt
my-project_v2.txt
sample-text.txt

❌ 非推奨:
シナリオ　１.txt
sample(final).txt
test file.txt
```

### 🔄 **定期メンテナンス**

#### **月次チェック項目**
```bash
# 1. Pythonの更新確認
python --version

# 2. 依存関係の更新
pip list --outdated

# 3. ディスク容量確認
df -h  # macOS/Linux
dir C:\ /-c  # Windows

# 4. バックアップの作成
cp -r projects/ backup/backup_$(date +%Y%m%d)/  # macOS/Linux
```

#### **年次チェック項目**
- Python環境の刷新（新しい仮想環境作成）
- 不要ファイルの削除
- セキュリティ設定の見直し
- ドキュメントの更新確認

---

## ❓ よくある質問（FAQ）

### **Q1: 変換にどのくらい時間がかかりますか？**
**A:** ファイルサイズによって異なります：
- 1-10KB（A4数ページ分）: 1-3秒
- 10-100KB（小説1章分）: 3-10秒  
- 100KB-1MB（長編小説）: 10-60秒

### **Q2: 同時に複数ファイルを変換できますか？**
**A:** 現在は単一ファイルのみサポートしています。複数ファイルの場合は：
```bash
# バッチ処理（Windows）
for %f in (*.txt) do python -m kumihan_formatter.cli "%f"

# バッチ処理（macOS/Linux）
for file in *.txt; do python -m kumihan_formatter.cli "$file"; done
```

### **Q3: HTMLファイルのカスタマイズは可能ですか？**
**A:** はい、以下の方法があります：
- CSS設定ファイルの編集（`config/custom.yaml`）
- テンプレートファイルの変更（上級者向け）

### **Q4: 他の形式（PDF、EPUB）への対応予定は？**
**A:** v2.0以降で検討中です。現在はHTMLのみサポートしています。

### **Q5: 商用利用は可能ですか？**
**A:** 個人利用に限定されています。商用利用については開発者にお問い合わせください。

---

## 🆘 完全リセット手順

### 🔄 **段階的リセット手順**

#### **Level 1: 仮想環境のリセット**
```bash
# 1. 現在の仮想環境を削除
rm -rf .venv     # macOS/Linux
rmdir /s .venv   # Windows

# 2. 新しい仮想環境を作成
python -m venv .venv

# 3. 仮想環境のアクティベート
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 4. 依存関係の再インストール
pip install -e .
```

#### **Level 2: 設定ファイルのリセット**
```bash
# 設定ファイルの削除（バックアップ後）
# Windows
del "%APPDATA%\kumihan-formatter\*"

# macOS
rm -rf ~/Library/Preferences/kumihan-formatter/

# Linux
rm -rf ~/.config/kumihan-formatter/
```

#### **Level 3: 完全なクリーンインストール**
```bash
# 1. Kumihan-Formatterフォルダ全体を削除
cd ..
rm -rf Kumihan-Formatter/  # macOS/Linux
rmdir /s Kumihan-Formatter\ # Windows

# 2. 新しいダウンロード
# GitHubから最新版をダウンロード

# 3. 初回セットアップの実行
# Windows: WINDOWS\初回セットアップ.bat
# macOS: MAC/初回セットアップ.command
```

### 🔧 **リセット後の確認項目**
```bash
# 1. Python環境の確認
python --version
pip --version

# 2. Kumihan-Formatterの動作確認
python -m kumihan_formatter.cli --help

# 3. 最小限ファイルでのテスト
echo ";;;見出し1\nテスト\n;;;" > test.txt
python -m kumihan_formatter.cli test.txt
```

---

## 📞 サポート連絡方法

### 🎯 **効果的なサポート依頼の書き方**

#### **必須情報**
```text
【環境情報】
- OS: Windows 11 / macOS Ventura / Ubuntu 22.04 など
- Pythonバージョン: python --version の結果
- Kumihan-Formatterバージョン: 

【問題の詳細】
- 何をしようとしていたか
- 発生した症状・エラーメッセージ（完全なコピー）
- 期待していた結果

【再現手順】
1. 具体的な操作手順
2. 使用したファイル（可能であれば添付）
3. 実行したコマンド

【試したこと】
- このガイドで試した解決方法
- 結果（改善した/変化なし/悪化した）
```

#### **サポート報告テンプレート**
```markdown
## 問題報告

### 環境
- **OS**: 
- **Pythonバージョン**: 
- **エラー発生日時**: 

### 問題の詳細
<!-- 具体的に何が起こったかを記述 -->

### エラーメッセージ
```
<!-- エラーメッセージをここに貼り付け -->
```

### 再現手順
1. 
2. 
3. 

### 試した解決方法
<!-- このガイドで試した項目をチェック -->
- [ ] Python環境の確認
- [ ] エンコーディングの確認
- [ ] 記法チェックの実行
- [ ] 完全リセット

### 添付ファイル
<!-- 可能であれば問題のファイルを添付 -->
```

### 📋 **サポートチャンネル**

#### **GitHub Issues（推奨）**
- URL: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues
- 新しいIssueを作成
- テンプレートに従って記入

#### **緊急度別の対応**

**🚨 緊急（変換不可）**: 24時間以内の返信目標
**⚠️ 通常（機能障害）**: 48時間以内の返信目標  
**💡 要望・質問**: 1週間以内の返信目標

---

## 📊 トラブルシューティング成功率向上のコツ

### 🎯 **効果的なトラブルシューティング手順**

1. **症状の正確な把握** - エラーメッセージの完全なコピー
2. **段階的なアプローチ** - 簡単な解決方法から試す
3. **一つずつの変更** - 複数の修正を同時に行わない
4. **変更内容の記録** - 何を変更したかメモを取る
5. **バックアップの作成** - 重要なファイルは事前にコピー

### 💡 **予防のベストプラクティス**

- **定期的なバックアップ** - 重要なプロジェクトは日次バックアップ
- **段階的な作業** - 大きなファイルも小分けして変換
- **環境の統一** - 開発環境と本番環境を合わせる
- **ドキュメントの更新** - 新しい問題と解決方法の記録

---

**このガイドが問題解決に役立たない場合は、遠慮なくサポートにご連絡ください。**
**初心者の方でも安心してKumihan-Formatterをご活用いただけるよう、継続的にサポートいたします。**

---

*最終更新: 2025-06-26*  
*ガイド版数: v1.0 (Issue #130 対応版)*