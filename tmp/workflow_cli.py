"""
CLI インターフェース

全システム機能のCLI化、ヘルプ・自動補完・カラー出力。
init, run, status, config, migrate等のコマンドを提供。
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# 相対インポート用のパス設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from advanced_project_config import AdvancedProjectConfig, ProjectType
from plugin_system import PluginManager
from project_wizard import InteractiveWizard, QuickSetupWizard
from workflow_engine_api import AutomationLevel, TaskPriority, WorkflowEngineAPI, WorkflowRequest


# リッチコンソール初期化
console = Console()


class WorkflowCLI:
    """ワークフローCLI管理クラス"""

    def __init__(self):
        self.config_manager = AdvancedProjectConfig()
        self.plugin_manager = None
        self.api = None

    async def initialize(self) -> None:
        """CLI初期化"""
        self.plugin_manager = PluginManager()
        await self.plugin_manager.initialize()
        self.api = WorkflowEngineAPI.auto_detect(".")


# CLIグループ定義
@click.group()
@click.version_option(version="1.0.0", prog_name="workflow-engine")
@click.option("--verbose", "-v", is_flag=True, help="詳細出力を有効にする")
@click.option("--config", "-c", help="設定ファイルパスを指定")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config: Optional[str]) -> None:
    """
    🔧 Kumihan-Formatter ワークフローエンジン CLI

    プロジェクトの品質向上と自動化を支援するツールです。
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config
    ctx.obj["cli_instance"] = WorkflowCLI()


@cli.command()
@click.option("--project-type", "-t",
              type=click.Choice([pt.value for pt in ProjectType]),
              help="プロジェクト種別を指定")
@click.option("--interactive", "-i", is_flag=True,
              help="インタラクティブモードでセットアップ")
@click.option("--quick", "-q", is_flag=True,
              help="クイックセットアップ（非対話式）")
@click.argument("project_path", default=".")
@click.pass_context
def init(ctx: click.Context, project_type: Optional[str], interactive: bool,
         quick: bool, project_path: str) -> None:
    """
    プロジェクトの初期設定を行います。

    PROJECT_PATH: 設定を作成するプロジェクトのパス（デフォルト: 現在のディレクトリ）
    """
    async def _init():
        cli_instance = ctx.obj["cli_instance"]

        with console.status("[bold green]プロジェクト初期化中..."):
            if interactive:
                # インタラクティブウィザード
                wizard = InteractiveWizard()
                config = await wizard.start_wizard(project_path)
                console.print("✅ インタラクティブセットアップ完了", style="green")

            elif quick or project_type:
                # クイックセットアップ
                quick_wizard = QuickSetupWizard()
                ptype = ProjectType(project_type) if project_type else None
                config = quick_wizard.quick_setup(project_path, ptype)
                console.print("✅ クイックセットアップ完了", style="green")

            else:
                # デフォルト: クイックセットアップ
                quick_wizard = QuickSetupWizard()
                config = quick_wizard.quick_setup(project_path)
                console.print("✅ デフォルトセットアップ完了", style="green")

        # 結果表示
        _display_config_summary(config)

    asyncio.run(_init())


@cli.command()
@click.argument("task_description")
@click.option("--automation", "-a",
              type=click.Choice([level.value for level in AutomationLevel]),
              default=AutomationLevel.SEMI_AUTO.value,
              help="自動化レベル")
@click.option("--priority", "-p",
              type=click.Choice([p.value for p in TaskPriority]),
              default=TaskPriority.NORMAL.value,
              help="タスク優先度")
@click.option("--timeout", "-T", type=int, default=3600,
              help="タイムアウト時間（秒）")
@click.option("--project-path", default=".",
              help="プロジェクトパス")
@click.option("--api-key", envvar="WORKFLOW_API_KEY",
              help="APIキー（環境変数 WORKFLOW_API_KEY からも取得可能）")
@click.pass_context
def run(ctx: click.Context, task_description: str, automation: str,
        priority: str, timeout: int, project_path: str, api_key: Optional[str]) -> None:
    """
    ワークフロータスクを実行します。

    TASK_DESCRIPTION: 実行するタスクの説明（例: "MyPy修正を実行してください"）
    """
    async def _run():
        cli_instance = ctx.obj["cli_instance"]
        await cli_instance.initialize()

        # パラメータ変換
        automation_level = AutomationLevel(automation)
        task_priority = TaskPriority(priority)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("タスク実行中...", total=None)

            try:
                result = await cli_instance.api.run(
                    task_description=task_description,
                    project_path=project_path,
                    api_key=api_key,
                    automation_level=automation_level
                )

                progress.remove_task(task)
                _display_task_result(result)

            except Exception as e:
                progress.remove_task(task)
                console.print(f"❌ エラー: {e}", style="red")
                sys.exit(1)

    asyncio.run(_run())


@cli.command()
@click.option("--task-id", help="特定のタスクID")
@click.option("--all", "-a", is_flag=True, help="全タスクの状態を表示")
@click.option("--format", "-f", type=click.Choice(["table", "json"]),
              default="table", help="出力形式")
@click.pass_context
def status(ctx: click.Context, task_id: Optional[str], all: bool, format: str) -> None:
    """
    タスクの実行状態を表示します。
    """
    async def _status():
        cli_instance = ctx.obj["cli_instance"]
        await cli_instance.initialize()

        if task_id:
            # 特定タスクの状態
            result = cli_instance.api.get_task_status(task_id)
            if result:
                if format == "json":
                    console.print_json(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
                else:
                    _display_task_result(result)
            else:
                console.print(f"タスクが見つかりません: {task_id}", style="yellow")

        elif all:
            # 全タスクの状態
            tasks = cli_instance.api.list_active_tasks()
            if format == "json":
                tasks_data = [task.to_dict() for task in tasks]
                console.print_json(json.dumps(tasks_data, ensure_ascii=False, indent=2))
            else:
                _display_task_list(tasks)

        else:
            console.print("--task-id または --all オプションを指定してください", style="yellow")

    asyncio.run(_status())


@cli.command()
@click.option("--show", "-s", is_flag=True, help="現在の設定を表示")
@click.option("--edit", "-e", is_flag=True, help="設定ファイルを編集")
@click.option("--validate", "-v", is_flag=True, help="設定ファイルを検証")
@click.option("--format", "-f", type=click.Choice(["yaml", "json", "toml"]),
              help="設定ファイル形式を指定")
@click.argument("config_path", default="workflow_config.yaml")
@click.pass_context
def config(ctx: click.Context, show: bool, edit: bool, validate: bool,
           format: Optional[str], config_path: str) -> None:
    """
    プロジェクト設定を管理します。

    CONFIG_PATH: 設定ファイルのパス（デフォルト: workflow_config.yaml）
    """
    cli_instance = ctx.obj["cli_instance"]

    if show:
        # 設定表示
        try:
            config = cli_instance.config_manager.load_config(config_path)
            _display_config_summary(config)
        except Exception as e:
            console.print(f"設定読み込みエラー: {e}", style="red")

    elif edit:
        # 設定編集
        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} {config_path}")
        console.print(f"設定ファイルを編集しました: {config_path}", style="green")

    elif validate:
        # 設定検証
        try:
            config = cli_instance.config_manager.load_config(config_path)
            warnings = cli_instance.config_manager.validate_config(config)

            if warnings:
                console.print("⚠️ 設定に警告があります:", style="yellow")
                for warning in warnings:
                    console.print(f"  - {warning}", style="yellow")
            else:
                console.print("✅ 設定は正常です", style="green")

        except Exception as e:
            console.print(f"❌ 設定エラー: {e}", style="red")

    else:
        console.print("--show, --edit, --validate のいずれかを指定してください", style="yellow")


@cli.command()
@click.argument("old_config")
@click.argument("new_config")
@click.option("--backup", "-b", is_flag=True, help="移行前にバックアップを作成")
@click.pass_context
def migrate(ctx: click.Context, old_config: str, new_config: str, backup: bool) -> None:
    """
    設定ファイル形式を移行します。

    OLD_CONFIG: 移行元設定ファイル
    NEW_CONFIG: 移行先設定ファイル
    """
    cli_instance = ctx.obj["cli_instance"]

    try:
        # バックアップ作成
        if backup and os.path.exists(new_config):
            backup_path = f"{new_config}.backup"
            os.rename(new_config, backup_path)
            console.print(f"バックアップを作成しました: {backup_path}", style="blue")

        # 移行実行
        cli_instance.config_manager.migrate_config(old_config, new_config)
        console.print(f"✅ 設定移行完了: {old_config} → {new_config}", style="green")

    except Exception as e:
        console.print(f"❌ 移行エラー: {e}", style="red")


@cli.command()
@click.option("--list", "-l", is_flag=True, help="利用可能なプラグインを一覧表示")
@click.option("--install", help="プラグインをインストール")
@click.option("--uninstall", help="プラグインをアンインストール")
@click.option("--enable", help="プラグインを有効化")
@click.option("--disable", help="プラグインを無効化")
@click.pass_context
def plugin(ctx: click.Context, list: bool, install: Optional[str],
           uninstall: Optional[str], enable: Optional[str], disable: Optional[str]) -> None:
    """
    プラグインを管理します。
    """
    async def _plugin():
        cli_instance = ctx.obj["cli_instance"]
        await cli_instance.initialize()

        if list:
            # プラグイン一覧
            plugins = cli_instance.plugin_manager.registry.list_plugins()
            _display_plugin_list(plugins)

        elif install:
            # プラグインインストール（実装は簡略化）
            console.print(f"プラグインインストール機能は開発中です: {install}", style="yellow")

        elif uninstall:
            # プラグインアンインストール
            cli_instance.plugin_manager.registry.unregister_plugin(uninstall)
            console.print(f"✅ プラグインを削除しました: {uninstall}", style="green")

        elif enable or disable:
            # プラグイン有効化/無効化（実装は簡略化）
            action = "有効化" if enable else "無効化"
            plugin_name = enable or disable
            console.print(f"プラグイン{action}機能は開発中です: {plugin_name}", style="yellow")

        else:
            console.print("--list, --install, --uninstall, --enable, --disable のいずれかを指定してください",
                         style="yellow")

    asyncio.run(_plugin())


@cli.command()
@click.option("--analytics", "-a", is_flag=True, help="分析レポートを表示")
@click.option("--export", "-e", help="レポートをファイルに出力")
@click.option("--period", "-p", type=click.Choice(["day", "week", "month"]),
              default="week", help="レポート期間")
@click.pass_context
def report(ctx: click.Context, analytics: bool, export: Optional[str], period: str) -> None:
    """
    実行レポートを生成します。
    """
    # レポート機能は実装簡略化
    console.print("📊 実行レポート", style="bold blue")

    if analytics:
        console.print("分析機能は開発中です", style="yellow")

    if export:
        console.print(f"エクスポート機能は開発中です: {export}", style="yellow")

    console.print(f"期間: {period}", style="blue")


# ヘルパー関数

def _display_config_summary(config) -> None:
    """設定サマリー表示"""
    table = Table(title="プロジェクト設定サマリー")
    table.add_column("項目", style="cyan")
    table.add_column("値", style="green")

    table.add_row("プロジェクト名", config.name)
    table.add_row("プロジェクト種別", config.project_type.value)
    table.add_row("ルートパス", config.root_path)
    table.add_row("ソースディレクトリ", ", ".join(config.source_dirs))
    table.add_row("テストディレクトリ", ", ".join(config.test_dirs))
    table.add_row("ツール数", str(len(config.tools)))

    if config.tools:
        tools_list = ", ".join([tool.name for tool in config.tools])
        table.add_row("ツール", tools_list)

    console.print(table)


def _display_task_result(result) -> None:
    """タスク結果表示"""
    # ステータスに応じたスタイル
    status_styles = {
        "completed": "green",
        "failed": "red",
        "running": "yellow",
        "pending": "blue",
        "cancelled": "gray"
    }

    status_style = status_styles.get(result.status.value, "white")

    console.print(f"\n📋 タスク結果 (ID: {result.task_id})", style="bold")
    console.print(f"ステータス: {result.status.value}", style=status_style)
    console.print(f"開始時刻: {result.start_time}")

    if result.end_time:
        console.print(f"終了時刻: {result.end_time}")
        console.print(f"実行時間: {result.duration:.2f}秒")

    if result.output:
        console.print("\n📄 出力:")
        console.print(result.output, style="dim")

    if result.error:
        console.print("\n❌ エラー:")
        console.print(result.error, style="red")


def _display_task_list(tasks: List) -> None:
    """タスク一覧表示"""
    if not tasks:
        console.print("アクティブなタスクはありません", style="yellow")
        return

    table = Table(title="アクティブタスク一覧")
    table.add_column("Task ID", style="cyan")
    table.add_column("ステータス", style="green")
    table.add_column("開始時刻", style="blue")
    table.add_column("実行時間", style="yellow")

    for task in tasks:
        duration = f"{task.duration:.2f}s" if task.duration else "実行中"
        table.add_row(
            task.task_id[:8] + "...",
            task.status.value,
            task.start_time.strftime("%H:%M:%S"),
            duration
        )

    console.print(table)


def _display_plugin_list(plugins: List) -> None:
    """プラグイン一覧表示"""
    if not plugins:
        console.print("インストール済みプラグインはありません", style="yellow")
        return

    table = Table(title="プラグイン一覧")
    table.add_column("名前", style="cyan")
    table.add_column("種別", style="green")
    table.add_column("バージョン", style="blue")
    table.add_column("説明", style="dim")

    for plugin in plugins:
        table.add_row(
            plugin.name,
            plugin.plugin_type.value,
            plugin.version,
            plugin.description[:50] + "..." if len(plugin.description) > 50 else plugin.description
        )

    console.print(table)


# 自動補完サポート
def _get_project_types():
    """プロジェクト種別一覧取得（自動補完用）"""
    return [pt.value for pt in ProjectType]


def _get_automation_levels():
    """自動化レベル一覧取得（自動補完用）"""
    return [level.value for level in AutomationLevel]


# メイン実行部
if __name__ == "__main__":
    try:
        # 必要な依存関係チェック
        missing_deps = []

        try:
            import yaml
        except ImportError:
            missing_deps.append("PyYAML")

        try:
            import tomllib
        except ImportError:
            missing_deps.append("tomli (Python 3.11+)")

        try:
            from rich import console
        except ImportError:
            missing_deps.append("rich")

        if missing_deps:
            print(f"❌ 必要な依存関係が不足しています: {', '.join(missing_deps)}")
            print("以下のコマンドでインストールしてください:")
            print(f"pip install {' '.join(missing_deps)}")
            sys.exit(1)

        # CLI実行
        cli()

    except KeyboardInterrupt:
        console.print("\n中断されました", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ 予期しないエラー: {e}", style="red")
        sys.exit(1)
