# 📦 Serena-local インストールガイド

> Kumihan-Formatter開発環境でのserena設定手順

## 🎯 このガイドについて

このガイドでは、Kumihan-FormatterプロジェクトでSerena-localを利用するための実際の設定手順を説明します。

**重要：全ての手順は手動で実行する必要があります。**

## ⚠️ 事前準備

### 必須確認事項
```bash
# Claude Desktopのバージョン確認
# 最新版である必要があります

# Python 3.12以上の確認
python --version  # 3.12.x以上必須

# Node.js 18以上の確認
node --version  # v18.x.x以上推奨

# UVの確認
uv --version  # 最新版推奨
```

### バックアップ作成
```bash
# Claude Desktop設定のバックアップ
cp ~/.config/claude_desktop/config.json ~/.config/claude_desktop/config.json.backup

# または macOSの場合
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup
```

## 🔧 Step 1: Serena-localのインストール

### 1.1 リポジトリのクローン
```bash
# ✅ このプロジェクトには既にSerenaが含まれています
cd ./serena  # 既存のSerenaディレクトリを使用
```

### 1.2 依存関係のインストール
```bash
# Python依存関係のインストール
uv venv
source .venv/bin/activate  # Linuxの場合
# または
.venv\Scripts\activate  # Windowsの場合

uv pip install -e .
```

### 1.3 動作確認
```bash
# serenaが正常にインストールされたか確認
python -m serena_local --help
```

## 🔗 Step 2: MCP設定

### 2.1 Claude Desktop設定ファイルの場所確認
```bash
# macOSの場合
ls ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linuxの場合
ls ~/.config/claude_desktop/config.json
```

### 2.2 設定ファイルの編集
Claude Desktop設定ファイルに以下を追加：

```json
{
  "mcpServers": {
    "serena": {
      "command": "python",
      "args": [
        "-m",
        "serena_local"
      ],
      "cwd": "/path/to/your/serena",
      "env": {}
    }
  }
}
```

**重要：`/path/to/your/serena`を実際のパスに置き換えてください**

### 2.3 既存設定がある場合の追加方法
既存の`mcpServers`がある場合：
```json
{
  "mcpServers": {
    "existing-server": {
      "command": "existing-command",
      "args": ["existing-args"]
    },
    "serena": {
      "command": "python",
      "args": ["-m", "serena_local"],
      "cwd": "/path/to/your/serena",
      "env": {}
    }
  }
}
```

## 🚀 Step 3: Kumihan-Formatterプロジェクトでの設定

### 3.1 プロジェクトディレクトリでの初期化
```bash
# Kumihan-Formatterプロジェクトディレクトリに移動
cd /path/to/Kumihan-Formatter

# serena用設定ファイル作成（オプション）
touch .serena_config
```

### 3.2 プロジェクト固有設定
`.serena_config`ファイル（オプション）:
```yaml
project_name: "Kumihan-Formatter"
python_version: "3.12"
code_style: "black"
lint_tools:
  - "mypy"
  - "black"
  - "isort"
```

## ✅ Step 4: 動作確認

### 4.1 Claude Desktopの再起動
1. Claude Desktopを完全に終了
2. 再起動
3. 新しい会話を開始

### 4.2 基本動作テスト
Claude Codeで以下を実行して動作確認：

```text
プロジェクトの構造を確認してください
```

serenaが正常に動作している場合、`find_symbol`や`get_symbols_overview`などのツールが利用可能になります。

### 4.3 具体的な動作確認方法
```text
kumihan_formatterディレクトリの主要ファイルのシンボルを表示してください
```

期待される応答：`mcp__serena__get_symbols_overview`が使用され、プロジェクトのクラスや関数が表示される。

## 🔍 Step 5: 高度な設定（オプション）

### 5.1 カスタムLSP設定
より高度な機能を利用する場合：
```json
{
  "mcpServers": {
    "serena": {
      "command": "python",
      "args": ["-m", "serena_local", "--lsp-config", "/path/to/lsp_config.json"],
      "cwd": "/path/to/your/serena",
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

### 5.2 メモリ最適化設定
大きなプロジェクトの場合：
```json
{
  "mcpServers": {
    "serena": {
      "command": "python",
      "args": ["-m", "serena_local", "--max-memory", "2048MB"],
      "cwd": "/path/to/your/serena",
      "env": {}
    }
  }
}
```

## 🚨 よくある問題と対処法

### 問題1: serenaが認識されない
```bash
# 設定ファイルの構文確認
python -m json.tool < ~/.config/claude_desktop/config.json
# またはmacOSの場合
python -m json.tool < ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 問題2: パーミッションエラー
```bash
# serenaディレクトリのパーミッション確認
ls -la /path/to/your/serena
chmod +x /path/to/your/serena
```

### 問題3: Python環境の問題
```bash
# 仮想環境の確認
which python
python --version

# serenaの再インストール
uv pip uninstall serena
uv pip install -e .
```

## 📋 設定確認チェックリスト

- [ ] Claude Desktop最新版インストール済み
- [ ] Python 3.12以上インストール済み
- [ ] serenaクローン・インストール完了
- [ ] MCP設定ファイル編集完了
- [ ] 設定ファイル構文エラーなし
- [ ] Claude Desktop再起動完了
- [ ] 基本動作確認完了
- [ ] Kumihan-Formatterプロジェクトで動作確認完了

## 🔄 設定の更新・メンテナンス

### 定期的な更新
```bash
# serenaの更新
cd /path/to/your/serena
git pull
uv pip install -e .
```

### 設定の最適化
- プロジェクトサイズに応じたメモリ設定調整
- 使用頻度に応じた機能のON/OFF
- パフォーマンス問題がある場合の設定見直し

---

**注意：この手順は実際の動作を基に作成されています。**  
**問題が発生した場合は、TROUBLESHOOTING.mdを参照してください。**

*Kumihan-Formatter Serena-local Installation Guide v1.0*