# 👶 初心者向けSerena-local導入ガイド

> 段階的導入で確実にSerena-localを使えるようになる

## 🎯 このガイドについて

このガイドでは、プログラミング初心者や設定作業に慣れていない方が、安全にSerena-localを導入できるように段階的な手順を提供します。

**重要：このガイドは実際に動作する手順のみを記載しています。**

## ⚠️ 開始前の確認事項

### 必要な前提知識
- **基本的なコマンドライン操作**: ターミナル/コマンドプロンプトで簡単なコマンドを実行できる
- **ファイル編集の基本**: テキストエディタでファイルを開き、保存できる
- **JSON形式の理解**: 基本的なJSON構文（括弧、カンマの位置）を理解している

### 推定所要時間
- **準備段階**: 30分
- **基本設定**: 1時間
- **動作確認**: 30分
- **合計**: 約2時間

### 必要なツール
```bash
# これらのコマンドが使えることを確認
python --version  # Python 3.12以上
git --version     # Git（最新版推奨）
```

## 📋 段階1: 環境確認（30分）

### 1.1 Claude Desktopの確認
```bash
# Claude Desktopが最新版であることを確認
# アプリケーションのバージョン情報を確認してください
```

### 1.2 Python環境の確認
```bash
# Pythonバージョン確認
python --version

# 3.12より古い場合は更新が必要
# Ubuntu/Debian
sudo apt update && sudo apt install python3.12

# macOS (Homebrew)
brew install python@3.12
```

### 1.3 UVのインストール
```bash
# UVがインストールされているか確認
uv --version

# インストールされていない場合
curl -LsSf https://astral.sh/uv/install.sh | sh

# ターミナルを再起動または
source ~/.bashrc  # または ~/.zshrc
```

### 1.4 設定ファイルの場所確認
```bash
# macOSの場合
ls ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linuxの場合
ls ~/.config/claude_desktop/config.json

# どちらか一つが存在すればOK
# 存在しない場合は空のファイルを作成
mkdir -p ~/.config/claude_desktop/
echo '{}' > ~/.config/claude_desktop/config.json  # Linux
# または
mkdir -p ~/Library/Application\ Support/Claude/
echo '{}' > ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS
```

## 🔧 段階2: Serena-localの準備（1時間）

### 2.1 作業ディレクトリの準備
```bash
# ホームディレクトリに移動
cd ~

# serenaプロジェクト用ディレクトリ作成
mkdir -p GitHub
cd GitHub
```

### 2.2 Serena-localのクローン
```bash
# ✅ このプロジェクトには既にSerenaが含まれています
cd serena  # 既存のserenaディレクトリを使用

# 正常にディレクトリが存在するか確認
ls -la
# pyproject.toml などのファイルが表示されればOK
```

### 2.3 仮想環境の作成とインストール
```bash
# 仮想環境作成
uv venv

# 仮想環境有効化
source .venv/bin/activate  # Linux/macOS
# または (Windows)
.venv\Scripts\activate

# インストール実行
uv pip install -e .

# 正常にインストールされたか確認
python -m serena_local --help
# ヘルプメッセージが表示されればOK
```

### 2.4 インストール確認
```bash
# serenaの場所を記録
pwd  # このパスを控えておいてください
# 例: /home/user/GitHub/serena
```

## ⚙️ 段階3: Claude Desktop設定（30分）

### 3.1 設定ファイルのバックアップ
```bash
# 既存設定のバックアップ（macOS）
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# 既存設定のバックアップ（Linux）
cp ~/.config/claude_desktop/config.json ~/.config/claude_desktop/config.json.backup
```

### 3.2 設定ファイルの編集準備
```bash
# 現在の設定内容確認（macOS）
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 現在の設定内容確認（Linux）
cat ~/.config/claude_desktop/config.json
```

### 3.3 設定の追加
設定ファイルに以下を追加してください。**パスは段階2.4で控えたパスに置き換えてください。**

**完全に空の設定ファイルの場合:**
```json
{
  "mcpServers": {
    "serena": {
      "command": "python",
      "args": [
        "-m",
        "serena_local"
      ],
      "cwd": "/home/user/GitHub/serena",
      "env": {}
    }
  }
}
```

**既存の設定がある場合:**
既存の`mcpServers`セクションに`serena`を追加:
```json
{
  "mcpServers": {
    "existing-server": {
      "command": "existing-command"
    },
    "serena": {
      "command": "python",
      "args": ["-m", "serena_local"],
      "cwd": "/home/user/GitHub/serena",
      "env": {}
    }
  }
}
```

### 3.4 設定の検証
```bash
# JSON構文エラーがないかチェック（macOS）
python -c "import json; json.load(open(os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json')))" && echo "JSON OK"

# JSON構文エラーがないかチェック（Linux）
python -c "import json; json.load(open(os.path.expanduser('~/.config/claude_desktop/config.json')))" && echo "JSON OK"

# エラーが出た場合は構文を確認してください
```

## ✅ 段階4: 動作確認（30分）

### 4.1 Claude Desktopの再起動
1. Claude Desktopアプリケーションを完全に終了
2. 5秒待機
3. Claude Desktopを再起動
4. 新しい会話を開始

### 4.2 基本動作テスト
Claude Codeで以下のように依頼してください:

```text
Kumihan-Formatterプロジェクトの構造を教えてください
```

**期待される結果:**
- `mcp__serena__get_symbols_overview`などのツールが使用される
- プロジェクトの構造情報が表示される

### 4.3 詳細動作テスト
```text
kumihan_formatterディレクトリの主要なクラスを表示してください
```

**期待される結果:**
- `mcp__serena__find_symbol`ツールが使用される
- Pythonクラスの一覧が表示される

## 🔍 段階5: トラブルシューティング（必要時）

### 5.1 serenaが認識されない場合

**確認事項:**
```bash
# パスが正しいか確認
ls /home/user/GitHub/serena/pyproject.toml

# 仮想環境が有効か確認
cd /home/user/GitHub/serena
source .venv/bin/activate
python -m serena_local --help
```

**解決策:**
- パスを再確認し、設定ファイルを更新
- Claude Desktopを再起動

### 5.2 JSON構文エラーがある場合

**確認方法:**
```bash
# 設定ファイルの構文チェック
python -m json.tool < ~/.config/claude_desktop/config.json
```

**解決策:**
- バックアップから復元
- カンマ、括弧の位置を確認
- オンラインJSON構文チェッカーを利用

### 5.3 権限エラーがある場合

**解決策:**
```bash
# ファイル権限修正
chmod 644 ~/.config/claude_desktop/config.json
# または
chmod 644 ~/Library/Application\ Support/Claude/claude_desktop_config.json

# ディレクトリ権限修正
chmod 755 ~/.config/claude_desktop/
# または
chmod 755 ~/Library/Application\ Support/Claude/
```

## 📈 段階6: 応用利用（慣れてから）

### 6.1 プロジェクト固有設定
Kumihan-Formatterプロジェクトで作業する際:
```bash
# プロジェクトディレクトリに移動
cd /path/to/Kumihan-Formatter

# Python パスの設定（必要に応じて）
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### 6.2 よく使う操作
```text
# Claude Codeでの一般的な依頼例
- 「ファイルXXXのクラス一覧を表示してください」
- 「関数YYYの実装を見せてください」
- 「ファイルZZZで使用されているインポートを確認してください」
```

### 6.3 パフォーマンス最適化
- 大きなプロジェクトでは部分的なディレクトリを指定
- 必要に応じて仮想環境を再作成
- Claude Desktopの再起動で問題解決することが多い

## 🎯 成功の判断基準

### 完了チェックリスト
- [ ] Python 3.12以上がインストール済み
- [ ] UVがインストール済み
- [ ] serenaがクローン・インストール完了
- [ ] Claude Desktop設定ファイル編集完了
- [ ] JSON構文エラーなし
- [ ] Claude Desktop再起動完了
- [ ] 基本動作テスト成功
- [ ] Kumihan-Formatterでの動作確認完了

### 期待される体験
- Claude CodeでSerenaツールが自動的に使用される
- `find_symbol`、`get_symbols_overview`等が利用可能
- コードの精密な編集・分析が可能
- プロジェクト構造の詳細な把握が可能

## 🚨 注意点とよくある誤解

### やってはいけないこと
- 設定ファイルを手動で複雑にカスタマイズ
- 複数のserenaを同時インストール
- 仮想環境を有効化しないまま作業

### よくある誤解
- **誤解**: 「一度設定すれば永久に動作する」
- **現実**: 環境変更時に再設定が必要な場合がある

- **誤解**: 「エラーが出たら諦めるしかない」
- **現実**: ほとんどの問題は設定確認で解決可能

## 📞 困った時の相談先

### 自分で解決を試みる順序
1. このガイドの段階を順番に再確認
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)を参照
3. 設定ファイルをバックアップから復元
4. serenaを再インストール

### GitHub Issueでの相談
- **対象**: 手順通り実行してもエラーが解決しない場合
- **準備**: エラーメッセージ、実行コマンド、環境情報を記録
- **タイトル**: [Setup Kit] [初心者] 具体的な問題

---

**このガイドは初心者の方々の実際の体験に基づいて作成されています。**  
**不明な点があれば、一つずつ確実に進めることが成功の鍵です。**

*Kumihan-Formatter Serena Setup Kit - Beginner's Guide v1.0*