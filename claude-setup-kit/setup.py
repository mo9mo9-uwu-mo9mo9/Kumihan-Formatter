#!/usr/bin/env python3
"""
Claude Code セットアップキット
Kumihan-Formatterで構築したClaude Code設定を他プロジェクトに移植するツール

Usage:
    python setup.py --project-name "MyProject" --project-path "/path/to/project"
"""

import os
import sys
import json
import yaml
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

class ClaudeSetupKit:
    """Claude Code設定の自動セットアップツール"""

    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir
        self.templates_dir = kit_dir / "templates"
        self.config_file = kit_dir / "project_config.yaml"

    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if config_path:
            config_file = config_path
        else:
            config_file = self.config_file

        if not config_file.exists():
            return self.create_default_config()

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def create_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を作成"""
        return {
            "project": {
                "name": "{{PROJECT_NAME}}",
                "status": "開発中",
                "phase": "Development",
                "path": "{{PROJECT_PATH}}",
                "language": "Python",
                "version": "3.12",
                "release_version": "未定"
            },
            "tools": {
                "formatter": "black",
                "linter": "flake8",
                "type_checker": "mypy",
                "test_runner": "pytest",
                "test_command": "python -m pytest tests/ -v"
            },
            "components": {
                "example": "コンポーネント:パーサー",
                "list": [
                    "コンポーネント:パーサー",
                    "コンポーネント:レンダラー",
                    "コンポーネント:CLI",
                    "コンポーネント:コア"
                ]
            },
            "review": {
                "automation_status": "無効化完了",
                "manual_process": "Claude Codeとの対話セッション内で実施",
                "request_process": "PR作成後、Claude Codeセッションで「変更内容をレビュー」と依頼",
                "merge_policy": "mo9mo9手動のみ",
                "ci_cd_requirements": "新CI必須通過"
            },
            "logging": {
                "import": "from myproject.utilities.logger import get_logger"
            },
            "documentation": {
                "links": [
                    "- [アーキテクチャ](docs/architecture.md) - システム設計",
                    "- [ユーザーガイド](docs/user-guide.md) - 利用者向けガイド"
                ],
                "project_specific": "# プロジェクト固有の設定\\n\\n追加設定をここに記述してください。"
            },
            "mcp_servers": [
                "context7",
                "gemini-cli",
                "memory",
                "deepview",
                "sequential-thinking"
            ]
        }

    def substitute_template(self, template_content: str, config: Dict[str, Any]) -> str:
        """テンプレート変数を置換"""
        substitutions = {
            "{{PROJECT_NAME}}": config["project"]["name"],
            "{{PROJECT_STATUS}}": config["project"]["status"],
            "{{PROJECT_PHASE}}": config["project"]["phase"],
            "{{PROJECT_PATH}}": config["project"]["path"],
            "{{LANGUAGE}}": config["project"]["language"],
            "{{VERSION}}": config["project"]["version"],
            "{{RELEASE_VERSION}}": config["project"]["release_version"],
            "{{FORMATTER}}": config["tools"]["formatter"],
            "{{LINTER}}": config["tools"]["linter"],
            "{{TYPE_CHECKER}}": config["tools"]["type_checker"],
            "{{TEST_RUNNER}}": config["tools"]["test_runner"],
            "{{TEST_COMMAND}}": config["tools"]["test_command"],
            "{{COMPONENT_EXAMPLE}}": config["components"]["example"],
            "{{PROJECT_COMPONENTS}}": ", ".join([f"`{comp}`" for comp in config["components"]["list"]]),
            "{{REVIEW_AUTOMATION_STATUS}}": config["review"]["automation_status"],
            "{{MANUAL_REVIEW_PROCESS}}": config["review"]["manual_process"],
            "{{REVIEW_REQUEST_PROCESS}}": config["review"]["request_process"],
            "{{MERGE_POLICY}}": config["review"]["merge_policy"],
            "{{CI_CD_REQUIREMENTS}}": config["review"]["ci_cd_requirements"],
            "{{LOGGER_IMPORT}}": config["logging"]["import"],
            "{{DOCUMENTATION_LINKS}}": "\\n".join(config["documentation"]["links"]),
            "{{PROJECT_SPECIFIC_CONTENT}}": config["documentation"]["project_specific"],
            "{{PROJECT_SPECIFIC_SECTION}}": config["project"]["name"] + "固有設定",
            "{{PROJECT_COMMAND}}": config["project"]["name"].lower(),
            "{{HOOK_COMMAND_PREFIX}}": f"bash .claude/hooks",
            "{{TIMESTAMP}}": "$(date '+%Y-%m-%d %H:%M:%S')"
        }

        result = template_content
        for placeholder, value in substitutions.items():
            result = result.replace(placeholder, str(value))

        return result

    def setup_project(self, project_path: Path, config: Dict[str, Any], options: Dict[str, bool]):
        """プロジェクトのセットアップを実行"""
        print(f"🚀 Claude Code セットアップ開始: {config['project']['name']}")
        print(f"📂 プロジェクトパス: {project_path}")

        # プロジェクトディレクトリの作成
        project_path.mkdir(parents=True, exist_ok=True)
        claude_dir = project_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # 1. CLAUDE.mdの作成
        if options.get("create_claude_md", True):
            self._create_claude_md(project_path, config)

        # 2. Claude設定の作成
        if options.get("create_claude_settings", True):
            self._create_claude_settings(claude_dir, config)

        # 3. CLAUDE.md管理設定の作成
        if options.get("create_md_config", True):
            self._create_md_config(project_path, config)

        # 4. Serena-Expert強制設定の作成（デフォルト有効）
        if options.get("create_serena_config", True):
            self._create_serena_config(project_path, config)

        # 5. MCPサーバー設定（グローバル）
        if options.get("setup_mcp", True):
            self._setup_mcp_servers(config)

        # 6. Hooks設定の作成（オプション）
        if options.get("create_hooks", False):
            self._create_hooks(claude_dir, config)

        # 7. SubAgentの設定
        if options.get("setup_subagent", True):
            self._setup_subagent(project_path, config)

        print("✅ セットアップ完了！")
        self._print_next_steps(project_path)

    def _create_claude_md(self, project_path: Path, config: Dict[str, Any]):
        """CLAUDE.mdを作成"""
        print("📝 CLAUDE.md作成中...")
        template_path = self.templates_dir / "CLAUDE.md.template"

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        content = self.substitute_template(template_content, config)

        output_path = project_path / "CLAUDE.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ {output_path}")

    def _create_claude_settings(self, claude_dir: Path, config: Dict[str, Any]):
        """Claude設定を作成"""
        print("⚙️ Claude設定作成中...")
        template_path = self.templates_dir / "settings.local.json.template"

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        content = self.substitute_template(template_content, config)

        output_path = claude_dir / "settings.local.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ {output_path}")

    def _create_md_config(self, project_path: Path, config: Dict[str, Any]):
        """CLAUDE.md管理設定を作成"""
        print("📋 CLAUDE.md管理設定作成中...")
        template_path = self.templates_dir / "claude_md_config.yaml.template"

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        content = self.substitute_template(template_content, config)

        output_path = project_path / ".claude_md_config.yaml"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ {output_path}")

    def _setup_mcp_servers(self, config: Dict[str, Any]):
        """MCPサーバーをセットアップ"""
        print("🔧 MCPサーバー設定中...")

        # Serenaセットアップ
        serena_command = f'claude mcp add serena uvx --from git+https://github.com/oraios/serena serena-mcp-server --context ide-assistant --project "{config["project"]["path"]}"'
        print(f"  📦 Serena: {serena_command}")

        # その他のMCPサーバー
        mcp_commands = {
            "context7": "claude mcp add context7 npx -y @upstash/context7-mcp",
            "gemini-cli": "claude mcp add gemini-cli npx mcp-gemini-cli --allow-npx",
            "memory": "claude mcp add memory npx @modelcontextprotocol/server-memory",
            "deepview": "claude mcp add deepview uvx deepview-mcp",
            "sequential-thinking": "claude mcp add sequential-thinking uvx sequential-thinking-mcp"
        }

        for server_name, command in mcp_commands.items():
            if server_name in config["mcp_servers"]:
                print(f"  📦 {server_name}: {command}")

        print("  💡 上記のコマンドを手動で実行してください")

    def _create_hooks(self, claude_dir: Path, config: Dict[str, Any]):
        """Hooks設定を作成"""
        print("🪝 Hooks設定作成中...")
        template_path = self.templates_dir / "hooks.json.template"

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        content = self.substitute_template(template_content, config)

        output_path = claude_dir / "hooks.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Hooksスクリプトディレクトリ作成
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        print(f"  ✓ {output_path}")
        print(f"  ✓ {hooks_dir}")


    def _create_serena_config(self, project_path: Path, config: Dict[str, Any]):
        """Serena-Expert強制設定を作成"""
        print("🚨 Serena-Expert強制設定作成中...")
        template_path = self.templates_dir / "claude_config.yml.template"

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        content = self.substitute_template(template_content, config)

        output_path = project_path / ".claude-config.yml"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ {output_path}")
        print("  🚨 Serena-Expert強制システム有効化完了")

    def _setup_subagent(self, project_path: Path, config: Dict[str, Any]):
        """SubAgent設定を作成"""
        print("🤖 SubAgent設定作成中...")

        subagent_config = {
            "serena-expert": {
                "description": f"Elite app development agent for {config['project']['name']} using Serena MCP",
                "context": "ide-assistant",
                "tools": ["*"],
                "specialization": [
                    "Component implementation",
                    "API development",
                    "System architecture",
                    "Code refactoring"
                ]
            }
        }

        config_path = project_path / ".claude" / "subagents.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(subagent_config, f, indent=2, ensure_ascii=False)

        print(f"  ✓ {config_path}")

    def _print_next_steps(self, project_path: Path):
        """次のステップを表示"""
        print("\\n🎯 次のステップ:")
        print("1. MCPサーバーを手動でセットアップ:")
        print("   - 上記のMCPコマンドを実行")
        print("2. プロジェクトディレクトリに移動:")
        print(f"   cd {project_path}")
        print("3. Claude Codeを起動:")
        print("   claude")
        print("4. CLAUDE.mdの内容を確認・カスタマイズ")
        print("5. 必要に応じて設定ファイルを調整")
        print("\\n🎉 セットアップ完了！Claude Codeの高度な機能をお楽しみください。")

def main():
    parser = argparse.ArgumentParser(description="Claude Code セットアップキット")
    parser.add_argument("--project-name", required=True, help="プロジェクト名")
    parser.add_argument("--project-path", required=True, help="プロジェクトパス")
    parser.add_argument("--config", help="設定ファイルパス")
    parser.add_argument("--language", default="Python", help="プログラミング言語")
    parser.add_argument("--no-mcp", action="store_true", help="MCP設定をスキップ")
    parser.add_argument("--no-hooks", action="store_true", help="Hooks設定をスキップ")
    parser.add_argument("--with-hooks", action="store_true", help="Hooks設定を含める")
    parser.add_argument("--with-serena-config", action="store_true", default=True, help="Serena-Expert強制設定を含める")
    parser.add_argument("--no-serena-enforcement", action="store_true", help="Serena強制を無効化（非推奨）")

    args = parser.parse_args()

    # キットディレクトリの確認
    kit_dir = Path(__file__).parent
    if not (kit_dir / "templates").exists():
        print("❌ テンプレートディレクトリが見つかりません")
        sys.exit(1)

    # セットアップキットの初期化
    setup_kit = ClaudeSetupKit(kit_dir)

    # 設定の読み込み・カスタマイズ
    config = setup_kit.load_config(Path(args.config) if args.config else None)
    config["project"]["name"] = args.project_name
    config["project"]["path"] = os.path.abspath(args.project_path)
    config["project"]["language"] = args.language

    # Serena強制無効化の警告
    if args.no_serena_enforcement:
        print("⚠️  警告: Serena-Expert強制システムを無効化します（非推奨）")
        print("⚠️  この設定は開発効率を大幅に低下させる可能性があります")

    # セットアップオプション
    options = {
        "create_claude_md": True,
        "create_claude_settings": True,
        "create_md_config": True,
        "create_serena_config": not args.no_serena_enforcement,
        "setup_mcp": not args.no_mcp,
        "create_hooks": args.with_hooks,
        "setup_subagent": True
    }

    # セットアップ実行
    project_path = Path(args.project_path)
    setup_kit.setup_project(project_path, config, options)

if __name__ == "__main__":
    main()
