"""
コンソール メッセージング

成功・エラー・警告・情報メッセージの表示機能
Issue #492 Phase 5A - console_ui.py分割
"""

from typing import Any, Optional


class ConsoleMessaging:
    """Console messaging functionality

    Handles all types of user feedback messages including
    success, error, warning, and information displays.
    """

    def __init__(self, console: Any) -> None:
        """Initialize with a Rich Console instance"""
        self.console = console

    # Processing status messages
    def processing_start(self, message: str, file_path: Optional[str] = None) -> None:
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
    def success(self, message: str, file_path: Optional[str] = None) -> None:
        """Display success message"""
        if file_path:
            self.console.print(f"[green][完了] {message}:[/green] {file_path}")
        else:
            self.console.print(f"[green][完了] {message}[/green]")

    def conversion_complete(self, output_file: str) -> None:
        """Display conversion completion"""
        self.console.print(f"[green][完了] 完了:[/green] {output_file}")

    # Error messages
    def error(self, message: str, details: Optional[str] = None) -> None:
        """Display error message"""
        self.console.print(f"[red][エラー] エラー:[/red] {message}")
        if details:
            self.console.print(f"[dim]   {details}[/dim]")

    def file_error(self, file_path: str, error_type: str = "ファイルが見つかりません") -> None:
        """Display file error"""
        self.console.print(f"[red][エラー] ファイルエラー:[/red] {error_type}: {file_path}")

    def encoding_error(self, file_path: str) -> None:
        """Display encoding error"""
        self.console.print(
            "[red][エラー] エンコーディングエラー:[/red] ファイルを UTF-8 として読み込めません"
        )
        self.console.print(f"[dim]   ファイル: {file_path}[/dim]")

    def permission_error(self, error: str) -> None:
        """Display permission error"""
        self.console.print(f"[red][エラー] 権限エラー:[/red] ファイルにアクセスできません: {error}")

    def unexpected_error(self, error: str) -> None:
        """Display unexpected error"""
        self.console.print(f"[red][エラー] 予期しないエラー:[/red] {error}")
        self.console.print(
            "[dim]   詳細なエラー情報が必要な場合は、GitHubのissueで報告してください[/dim]"
        )

    # Warning messages
    def warning(self, message: str, details: Optional[str] = None) -> None:
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
                "[yellow]   これらのエラーは、" "記法の学習用にわざと含まれています[/yellow]"
            )
            self.console.print("[yellow]   HTMLファイルでエラー箇所を確認してください[/yellow]")
        else:
            self.console.print(
                f"[yellow][警告]  警告: {error_count}個のエラーが検出されました[/yellow]"
            )
            self.console.print("[yellow]   HTMLファイルでエラー箇所を確認してください[/yellow]")

    # Information messages
    def info(self, message: str, details: Optional[str] = None) -> None:
        """Display info message"""
        self.console.print(f"[blue][情報] {message}[/blue]")
        if details:
            self.console.print(f"[dim]   {details}[/dim]")

    def hint(self, message: str, details: Optional[str] = None) -> None:
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

    # Experimental features
    def experimental_feature(self, feature_name: str) -> None:
        """Display experimental feature warning"""
        self.console.print(f"[yellow][実験] 実験的機能を有効化:[/yellow] {feature_name}")
        self.console.print("[dim]   この機能は実験的で、予期しない動作をする可能性があります[/dim]")

    def no_preview_files(self) -> None:
        """Display no preview files message"""
        self.console.print("[dim][情報] プレビュー用HTMLファイルが見つかりませんでした[/dim]")

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

    # Statistics and details
    def statistics(self, stats: dict[str, Any]) -> None:
        """Display statistics"""
        if "total_nodes" in stats:
            self.console.print(f"[dim]   - 処理したブロック数: {stats['total_nodes']}[/dim]")
        if "file_size" in stats:
            self.console.print(f"[dim]   - ファイルサイズ: {stats['file_size']} 文字[/dim]")

        # Enhanced stats for large files
        if "input_size_mb" in stats and stats["input_size_mb"] > 1:
            self.console.print(f"[dim]   - 入力サイズ: {stats['input_size_mb']:.1f}MB[/dim]")
        if "output_size_mb" in stats and stats["output_size_mb"] > 1:
            self.console.print(f"[dim]   - 出力サイズ: {stats['output_size_mb']:.1f}MB[/dim]")

    def test_statistics(self, stats: dict[str, Any], double_click_mode: bool = False) -> None:
        """Display test generation statistics"""
        if double_click_mode:
            self.console.print(f"[dim]   [統計] 生成パターン数: {stats['total_patterns']}[/dim]")
            self.console.print(
                f"[dim]   [キーワード]  単一キーワード数: {stats['single_keywords']}[/dim]"
            )
            self.console.print(f"[dim]   [生成] ハイライト色数: {stats['highlight_colors']}[/dim]")
            self.console.print(f"[dim]    最大組み合わせ数: {stats['max_combinations']}[/dim]")
        else:
            self.console.print(f"[dim]   - 生成パターン数: {stats['total_patterns']}[/dim]")
            self.console.print(f"[dim]   - 単一キーワード数: {stats['single_keywords']}[/dim]")
            self.console.print(f"[dim]   - ハイライト色数: {stats['highlight_colors']}[/dim]")
            self.console.print(f"[dim]   - 最大組み合わせ数: {stats['max_combinations']}[/dim]")
