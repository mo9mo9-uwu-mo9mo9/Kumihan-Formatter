# 🐍 Python環境のトラブルシューティング

> **Python関連の問題を解決** - インストール・環境設定・依存関係の問題

[← トラブルシューティング目次に戻る](TROUBLESHOOTING.md)

---

## 📋 Python環境問題一覧

- [`Python not found` / `python: command not found`](#-症状-python-not-found--python-command-not-found)
- [`Virtual environment not found` / 仮想環境エラー](#-症状-virtual-environment-not-found--仮想環境エラー)
- [`pip: command not found` / pipエラー](#-症状-pip-command-not-found--pipエラー)
- [`ImportError` / モジュールインポートエラー](#-症状-importerror--モジュールインポートエラー)

---

## ❌ **症状**: `Python not found` / `python: command not found`

### 🔍 **原因**
- Pythonがインストールされていない
- PATHが正しく設定されていない
- 間違ったPythonバージョンを使用している

### ✅ **解決方法**

#### **Step 1: Pythonバージョン確認**
```bash
# コマンドプロンプト/ターミナルで実行
python --version
python3 --version
```

**期待される結果**: `Python 3.9.x` 以上

#### **Step 2: Pythonインストール（未インストールの場合）**

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

#### **Step 3: PATH設定の修正**

**Windows（手動PATH設定）:**
1. 「環境変数の編集」を検索して開く
2. 「システム環境変数」→「Path」→「編集」
3. 以下のパスを追加:
   - `C:\\Users\\[ユーザー名]\\AppData\\Local\\Programs\\Python\\Python39\\`
   - `C:\\Users\\[ユーザー名]\\AppData\\Local\\Programs\\Python\\Python39\\Scripts\\`
4. コマンドプロンプトを再起動

**macOS（Zsh設定）:**
```bash
# ~/.zshrcファイルに追加
echo 'export PATH="/usr/local/bin/python3:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## ❌ **症状**: `Virtual environment not found` / 仮想環境エラー

### 🔍 **原因**
- 初回セットアップが未実行
- `.venv`フォルダが破損・削除されている
- Python環境の変更（バージョンアップ等）

### ✅ **解決方法**

#### **Step 1: 初回セットアップの実行**
```bash
# Windows
WINDOWS\初回セットアップ.bat

# macOS
./MAC/初回セットアップ.command
```

#### **Step 2: 手動での仮想環境作成**
```bash
# 現在の仮想環境を削除（存在する場合）
rm -rf .venv

# 新しい仮想環境を作成
python -m venv .venv

# 仮想環境をアクティベート
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 依存関係をインストール
pip install -e .
```

#### **Step 3: 仮想環境の確認**
```bash
# 仮想環境がアクティブか確認
which python  # macOS/Linux
where python  # Windows

# 期待される結果: プロジェクト内の.venv/... が表示される
```

---

## ❌ **症状**: `pip: command not found` / pipエラー

### 🔍 **原因**
- pipがインストールされていない
- 古いPythonバージョンを使用している
- 仮想環境が正しく設定されていない

### ✅ **解決方法**

#### **Step 1: pipの確認・インストール**
```bash
# pipバージョン確認
pip --version
pip3 --version

# pipがない場合のインストール
# Windows
python -m ensurepip --upgrade

# macOS
python3 -m ensurepip --upgrade
```

#### **Step 2: pipの更新**
```bash
# pipを最新版に更新
python -m pip install --upgrade pip
```

#### **Step 3: 仮想環境での実行確認**
```bash
# 仮想環境アクティベート後
source .venv/bin/activate  # macOS
# または
.venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -e .
```

---

## ❌ **症状**: `ImportError` / モジュールインポートエラー

### 🔍 **原因**
- 必要なパッケージがインストールされていない
- 仮想環境が正しくアクティベートされていない
- パッケージのバージョン競合

### ✅ **解決方法**

#### **Step 1: 依存関係の再インストール**
```bash
# 仮想環境をアクティベート
source .venv/bin/activate  # macOS
.venv\Scripts\activate     # Windows

# 依存関係を再インストール
pip install -e .

# 特定のパッケージが見つからない場合
pip install click jinja2 pyyaml rich
```

#### **Step 2: 依存関係の完全クリア**
```bash
# 仮想環境を削除
rm -rf .venv

# 初回セットアップを再実行
# Windows: セットアップ_Windows.bat
# macOS: セットアップ_Mac.command
```

#### **Step 3: Python環境の確認**
```bash
# 正しいPython環境か確認
which python
python --version

# インストール済みパッケージ確認
pip list

# Kumihan-Formatterが表示されるかチェック
```

---

## 🔧 **高度なトラブルシューティング**

### **問題が解決しない場合**

#### **完全環境リセット**
```bash
# 1. プロジェクトディレクトリで実行
rm -rf .venv
rm -rf *.egg-info

# 2. Pythonバージョン確認
python --version  # 3.9以上か確認

# 3. 手動セットアップ
python -m venv .venv
source .venv/bin/activate  # macOS
.venv\Scripts\activate     # Windows
python -m pip install --upgrade pip
pip install -e .

# 4. 動作確認
python -m kumihan_formatter --version
```

#### **システム全体のPython確認**
```bash
# インストール済みPythonバージョン確認
ls /usr/bin/python*        # macOS/Linux
py -0                      # Windows

# 複数バージョンが存在する場合、明示的に指定
python3.9 -m venv .venv
python3.10 -m venv .venv
```

### **ログ確認**
```bash
# セットアップログの確認
cat setup.log              # macOS/Linux
type setup.log             # Windows

# エラーの詳細を確認
python -m kumihan_formatter examples/sample.txt --verbose
```

---

## 📞 **それでも解決しない場合**

以下の情報を含めて [GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues) に報告してください：

```
## Python環境情報
- OS: [Windows 10 / macOS Big Sur など]
- Pythonバージョン: [python --version の結果]
- Pythonインストール方法: [公式サイト/Homebrew/など]
- pipバージョン: [pip --version の結果]

## エラーメッセージ
[完全なエラーメッセージをコピペ]

## 試した解決方法
- [ ] セットアップスクリプト実行
- [ ] 手動仮想環境作成
- [ ] Python再インストール
- [ ] PATH設定確認
```

---

## 📚 関連リソース

- **[トラブルシューティング目次](TROUBLESHOOTING.md)** - 他の問題も確認
- **[クイックスタートガイド](QUICKSTART.md)** - 正しいセットアップ手順
- **[よくある質問](FAQ.md)** - Python関連のFAQ

---

**Python環境の問題が解決することを願っています！ 🐍✨**