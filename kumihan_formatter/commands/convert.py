"""Convert command implementation

This module contains the main conversion functionality that was
previously part of the large cli.py file.
"""

import sys
import time
import webbrowser
import re
from pathlib import Path
from typing import Optional, Any

import click
from rich.progress import Progress

from ..ui.console_ui import ui
from ..core.file_ops import FileOperations, PathValidator, ErrorHandler
from ..core.error_handling import ErrorHandler as FriendlyErrorHandler
from ..core.syntax import check_files, ErrorSeverity
from ..core.error_reporting import ErrorReport, ErrorReportBuilder, DetailedError
from ..parser import parse
from ..renderer import render
# from ..config import load_config  # 簡素化: 使用しない


class ConvertCommand:
    """Convert command implementation"""
    
    def __init__(self):
        self.file_ops = FileOperations(ui=ui)
        self.path_validator = PathValidator()
        self.error_handler = ErrorHandler()
        self.friendly_error_handler = FriendlyErrorHandler(console_ui=ui)
    
    def execute(self, input_file: Optional[str], output: str, no_preview: bool,
                watch: bool, config: Optional[str], show_test_cases: bool,
                template_name: Optional[str], include_source: bool,
                syntax_check: bool = True) -> Path:
        """
        Execute convert command
        
        Args:
            input_file: Input file path
            output: Output directory
            no_preview: Skip browser preview
            watch: Enable watch mode
            config: Config file path (deprecated - ignored)
            show_test_cases: Show test cases
            template_name: Template name to use
            include_source: Include source toggle
            syntax_check: Enable syntax check before conversion
        
        Returns:
            Path to output file
        """
        try:
            if not input_file:
                ui.error("入力ファイルが指定されていません")
                ui.dim("テストファイル生成には --generate-test オプションを使用してください")
                sys.exit(1)
            
            # Validate input file
            input_path = self.path_validator.validate_input_file(input_file)
            
            # Check file size and show warnings for large files
            size_info = self.file_ops.get_file_size_info(input_path)
            if size_info['is_large']:
                # Show large file warning
                if not self.file_ops.check_large_file_warning(input_path):
                    ui.info("処理を中断しました")
                    sys.exit(0)
                
                # Show estimated processing time
                estimated_time = self.file_ops.estimate_processing_time(size_info['size_mb'])
                ui.hint(f"推定処理時間: {estimated_time}")
            
            # 簡素化: 設定ファイルは使用しない
            config_obj = None
            
            ui.processing_start("読み込み中", str(input_path))
            
            # Syntax check before conversion
            if syntax_check:
                error_report = self._perform_enhanced_syntax_check(input_path)
                if error_report.has_errors():
                    # 詳細なエラーレポートを表示
                    ui.error("記法エラーが検出されました。変換を中止します。")
                    ui.info("\n=== 詳細エラーレポート ===")
                    print(error_report.to_console_output())
                    
                    # エラーレポートファイルを生成
                    self._save_error_report(error_report, input_path, output)
                    
                    ui.dim("--no-syntax-check オプションで記法チェックをスキップできます")
                    sys.exit(1)
                elif error_report.has_warnings():
                    # 警告のみの場合は続行するが表示
                    ui.warning("記法に関する警告があります:")
                    print(error_report.to_console_output())
            
            # Initial conversion
            output_file = self._convert_file(
                input_path, output, config_obj, 
                show_test_cases=show_test_cases,
                template=template_name,
                include_source=include_source
            )
            
            # Browser preview
            if not no_preview:
                ui.browser_opening()
                webbrowser.open(output_file.resolve().as_uri())
            
            # Watch mode
            if watch:
                self._handle_watch_mode(
                    input_file, output, config_obj, show_test_cases,
                    template_name, include_source, syntax_check
                )
            
            return output_file
            
        except FileNotFoundError as e:
            error = self.friendly_error_handler.handle_exception(
                e, context={"file_path": input_file or ""}
            )
            self.friendly_error_handler.display_error(error, verbose=True)
            sys.exit(1)
        except UnicodeDecodeError as e:
            error = self.friendly_error_handler.handle_exception(
                e, context={"file_path": input_file or ""}
            )
            self.friendly_error_handler.display_error(error, verbose=True)
            sys.exit(1)
        except PermissionError as e:
            error = self.friendly_error_handler.handle_exception(
                e, context={"file_path": input_file or "", "operation": "読み取り"}
            )
            self.friendly_error_handler.display_error(error, verbose=True)
            sys.exit(1)
        except Exception as e:
            error = self.friendly_error_handler.handle_exception(
                e, context={"input_file": input_file, "operation": "ファイル変換"}
            )
            self.friendly_error_handler.display_error(error, verbose=True)
            sys.exit(1)
    
    def _perform_syntax_check(self, input_path: Path) -> bool:
        """
        Perform syntax check on input file
        
        Args:
            input_path: Path to input file
            
        Returns:
            bool: True if no errors, False if errors found
        """
        ui.info("記法チェック", f"{input_path.name} の記法を検証中...")
        
        try:
            # Run syntax check
            results = check_files([input_path], verbose=False)
            
            if not results:
                ui.success("記法チェック", "記法エラーは見つかりませんでした")
                return True
            
            # Check for errors (not warnings)
            error_count = sum(1 for errors in results.values() 
                            for error in errors if error.severity == ErrorSeverity.ERROR)
            warning_count = sum(1 for errors in results.values() 
                              for error in errors if error.severity == ErrorSeverity.WARNING)
            
            if error_count > 0:
                ui.error("記法エラー", f"{error_count} 個のエラーが見つかりました")
                
                # Show first few errors
                for file_path, errors in results.items():
                    for error in errors[:3]:  # Show first 3 errors
                        if error.severity == ErrorSeverity.ERROR:
                            ui.dim(f"  行 {error.line_number}: {error.message}")
                
                if sum(len(errors) for errors in results.values()) > 3:
                    ui.dim(f"  ... 他 {sum(len(errors) for errors in results.values()) - 3} 個の問題")
                
                ui.dim("詳細は check-syntax コマンドで確認してください")
                return False
            
            elif warning_count > 0:
                ui.warning("記法警告", f"{warning_count} 個の警告がありますが、変換を続行します")
                return True
            
            return True
            
        except Exception as e:
            ui.warning("記法チェック", f"記法チェック中にエラーが発生しました: {e}")
            ui.dim("記法チェックをスキップして変換を続行します")
            return True  # Continue conversion on check failure
    
    def _convert_file(self, input_path: Path, output: str, config=None,
                     show_stats: bool = True, show_test_cases: bool = False,
                     template: Optional[str] = None, include_source: bool = False) -> Path:
        """Convert single file to HTML"""
        
        # Read file
        text = self.file_ops.read_text_file(input_path)
        
        # Extract test cases if requested
        if show_test_cases:
            self._show_test_cases(text)
        
        # Parse
        ui.parsing_status()
        ast = self._parse_with_progress(text, config)
        
        # Render
        ui.rendering_status()
        html = self._render_with_progress(
            ast, config, template, input_path.stem, 
            text if include_source else None,
            input_path.name if include_source else None
        )
        
        # Write output
        output_path = Path(output)
        self.file_ops.ensure_directory(output_path)
        output_file = output_path / f"{input_path.stem}.html"
        self.file_ops.write_text_file(output_file, html)
        
        # Copy images
        self.file_ops.copy_images(input_path, output_path, ast)
        
        # Show statistics
        if show_stats:
            self._show_conversion_stats(ast, text, output_file, input_path)
        
        return output_file
    
    def _parse_with_progress(self, text: str, config) -> Any:
        """Parse text with progress indication"""
        file_size = len(text)
        size_mb = file_size / (1024 * 1024)
        
        with Progress() as progress:
            # More detailed progress for large files
            if size_mb > 10:  # 10MB以上
                task = progress.add_task(
                    f"[cyan]大規模ファイルを解析中 ({size_mb:.1f}MB)", 
                    total=100
                )
            else:
                task = progress.add_task("[cyan]テキストを解析中", total=100)
            
            start_time = time.time()
            
            # Simulate chunked processing for very large files
            if size_mb > 50:  # 50MB以上は分割表示
                # chunk_size = len(text) // 10  # For future chunked processing
                for i in range(10):
                    # chunk_start = i * chunk_size  # Simulate chunked processing
                    # chunk_end = min((i + 1) * chunk_size, len(text))
                    progress.update(task, completed=i * 10)
                    time.sleep(0.1)  # Simulate processing time
                
                # Final parse
                ast = parse(text, config)
                progress.update(task, completed=100)
            else:
                ast = parse(text, config)
                elapsed = time.time() - start_time
                
                if elapsed < 0.5:
                    for i in range(0, 101, 20):
                        progress.update(task, completed=i)
                        time.sleep(0.05)
                progress.update(task, completed=100)
        
        return ast
    
    def _render_with_progress(self, ast: Any, config, template: Optional[str],
                            title: str, source_text: Optional[str] = None,
                            source_filename: Optional[str] = None) -> str:
        """Render AST to HTML with progress indication"""
        node_count = len(ast) if ast else 0
        
        with Progress() as progress:
            # More detailed progress for large ASTs
            if node_count > 1000:  # 1000ノード以上
                task = progress.add_task(
                    f"[yellow]大規模データを変換中 ({node_count:,}要素)", 
                    total=100
                )
            else:
                task = progress.add_task("[yellow]HTMLを生成中", total=100)
            
            start_time = time.time()
            
            # Simulate progress for large renders
            if node_count > 5000:  # 5000ノード以上は段階的表示
                for i in range(0, 101, 10):
                    progress.update(task, completed=i)
                    time.sleep(0.05)
            
            if source_text:
                html = render(ast, config, template=template, title=title,
                            source_text=source_text, source_filename=source_filename)
            else:
                html = render(ast, config, template=template, title=title)
            
            elapsed = time.time() - start_time
            
            if elapsed < 0.5 and node_count <= 5000:
                for i in range(0, 101, 25):
                    progress.update(task, completed=i)
                    time.sleep(0.04)
            progress.update(task, completed=100)
        
        return html
    
    def _show_test_cases(self, text: str) -> None:
        """Extract and show test cases from text"""
        test_case_pattern = r'# \[TEST-(\d+)\] ([^:]+): (.+)'
        test_cases = re.findall(test_case_pattern, text)
        
        if test_cases:
            ui.test_cases_detected(len(test_cases), test_cases)
    
    def _show_conversion_stats(self, ast: Any, text: str, output_file: Path, input_path: Path) -> None:
        """Show conversion statistics"""
        # Error statistics
        error_count = sum(1 for node in ast if getattr(node, 'type', None) == 'error')
        if error_count > 0:
            # Check if it's a sample file
            is_sample = input_path.name in ['02-basic.txt', '03-comprehensive.txt']
            ui.validation_warning(error_count, is_sample)
        
        ui.conversion_complete(str(output_file))
        
        # Show enhanced statistics for large files
        input_size_info = self.file_ops.get_file_size_info(input_path)
        output_size_info = self.file_ops.get_file_size_info(output_file)
        
        stats = {
            'total_nodes': len(ast),
            'file_size': len(text),
            'input_size_mb': input_size_info['size_mb'],
            'output_size_mb': output_size_info['size_mb'],
            'compression_ratio': output_size_info['size_mb'] / input_size_info['size_mb'] if input_size_info['size_mb'] > 0 else 0
        }
        
        ui.statistics(stats)
        
        # Show additional info for large files
        if input_size_info['is_large']:
            ui.dim(f"入力ファイル: {input_size_info['size_mb']:.1f}MB → 出力ファイル: {output_size_info['size_mb']:.1f}MB")
            if stats['compression_ratio'] > 1:
                ui.hint(f"HTML変換により約{stats['compression_ratio']:.1f}倍のサイズになりました")
    
    def _handle_watch_mode(self, input_file: str, output: str, config_obj,
                          show_test_cases: bool, template_name: Optional[str],
                          include_source: bool, syntax_check: bool = True) -> None:
        """Handle watch mode for automatic file regeneration"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            ui.error("watchdog ライブラリがインストールされていません")
            ui.dim("pip install watchdog を実行してください")
            sys.exit(1)
        
        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, command_instance):
                self.command = command_instance
                self.input_file = Path(input_file)
                self.output = output
                self.config = config_obj
                self.show_test_cases = show_test_cases
                self.template_name = template_name
                self.include_source = include_source
                self.syntax_check = syntax_check
                self.last_modified = 0
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                modified_path = Path(event.src_path)
                if modified_path.resolve() == self.input_file.resolve():
                    # Prevent duplicate events
                    current_time = time.time()
                    if current_time - self.last_modified < 1:
                        return
                    self.last_modified = current_time
                    
                    try:
                        ui.watch_file_changed(modified_path.name)
                        
                        # Syntax check in watch mode
                        if self.syntax_check:
                            if not self.command._perform_syntax_check(self.input_file):
                                ui.watch_update_error("記法エラーにより変換をスキップしました")
                                return
                        
                        self.command._convert_file(
                            self.input_file, self.output, self.config,
                            show_stats=False, show_test_cases=self.show_test_cases,
                            template=self.template_name, include_source=self.include_source
                        )
                        ui.watch_update_complete(time.strftime('%H:%M:%S'))
                    except Exception as e:
                        ui.watch_update_error(str(e))
        
        input_path = Path(input_file)
        ui.watch_start(str(input_path))
        
        event_handler = FileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=str(input_path.parent), recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            ui.watch_stopped()
            observer.stop()
        observer.join()
    
    def _perform_enhanced_syntax_check(self, input_path: Path) -> ErrorReport:
        """拡張された記法チェックを実行してエラーレポートを返す"""
        error_report = ErrorReport(source_file=input_path)
        
        try:
            # 既存の記法チェックを実行
            results = check_files([input_path])
            
            # resultsは辞書形式 {file_path: [SyntaxError, ...]}
            for file_path_str, syntax_errors in results.items():
                for syntax_error in syntax_errors:
                    # SyntaxErrorからDetailedErrorに変換
                    detailed_error = self._convert_syntax_error_to_detailed(syntax_error, input_path)
                    error_report.add_error(detailed_error)
            
            # 追加の詳細チェック
            self._add_enhanced_checks(input_path, error_report)
            
        except Exception as e:
            # チェック中にエラーが発生した場合
            critical_error = ErrorReportBuilder.create_syntax_error(
                title="記法チェック中にエラーが発生",
                message=f"記法チェック処理中に予期しないエラーが発生しました: {str(e)}",
                file_path=input_path,
                line_number=1,
                problem_text="（不明）"
            )
            critical_error.severity = self._get_critical_severity()
            error_report.add_error(critical_error)
        
        return error_report
    
    def _convert_syntax_error_to_detailed(self, syntax_error, input_path: Path) -> DetailedError:
        """既存のSyntaxErrorをDetailedErrorに変換"""
        from ..core.error_reporting import ErrorSeverity, ErrorCategory, ErrorLocation, FixSuggestion
        
        # エラータイプに基づいてカテゴリを決定
        if hasattr(syntax_error, 'error_type'):
            error_type_str = str(syntax_error.error_type).lower()
            if 'keyword' in error_type_str:
                category = ErrorCategory.KEYWORD
            elif 'marker' in error_type_str:
                category = ErrorCategory.SYNTAX
            elif 'block' in error_type_str:
                category = ErrorCategory.STRUCTURE
            else:
                category = ErrorCategory.SYNTAX
        else:
            category = ErrorCategory.SYNTAX
        
        # 修正提案を作成
        suggestions = []
        if hasattr(syntax_error, 'suggestion') and syntax_error.suggestion:
            suggestions.append(FixSuggestion(
                description=syntax_error.suggestion,
                confidence=0.8
            ))
        
        # 詳細エラーを作成
        return DetailedError(
            error_id=f"syntax_{syntax_error.line_number}_{hash(syntax_error.message) % 10000}",
            severity=ErrorSeverity.ERROR,
            category=category,
            title=str(syntax_error.error_type) if hasattr(syntax_error, 'error_type') else "記法エラー",
            message=syntax_error.message,
            file_path=input_path,
            location=ErrorLocation(line=syntax_error.line_number),
            fix_suggestions=suggestions,
            help_url="https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md"
        )
    
    def _add_enhanced_checks(self, input_path: Path, error_report: ErrorReport) -> None:
        """追加の詳細チェックを実行"""
        from ..core.error_reporting import FixSuggestion
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # 単独の;;;マーカーチェック
                if line_stripped == ';;;':
                    error = ErrorReportBuilder.create_syntax_error(
                        title="単独の;;;マーカー",
                        message="ブロック開始マーカーなしに ;;; が見つかりました",
                        file_path=input_path,
                        line_number=line_num,
                        problem_text=line_stripped,
                        suggestions=[
                            FixSuggestion(
                                description="この行を削除する",
                                original_text=line_stripped,
                                suggested_text="",
                                action_type="delete",
                                confidence=0.9
                            ),
                            FixSuggestion(
                                description="内容を追加してブロックを完成させる",
                                original_text=line_stripped,
                                suggested_text="何らかの内容\n;;;",
                                action_type="replace",
                                confidence=0.7
                            )
                        ]
                    )
                    error_report.add_error(error)
                
                # 不完全なマーカーチェック
                if line_stripped.startswith(';;;') and line_stripped != ';;;':
                    # 開始マーカーと思われるが、対応する終了マーカーを探す
                    found_end = False
                    for check_line_num in range(line_num, len(lines)):
                        if lines[check_line_num].strip() == ';;;':
                            found_end = True
                            break
                    
                    if not found_end:
                        error = ErrorReportBuilder.create_syntax_error(
                            title="未閉じブロック",
                            message=f"ブロック開始マーカー '{line_stripped}' に対応する閉じマーカー ;;; が見つかりません",
                            file_path=input_path,
                            line_number=line_num,
                            problem_text=line_stripped,
                            suggestions=[
                                FixSuggestion(
                                    description="ブロックの最後に ;;; を追加する",
                                    action_type="insert",
                                    confidence=0.9
                                )
                            ]
                        )
                        error_report.add_error(error)
        
        except Exception:
            # ファイル読み込みエラーなど
            pass
    
    def _save_error_report(self, error_report: ErrorReport, input_path: Path, output_dir: str) -> None:
        """エラーレポートをファイルに保存"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            report_file = output_path / f"{input_path.stem}_errors.txt"
            error_report.to_file_report(report_file)
            
            ui.info(f"詳細エラーレポートを保存しました: {report_file}")
            ui.dim("このファイルには問題箇所と修正提案が含まれています")
            
        except Exception as e:
            ui.warning(f"エラーレポートの保存に失敗しました: {e}")
    
    def _get_critical_severity(self):
        """Critical重要度を取得"""
        from ..core.error_reporting import ErrorSeverity
        return ErrorSeverity.CRITICAL


def create_convert_command():
    """Create the convert click command"""
    
    @click.command()
    @click.argument("input_file", type=click.Path(exists=True), required=False)
    @click.option("-o", "--output", default="dist", help="出力ディレクトリ")
    @click.option("--no-preview", is_flag=True, help="HTML生成後にブラウザを開かない")
    @click.option("--watch", is_flag=True, help="ファイルの変更を監視して自動再生成")
    # @click.option("--config", type=click.Path(exists=True), help="設定ファイルのパス")  # 簡素化: 削除
    @click.option("--show-test-cases", is_flag=True, help="テストケース名を表示（テスト用ファイル変換時）")
    @click.option("--with-source-toggle", is_flag=True, help="記法と結果を切り替えるトグル機能付きで出力")
    @click.option("--no-syntax-check", is_flag=True, help="変換前の記法チェックをスキップ")
    @click.option("--experimental", type=str, help="実験的機能を有効化 (例: scroll-sync)")
    def convert(input_file, output, no_preview, watch, show_test_cases, 
                with_source_toggle, no_syntax_check, experimental):
        """テキストファイルをHTMLに変換します"""
        
        # Determine source toggle usage
        # Only ask for confirmation if the flag was not explicitly provided
        use_source_toggle = with_source_toggle
        
        # Template selection (considering experimental features)
        template_name = None
        if use_source_toggle:
            if experimental == "scroll-sync":
                ui.experimental_feature("スクロール同期")
                template_name = "experimental/base-with-scroll-sync.html.j2"
            else:
                template_name = "base-with-source-toggle.html.j2"
        
        command = ConvertCommand()
        command.execute(
            input_file, output, no_preview, watch, None,
            show_test_cases, template_name, use_source_toggle,
            syntax_check=not no_syntax_check
        )
    
    return convert