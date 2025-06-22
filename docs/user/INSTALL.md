# Kumihan-Formatter インストールガイド

## 前提条件

- **Python 3.9以上**がインストールされていること
- **pip**（Pythonパッケージマネージャー）が使用可能なこと

### Pythonのインストール確認

```bash
# バージョン確認
python --version
# または
python3 --version
```

Python 3.9以上が表示されれば準備完了です。

### Pythonのインストール方法

#### Windows
1. [python.org](https://www.python.org/downloads/)から最新版をダウンロード
2. インストーラーを実行
3. **"Add Python to PATH"にチェック**を入れてインストール

#### macOS
```bash
# Homebrewを使用
brew install python

# または公式インストーラーを使用
# python.orgからダウンロード
```

## インストール方法

### 1. 基本インストール（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# インストール
pip install -e .
```

### 2. 開発環境のインストール

開発やテストを行う場合は、追加の依存関係をインストールします：

```bash
# 仮想環境の作成（推奨）
python -m venv .venv

# 仮想環境の有効化
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 開発用依存関係を含めてインストール
pip install -e ".[dev]"
```

### 3. グローバルインストール

システム全体で使用したい場合：

```bash
pip install .
```

## インストール確認

インストールが成功したか確認：

```bash
# コマンドの確認
kumihan --help

# または
python -m kumihan_formatter --help
```

## アンインストール

```bash
pip uninstall kumihan-formatter
```

## トラブルシューティング

### pipが見つからない場合

```bash
# pipのインストール
python -m ensurepip --upgrade
```

### 権限エラーが発生する場合

```bash
# ユーザー領域にインストール
pip install --user -e .
```

### 依存関係の問題

```bash
# 依存関係を再インストール
pip install --upgrade -r requirements.txt
```

## 次のステップ

インストールが完了したら：
- [クイックスタート](QUICK_START.txt)で基本的な使い方を確認
- [記法一覧](SYNTAX_CHEATSHEET.txt)で記法を学習
- [ダブルクリックガイド](DOUBLE_CLICK_GUIDE.md)で簡単な使い方を確認