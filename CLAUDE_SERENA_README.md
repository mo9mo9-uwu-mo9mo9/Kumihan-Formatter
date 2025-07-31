# 🤖 Claude Code + Serena MCP Server 統合環境

Kumihan-Formatter プロジェクト用の Claude Code + Serena MCP Server 統合起動スクリプト集です。

## 📁 スクリプト一覧

### 1. `start-claude-serena.sh`
**基本的な Serena MCP Server 起動スクリプト**
- Serena MCP Server を直接起動
- シンプルな設定で最小限の機能

### 2. `start-claude-with-serena.sh` ⭐ **推奨**
**Claude Code + Serena 統合起動スクリプト**  
- Claude Code CLI と Serena MCP Server を統合
- 美しいログ出力とエラーハンドリング
- MCP設定の自動生成
- 依存関係の自動チェック

### 3. `setup-claude-alias.sh`
**エイリアス設定スクリプト**
- `claude-kumihan` エイリアスを自動設定
- シェル自動検出（bash/zsh/fish対応）
- どこからでも一発起動可能

## 🚀 クイックスタート

### ステップ1: 必要な依存関係をインストール

```bash
# Claude Code CLI のインストール
# https://docs.anthropic.com/claude-code からインストール

# uv のインストール（Python パッケージマネージャー）
pip install uv
```

### ステップ2: スクリプトの実行権限を確認

```bash
cd /Users/m2_macbookair_3911/GitHub/Kumihan-Formatter
ls -la *.sh

# 実行権限が付いていない場合
chmod +x *.sh
```

### ステップ3: 統合環境を起動

#### 方法A: 直接起動 (推奨)
```bash
./start-claude-with-serena.sh
```

#### 方法B: エイリアス設定後に起動
```bash
# エイリアス設定
./setup-claude-alias.sh

# 新しいターミナルで、どこからでも
claude-kumihan
```

## 🛠️ 設定詳細

### Serena MCP Server 設定

- **リポジトリ**: `git+https://github.com/oraios/serena`
- **コンテキスト**: `ide-assistant`
- **プロジェクト**: `/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter`

### 利用可能な Serena ツール

| ツール名 | 機能 | 説明 |
|---------|------|------|
| `mcp__serena__find_symbol` | シンボル検索 | クラス、メソッド、変数の検索 |
| `mcp__serena__search_for_pattern` | パターン検索 | 正規表現によるコード検索 |
| `mcp__serena__replace_symbol_body` | シンボル置換 | 関数・クラス本体の置換 |
| `mcp__serena__get_symbols_overview` | シンボル概要 | ファイル/ディレクトリのシンボル一覧 |
| `mcp__serena__read_memory` | メモリ読み取り | プロジェクト記憶の読み取り |
| `mcp__serena__write_memory` | メモリ書き込み | プロジェクト記憶の書き込み |
| `mcp__serena__insert_after_symbol` | シンボル後挿入 | シンボルの後にコード挿入 |
| `mcp__serena__insert_before_symbol` | シンボル前挿入 | シンボルの前にコード挿入 |

## 🔧 トラブルシューティング

### よくある問題

#### 1. `claude command not found`
```bash
# Claude Code CLI のインストールを確認
which claude

# インストールされていない場合
# https://docs.anthropic.com/claude-code からインストール
```

#### 2. `uv command not found`
```bash
# uv のインストール
pip install uv

# または conda を使用
conda install -c conda-forge uv
```

#### 3. `uvx command not found`
```bash
# uv を最新版に更新
pip install -U uv

# uvx は uv 0.4.0+ に含まれています
uv --version
```

#### 4. Serena MCP Server の初回ダウンロードが遅い
- 初回起動時は GitHub からダウンロードするため時間がかかります
- インターネット接続を確認してください
- プロキシ環境の場合は設定を確認してください

#### 5. MCP Server 接続エラー
```bash
# Serena を手動でテスト
uvx --from git+https://github.com/oraios/serena serena-mcp-server --help

# ポート競合の確認
lsof -i :8000  # デフォルトポートを確認
```

### ログとデバッグ

#### 詳細ログの有効化
```bash
# 環境変数でデバッグモードを有効化
export SERENA_DEBUG=1
export CLAUDE_DEBUG=1

./start-claude-with-serena.sh
```

#### 一時ファイルの確認
スクリプトは一時的なMCP設定ファイルを作成します：
```bash
# 一時ファイルの場所を確認
echo $TMPDIR
ls -la $TMPDIR/tmp.*
```

## 💡 使用のヒント

### 1. 効率的なコード編集
```
# Serena を使った効率的なワークフロー例
1. mcp__serena__get_symbols_overview でファイル構造を把握
2. mcp__serena__find_symbol で特定のクラス/関数を検索
3. mcp__serena__replace_symbol_body で実装を更新
4. mcp__serena__write_memory でプロジェクト情報を記録
```

### 2. プロジェクト記憶の活用
```
# プロジェクトの設計思想や重要な情報を記録
mcp__serena__write_memory("architecture", "システム設計情報...")
mcp__serena__write_memory("coding_standards", "コーディング規約...")

# 後で参照
mcp__serena__read_memory("architecture")
```

### 3. 大規模リファクタリング
```
# 複数ファイルの一括変更に最適
1. mcp__serena__search_for_pattern で変更対象を特定
2. mcp__serena__find_referencing_symbols で影響範囲を調査
3. 段階的に mcp__serena__replace_symbol_body で更新
```

## 📚 参考リンク

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Serena MCP Server](https://github.com/oraios/serena)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [uv Documentation](https://docs.astral.sh/uv/)

## 🐛 バグ報告・フィードバック

スクリプトに問題がある場合は、以下の情報と共に報告してください：

```bash
# システム情報
uname -a
echo $SHELL
claude --version
uv --version

# エラーログ
./start-claude-with-serena.sh 2>&1 | tee debug.log
```

---

*🤖 Generated with [Claude Code](https://claude.ai/code) - Kumihan-Formatter Project*