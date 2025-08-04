# Claude Code セットアップキット

> Kumihan-Formatterで構築したClaude Code設定を他プロジェクトに簡単移植するツール

## 🎯 概要

このセットアップキットを使用すると、Kumihan-Formatterで構築した高度なClaude Code設定を他のプロジェクトに一発でセットアップできます。

### 含まれる機能

- ✅ **AI運用7原則**を含むCLAUDE.md
- ✅ **Serena統合システム**（セマンティックコード編集）
- ✅ **高度なPermissions設定**（170+項目）
- ✅ **6つのMCPサーバー**（context7, gemini-cli, serena, memory, deepview, sequential-thinking）
- ✅ **Issue管理自動化**（ラベル付与ルール）
- ✅ **ブランチ管理ルール**（日本語ブランチ名禁止）
- ✅ **日本語レビューシステム**
- ✅ **SubAgent自動選択**
- ✅ **CLAUDE.md管理システム**
- ✅ **Hooks設定**（オプション）

## 🚀 クイックスタート

### 1. 基本セットアップ

```bash
# 新しいプロジェクトに移植
python claude-setup-kit/setup.py \\
  --project-name "MyAwesomeProject" \\
  --project-path "/path/to/my-project"
```

### 2. 言語別セットアップ

```bash
# JavaScript/TypeScriptプロジェクト
python claude-setup-kit/setup.py \\
  --project-name "MyWebApp" \\
  --project-path "/path/to/webapp" \\
  --language "JavaScript"

# Goプロジェクト
python claude-setup-kit/setup.py \\
  --project-name "MyGoAPI" \\
  --project-path "/path/to/go-api" \\
  --language "Go"
```

### 3. カスタム設定でセットアップ

```bash
# 独自の設定ファイルを使用
python claude-setup-kit/setup.py \\
  --project-name "MyProject" \\
  --project-path "/path/to/project" \\
  --config my-custom-config.yaml \\
  --with-hooks
```

## 📁 ファイル構成

```
claude-setup-kit/
├── setup.py                              # メインセットアップスクリプト
├── project_config.yaml                   # 設定ファイル
├── README.md                             # このファイル
└── templates/                            # テンプレートファイル
    ├── CLAUDE.md.template                # CLAUDE.mdテンプレート
    ├── settings.local.json.template      # Claude設定テンプレート
    ├── claude_md_config.yaml.template    # CLAUDE.md管理設定
    ├── claude_desktop_config.json.template # MCP設定（参考）
    └── hooks.json.template               # Hooks設定テンプレート
```

## ⚙️ 詳細設定

### project_config.yaml カスタマイズ

```yaml
project:
  name: "MyProject"
  language: "Python"  # Python, JavaScript, Go, Rust
  version: "3.12"

tools:
  formatter: "black"      # black, prettier, gofmt, rustfmt
  linter: "flake8"        # flake8, eslint, golangci-lint, clippy
  type_checker: "mypy"    # mypy, typescript, go, rustc
  test_runner: "pytest"   # pytest, jest, go test, cargo test

components:
  list:
    - "コンポーネント:API"
    - "コンポーネント:UI"
    - "コンポーネント:DB"
```

### コマンドラインオプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--project-name` | プロジェクト名（必須） | - |
| `--project-path` | プロジェクトパス（必須） | - |
| `--config` | カスタム設定ファイル | `project_config.yaml` |
| `--language` | プログラミング言語 | `Python` |
| `--no-mcp` | MCP設定をスキップ | False |
| `--with-hooks` | Hooks設定を含める | False |

## 🔧 セットアップ後の作業

### 1. MCPサーバーの手動セットアップ

セットアップスクリプト実行後、以下のコマンドを実行：

```bash
# Serena（プロジェクト固有パス）
claude mcp add serena uvx --from git+https://github.com/oraios/serena serena-mcp-server --context ide-assistant --project "/your/project/path"

# その他のMCPサーバー
claude mcp add context7 npx -y @upstash/context7-mcp
claude mcp add gemini-cli npx mcp-gemini-cli --allow-npx
claude mcp add memory npx @modelcontextprotocol/server-memory
claude mcp add deepview uvx deepview-mcp
claude mcp add sequential-thinking uvx sequential-thinking-mcp
```

### 2. プロジェクト固有のカスタマイズ

1. **CLAUDE.md**の「プロジェクト固有設定」セクションを編集
2. **components.list**を実際のコンポーネントに変更
3. **documentation.links**を実際のドキュメントに更新
4. **logging.import**を実際のログ設定に変更

### 3. 動作確認

```bash
cd /your/project/path
claude
```

Claude Code起動後、以下を確認：
- ✅ AI運用7原則が表示される
- ✅ Serena MCP が接続される
- ✅ `/serena` コマンドが使用可能
- ✅ SubAgent が自動選択される

## 📋 対応言語・フレームワーク

| 言語 | フォーマッター | リンター | 型チェッカー | テストランナー |
|------|------------|---------|-------------|-------------|
| **Python** | black | flake8 | mypy | pytest |
| **JavaScript/TypeScript** | prettier | eslint | typescript | jest |
| **Go** | gofmt | golangci-lint | go | go test |
| **Rust** | rustfmt | clippy | rustc | cargo test |

### 追加言語サポート

`project_config.yaml`の`language_configs`セクションに追加：

```yaml
language_configs:
  Java:
    formatter: "google-java-format"
    linter: "checkstyle"
    type_checker: "javac"
    test_runner: "junit"
```

## 🎛️ 高度な機能

### SubAgent自動選択

セットアップ後、以下が自動で利用可能：

```bash
# 自動でSerena Expertが選択される
/serena "新しい機能を実装したい"
/serena "コードをリファクタリングしたい"  
/serena "バグを修正したい"
```

### 権限管理システム

170+項目の詳細な権限設定：
- Git操作（add, commit, push, pull, merge, rebase等）
- テスト実行（pytest, make test等）
- コード品質（lint, format, type check等）
- プロジェクト固有コマンド
- MCP操作（serena, context7等）

### Issue管理自動化

```bash
# ラベル付与が自動化される
gh issue create --title "バグ修正" --body "内容" --label "バグ,優先度:高,難易度:普通,コンポーネント:API"
```

## 🔍 トラブルシューティング

### よくある問題

**Q: MCPサーバーが接続されない**
```bash
# MCP接続状況確認
claude mcp list

# 個別サーバー確認
claude mcp test serena
```

**Q: CLAUDE.mdが読み込まれない**
```bash
# ファイル存在確認
ls -la CLAUDE.md

# 権限確認
chmod 644 CLAUDE.md
```

**Q: SubAgentが自動選択されない**
```bash
# SubAgent設定確認
cat .claude/subagents.json

# セッション再起動
exit  # Claude Codeを終了
claude  # 再起動
```

### デバッグモード

```bash
# 詳細ログ付きでセットアップ
python claude-setup-kit/setup.py \\
  --project-name "DebugProject" \\
  --project-path "/tmp/debug" \\
  --verbose
```

## 📊 使用例

### 実際のプロジェクト例

```bash
# React + TypeScriptプロジェクト
python claude-setup-kit/setup.py \\
  --project-name "MyReactApp" \\
  --project-path "/Users/dev/my-react-app" \\
  --language "JavaScript" \\
  --config react-config.yaml

# FastAPIプロジェクト  
python claude-setup-kit/setup.py \\
  --project-name "MyFastAPI" \\
  --project-path "/Users/dev/my-fastapi" \\
  --language "Python" \\
  --config fastapi-config.yaml

# マイクロサービス
python claude-setup-kit/setup.py \\
  --project-name "UserService" \\
  --project-path "/Users/dev/microservices/user-service" \\
  --language "Go" \\
  --with-hooks
```

## 🔄 更新・メンテナンス

### キットの更新

```bash
# 最新版をKumihan-Formatterから取得
cd /path/to/Kumihan-Formatter
cp -r claude-setup-kit /path/to/new-location
```

### 設定の更新

```bash
# 既存プロジェクトの設定更新
python claude-setup-kit/setup.py \\
  --project-name "ExistingProject" \\
  --project-path "/path/to/existing" \\
  --update-only
```

## 🤝 コントリビューション

新しい言語サポートやテンプレート改善の提案を歓迎します：

1. `templates/` に新しいテンプレート追加
2. `project_config.yaml` に言語設定追加  
3. `setup.py` に処理ロジック追加
4. 動作テスト実施
5. PR作成

## 📜 ライセンス

Kumihan-Formatterプロジェクトと同じライセンスに従います。

---

**🎉 高度なClaude Code環境を他プロジェクトでも活用しましょう！**

*Generated by Claude Code Setup Kit v1.0 - Powered by Kumihan-Formatter*