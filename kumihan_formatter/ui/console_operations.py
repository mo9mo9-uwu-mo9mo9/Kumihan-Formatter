"""
コンソール オペレーション

ファイル操作・監視・テスト等の処理操作表示機能
Issue #492 Phase 5A - console_ui.py分割
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple


class ConsoleOperations:
    """Console operations functionality

    Handles display of file operations, watch mode,
    test generation, and other processing operations.
    """

    def __init__(self, console: Any) -> None:
        """Initialize with a Rich Console instance"""
        self.console = console

    # File operations
    def file_copied(self, count: int) -> None:
        """Display file copy count"""
        self.console.print("[green]{}個の画像ファイルをコピーしました[/green]".format(count))

    def files_missing(self, files: List[str]) -> None:
        """Display missing files"""
        self.console.print(f"[red][エラー] {len(files)}個の画像ファイルが" "見つかりません:[/red]")
        for filename in files:
            self.console.print(f"[red]   - {filename}[/red]")

    def duplicate_files(self, duplicates: Dict[str, int]) -> None:
        """Display duplicate files warning"""
        self.console.print("[yellow][警告]  同名の画像ファイルが複数回参照されています:[/yellow]")
        for filename, count in duplicates.items():
            self.console.print(f"[yellow]   - {filename} ({count}回参照)[/yellow]")

    # Watch mode
    def watch_start(self, file_path: str) -> None:
        """Display watch mode start"""
        self.console.print(f"\n[cyan][監視] ファイル監視を開始:[/cyan] {file_path}")
        self.console.print("[dim]   ファイルを編集すると自動的に再生成されます[/dim]")
        self.console.print("[dim]   停止するには Ctrl+C を押してください[/dim]")

    def watch_file_changed(self, file_name: str) -> None:
        """Display file change notification"""
        self.console.print(f"\n[blue][更新] ファイルが変更されました:[/blue] {file_name}")

    def watch_update_complete(self, timestamp: str) -> None:
        """Display watch update completion"""
        self.console.print(f"[green][更新] 自動更新完了:[/green] {timestamp}")

    def watch_update_error(self, error: str) -> None:
        """Display watch update error"""
        self.console.print(f"[red][エラー] 自動更新エラー:[/red] {error}")

    def watch_stopped(self) -> None:
        """Display watch mode stopped"""
        self.console.print("\n[yellow] ファイル監視を停止しました[/yellow]")

    # Sample generation
    def sample_generation(self, output_path: str) -> None:
        """Display sample generation info"""
        self.console.print(f"[cyan][処理] サンプルを生成中: {output_path}[/cyan]")

    def sample_complete(
        self, output_path: str, txt_name: str, html_name: str, image_count: int
    ) -> None:
        """Display sample generation completion"""
        self.console.print("[green][完了] サンプル生成完了！[/green]")
        self.console.print(f"[green]   [フォルダ] 出力先: {output_path}[/green]")
        self.console.print(f"[green]   [ファイル] テキスト: {txt_name}[/green]")
        self.console.print(f"[green]   [ブラウザ] HTML: {html_name}[/green]")
        self.console.print(f"[green]   [画像]  画像: {image_count}個[/green]")

    # Test case detection
    def test_cases_detected(self, count: int, cases: List[Tuple[int, str, str]]) -> None:
        """Display test case detection"""
        self.console.print(f"[blue][テスト] テストケース検出: {count}個[/blue]")
        for i, (num, category, description) in enumerate(cases[:5]):
            self.console.print(f"[dim]   - [TEST-{num}] {category}: {description}[/dim]")
        if len(cases) > 5:
            self.console.print(f"[dim]   ... 他 {len(cases) - 5}個[/dim]")

    # Test file generation
    def test_file_generation(self, double_click_mode: bool = False) -> None:
        """Display test file generation start"""
        if double_click_mode:
            self.console.print("[cyan][設定] テスト用記法網羅ファイルを生成中...[/cyan]")
            self.console.print(
                "[dim]   すべての記法パターンを網羅したテストファイルを作成します[/dim]"
            )
        else:
            self.console.print("[cyan][設定] テスト用記法網羅ファイルを生成中...[/cyan]")

    def test_file_complete(self, output_file: str, double_click_mode: bool = False) -> None:
        """Display test file generation completion"""
        if double_click_mode:
            self.console.print(f"[green][完了] テストファイルを生成しました:[/green] {output_file}")
        else:
            self.console.print(f"[green][完了] テストファイルを生成しました:[/green] {output_file}")

    def test_conversion_start(self, double_click_mode: bool = False) -> None:
        """Display test conversion start"""
        if double_click_mode:
            self.console.print("\n[yellow][テスト] 生成されたファイルをHTMLに変換中...[/yellow]")
            self.console.print("[dim]   すべての記法が正しく処理されるか" "テストしています[/dim]")
        else:
            self.console.print(
                "\n[yellow][テスト] 生成されたファイルのテスト変換を実行中...[/yellow]"
            )

    def test_conversion_complete(
        self, test_output_file: str, output_file: str, double_click_mode: bool = False
    ) -> None:
        """Display test conversion completion"""
        if double_click_mode:
            self.console.print(f"[green][完了] HTML変換成功:[/green] {test_output_file}")
            self.console.print(
                "[dim]   [ファイル] テストファイル (.txt) と変換結果 (.html) の両方が生成されました[/dim]"
            )

            # File size info
            txt_size = Path(output_file).stat().st_size
            html_size = Path(test_output_file).stat().st_size
            self.console.print(f"[dim]    テキストファイル: {txt_size:,} バイト[/dim]")
            self.console.print(f"[dim]    HTMLファイル: {html_size:,} バイト[/dim]")
        else:
            self.console.print(f"[green][完了] テスト変換成功:[/green] {test_output_file}")

    def test_conversion_error(self, error: str) -> None:
        """Display test conversion error"""
        self.console.print(f"[red][エラー] テスト変換中にエラーが発生しました: {error}[/red]")
