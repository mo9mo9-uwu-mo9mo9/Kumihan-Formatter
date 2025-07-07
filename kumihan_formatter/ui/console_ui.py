"""Console UI utilities for Kumihan-Formatter

Centralized console output and user interaction management.
All console.print() calls should go through this module.

Dependencies:
- rich: For console styling and progress display
- console_encoding: For platform-specific encoding setup (side effect removed)

Note: Uses lazy initialization pattern to avoid import-time side effects.
Use get_console_ui() function instead of direct global instance access.
"""

import sys

from rich.console import Console  # type: ignore
from rich.progress import Progress  # type: ignore

from .console_encoding import ConsoleEncodingSetup


class ConsoleUI:
    """Console UI management class

    Centralizes all console output and user interaction logic.
    Provides consistent formatting and error handling.
    """

    def __init__(self) -> None:
        """Initialize console UI with proper encoding setup"""
        ConsoleEncodingSetup.setup_encoding()
        self.console = self._create_console()

    def _create_console(self) -> Console:  # type: ignore[no-any-unimported]
        """Create console instance with safe settings"""
        try:
            # For Windows, use specific settings
            if sys.platform == "win32":
                return Console(
                    force_terminal=True,
                    legacy_windows=True,
                    color_system="windows",
                    # Ensure proper width detection
                    width=None,
                )
            else:
                return Console(force_terminal=True)
        except Exception:
            # Minimal console as fallback
            return Console(legacy_windows=True)

    # Processing status messages
    def processing_start(self, message: str, file_path: str = None) -> None:  # type: ignore
        """Display processing start message"""
        if file_path:
            self.console.print(f"[green][ドキュメント] 読み込み中:[/green] {file_path}")
        self.console.print(f"[cyan][処理] {message}[/cyan]")

    def processing_step(self, step: str) -> None:
        """Display processing step"""
        self.console.print(f"[cyan][処理] {step}[/cyan]")

    def parsing_status(self) -> None:
        """Display parsing status"""
        self.console.print("[cyan][処理] パース中...[/cyan]")

    def rendering_status(self) -> None:
        """Display rendering status"""
        self.console.print("[yellow][生成] HTML生成中...[/yellow]")

    # Success messages
    def success(self, message: str, file_path: str = None) -> None:  # type: ignore
        """Display success message"""
        if file_path:
            self.console.print(f"[green][完了] {message}:[/green] {file_path}")
        else:
            self.console.print(f"[green][完了] {message}[/green]")

    def conversion_complete(self, output_file: str) -> None:
        """Display conversion completion"""
        self.console.print(f"[green][完了] 完了:[/green] {output_file}")

    # Error messages
    def error(self, message: str, details: str = None) -> None:  # type: ignore
        """Display error message"""
        self.console.print(f"[red][エラー] エラー:[/red] {message}")
        if details:
            self.console.print(f"[dim]   {details}[/dim]")

    def file_error(
        self, file_path: str, error_type: str = "ファイルが見つかりません"
    ) -> None:
        """Display file error"""
        self.console.print(
            f"[red][エラー] ファイルエラー:[/red] {error_type}: {file_path}"
        )

    def encoding_error(self, file_path: str) -> None:
        """Display encoding error"""
        self.console.print(
            "[red][エラー] エンコーディングエラー:[/red] ファイルを UTF-8 として読み込めません"
        )
        self.console.print(f"[dim]   ファイル: {file_path}[/dim]")

    def permission_error(self, error: str) -> None:
        """Display permission error"""
        self.console.print(
            f"[red][エラー] 権限エラー:[/red] ファイルにアクセスできません: {error}"
        )

    def unexpected_error(self, error: str) -> None:
        """Display unexpected error"""
        self.console.print(f"[red][エラー] 予期しないエラー:[/red] {error}")
        self.console.print(
            "[dim]   詳細なエラー情報が必要な場合は、GitHubのissueで報告してください[/dim]"
        )

    # Warning messages
    def warning(self, message: str, details: str = None) -> None:  # type: ignore
        """Display warning message"""
        self.console.print(f"[yellow][警告] {message}[/yellow]")
        if details:
            self.console.print(f"[yellow]   {details}[/yellow]")

    def validation_warning(self, error_count: int, is_sample: bool = False) -> None:
        """Display validation warnings"""
        if is_sample:
            self.console.print(
                f"[yellow][警告]  {error_count}個のエラーが検出されました"
                "（想定されたエラーです）[/yellow]"
            )
            self.console.print(
                "[yellow]   これらのエラーは、"
                "記法の学習用にわざと含まれています[/yellow]"
            )
            self.console.print(
                "[yellow]   HTMLファイルでエラー箇所を確認してください[/yellow]"
            )
        else:
            self.console.print(
                f"[yellow][警告]  警告: {error_count}個のエラーが検出されました[/yellow]"
            )
            self.console.print(
                "[yellow]   HTMLファイルでエラー箇所を確認してください[/yellow]"
            )

    # Information messages
    def info(self, message: str, details: str = None) -> None:  # type: ignore
        """Display info message"""
        self.console.print(f"[blue][情報] {message}[/blue]")
        if details:
            self.console.print(f"[dim]   {details}[/dim]")

    def hint(self, message: str, details: str = None) -> None:  # type: ignore
        """Display hint message"""
        self.console.print(f"[cyan][ヒント] {message}[/cyan]")
        if details:
            self.console.print(f"[dim]   {details}[/dim]")

    def dim(self, message: str) -> None:
        """Display dimmed message"""
        self.console.print("[dim]   {}[/dim]".format(message))

    # Browser and preview
    def browser_opening(self) -> None:
        """Display browser opening message"""
        self.console.print("[blue][ブラウザ] ブラウザで開いています...[/blue]")

    def browser_preview(self) -> None:
        """Display browser preview message"""
        self.console.print("[blue][プレビュー] ブラウザでプレビューを表示中...[/blue]")

    # File operations
    def file_copied(self, count: int) -> None:
        """Display file copy count"""
        self.console.print(
            "[green]{}個の画像ファイルをコピーしました[/green]".format(count)
        )

    def files_missing(self, files: list) -> None:  # type: ignore
        """Display missing files"""
        self.console.print(
            f"[red][エラー] {len(files)}個の画像ファイルが" "見つかりません:[/red]"
        )
        for filename in files:
            self.console.print(f"[red]   - {filename}[/red]")

    def duplicate_files(self, duplicates: dict) -> None:  # type: ignore
        """Display duplicate files warning"""
        self.console.print(
            "[yellow][警告]  同名の画像ファイルが複数回参照されています:[/yellow]"
        )
        for filename, count in duplicates.items():
            self.console.print(f"[yellow]   - {filename} ({count}回参照)[/yellow]")

    # Statistics and details
    def statistics(self, stats: dict) -> None:  # type: ignore
        """Display statistics"""
        if "total_nodes" in stats:
            self.console.print(
                f"[dim]   - 処理したブロック数: {stats['total_nodes']}[/dim]"
            )
        if "file_size" in stats:
            self.console.print(
                f"[dim]   - ファイルサイズ: {stats['file_size']} 文字[/dim]"
            )

        # Enhanced stats for large files
        if "input_size_mb" in stats and stats["input_size_mb"] > 1:
            self.console.print(
                f"[dim]   - 入力サイズ: {stats['input_size_mb']:.1f}MB[/dim]"
            )
        if "output_size_mb" in stats and stats["output_size_mb"] > 1:
            self.console.print(
                f"[dim]   - 出力サイズ: {stats['output_size_mb']:.1f}MB[/dim]"
            )

    def test_statistics(self, stats: dict, double_click_mode: bool = False) -> None:  # type: ignore
        """Display test generation statistics"""
        if double_click_mode:
            self.console.print(
                f"[dim]   [統計] 生成パターン数: {stats['total_patterns']}[/dim]"
            )
            self.console.print(
                f"[dim]   [キーワード]  単一キーワード数: {stats['single_keywords']}[/dim]"
            )
            self.console.print(
                f"[dim]   [生成] ハイライト色数: {stats['highlight_colors']}[/dim]"
            )
            self.console.print(
                f"[dim]    最大組み合わせ数: {stats['max_combinations']}[/dim]"
            )
        else:
            self.console.print(
                f"[dim]   - 生成パターン数: {stats['total_patterns']}[/dim]"
            )
            self.console.print(
                f"[dim]   - 単一キーワード数: {stats['single_keywords']}[/dim]"
            )
            self.console.print(
                f"[dim]   - ハイライト色数: {stats['highlight_colors']}[/dim]"
            )
            self.console.print(
                f"[dim]   - 最大組み合わせ数: {stats['max_combinations']}[/dim]"
            )

    # User input
    def input(self, prompt: str) -> str:
        """Get user input with styled prompt"""
        return self.console.input(prompt)  # type: ignore[no-any-return]

    def confirm_source_toggle(self) -> bool:
        """Confirm source toggle feature usage"""
        self.hint(
            "記法と結果を切り替えて表示する機能があります",
            "改行処理などの動作を実際に確認しながら記法を学習できます",
        )
        response = self.input("[yellow]この機能を使用しますか？ (Y/n): [/yellow]")
        return response.lower() in ["y", "yes", ""]

    # Experimental features
    def experimental_feature(self, feature_name: str) -> None:
        """Display experimental feature warning"""
        self.console.print(
            f"[yellow][実験] 実験的機能を有効化:[/yellow] {feature_name}"
        )
        self.console.print(
            "[dim]   この機能は実験的で、予期しない動作をする可能性があります[/dim]"
        )

    # Watch mode
    def watch_start(self, file_path: str) -> None:
        """Display watch mode start"""
        self.console.print(f"\n[cyan][監視] ファイル監視を開始:[/cyan] {file_path}")
        self.console.print("[dim]   ファイルを編集すると自動的に再生成されます[/dim]")
        self.console.print("[dim]   停止するには Ctrl+C を押してください[/dim]")

    def watch_file_changed(self, file_name: str) -> None:
        """Display file change notification"""
        self.console.print(
            f"\n[blue][更新] ファイルが変更されました:[/blue] {file_name}"
        )

    def watch_update_complete(self, timestamp: str) -> None:
        """Display watch update completion"""
        self.console.print(f"[green][更新] 自動更新完了:[/green] {timestamp}")

    def watch_update_error(self, error: str) -> None:
        """Display watch update error"""
        self.console.print(f"[red][エラー] 自動更新エラー:[/red] {error}")

    def watch_stopped(self) -> None:
        """Display watch mode stopped"""
        self.console.print("\n[yellow] ファイル監視を停止しました[/yellow]")

    def no_preview_files(self) -> None:
        """Display no preview files message"""
        self.console.print(
            "[dim][情報] プレビュー用HTMLファイルが見つかりませんでした[/dim]"
        )

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
    def test_cases_detected(self, count: int, cases: list) -> None:  # type: ignore
        """Display test case detection"""
        self.console.print(f"[blue][テスト] テストケース検出: {count}個[/blue]")
        for i, (num, category, description) in enumerate(cases[:5]):
            self.console.print(
                f"[dim]   - [TEST-{num}] {category}: {description}[/dim]"
            )
        if len(cases) > 5:
            self.console.print(f"[dim]   ... 他 {len(cases) - 5}個[/dim]")

    # Test file generation
    def test_file_generation(self, double_click_mode: bool = False) -> None:
        """Display test file generation start"""
        if double_click_mode:
            self.console.print(
                "[cyan][設定] テスト用記法網羅ファイルを生成中...[/cyan]"
            )
            self.console.print(
                "[dim]   すべての記法パターンを網羅したテストファイルを作成します[/dim]"
            )
        else:
            self.console.print(
                "[cyan][設定] テスト用記法網羅ファイルを生成中...[/cyan]"
            )

    def test_file_complete(
        self, output_file: str, double_click_mode: bool = False
    ) -> None:
        """Display test file generation completion"""
        if double_click_mode:
            self.console.print(
                f"[green][完了] テストファイルを生成しました:[/green] {output_file}"
            )
        else:
            self.console.print(
                f"[green][完了] テストファイルを生成しました:[/green] {output_file}"
            )

    def test_conversion_start(self, double_click_mode: bool = False) -> None:
        """Display test conversion start"""
        if double_click_mode:
            self.console.print(
                "\n[yellow][テスト] 生成されたファイルをHTMLに変換中...[/yellow]"
            )
            self.console.print(
                "[dim]   すべての記法が正しく処理されるか" "テストしています[/dim]"
            )
        else:
            self.console.print(
                "\n[yellow][テスト] 生成されたファイルのテスト変換を実行中...[/yellow]"
            )

    def test_conversion_complete(
        self, test_output_file: str, output_file: str, double_click_mode: bool = False
    ) -> None:
        """Display test conversion completion"""
        if double_click_mode:
            self.console.print(
                f"[green][完了] HTML変換成功:[/green] {test_output_file}"
            )
            self.console.print(
                "[dim]   [ファイル] テストファイル (.txt) と変換結果 (.html) の両方が生成されました[/dim]"
            )

            # File size info
            from pathlib import Path

            txt_size = Path(output_file).stat().st_size
            html_size = Path(test_output_file).stat().st_size
            self.console.print(f"[dim]    テキストファイル: {txt_size:,} バイト[/dim]")
            self.console.print(f"[dim]    HTMLファイル: {html_size:,} バイト[/dim]")
        else:
            self.console.print(
                f"[green][完了] テスト変換成功:[/green] {test_output_file}"
            )

    def test_conversion_error(self, error: str) -> None:
        """Display test conversion error"""
        self.console.print(
            f"[red][エラー] テスト変換中にエラーが発生しました: {error}[/red]"
        )

    # Large file processing
    def large_file_detected(self, size_mb: float, estimated_time: str) -> None:
        """Display large file detection"""
        self.console.print(f"[yellow][検出] 大規模ファイル: {size_mb:.1f}MB[/yellow]")
        self.console.print(f"[dim]   推定処理時間: {estimated_time}[/dim]")

    def large_file_processing_start(self) -> None:
        """Display large file processing start"""
        self.console.print("[blue][大規模] 大規模ファイル処理を開始します[/blue]")
        self.console.print("[dim]   メモリ使用量を最適化して処理中...[/dim]")

    def memory_optimization_info(self, optimization_type: str) -> None:
        """Display memory optimization info"""
        self.console.print(f"[cyan][最適化] {optimization_type}[/cyan]")

    def performance_warning(self, warning: str) -> None:
        """Display performance warning"""
        self.console.print(f"[yellow][パフォーマンス] {warning}[/yellow]")

    # Generic progress
    def create_progress(self) -> Progress:  # type: ignore[no-any-unimported]
        """Create a progress instance"""
        return Progress()


# Global console UI instance - removed to avoid import-time side effects
# Use get_console_ui() function instead
_console_ui_instance = None


def get_console_ui() -> ConsoleUI:
    """Get the global console UI instance (lazy initialization)"""
    global _console_ui_instance
    if _console_ui_instance is None:
        _console_ui_instance = ConsoleUI()
    return _console_ui_instance
