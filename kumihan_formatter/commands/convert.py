"""Convert command implementation

This module contains the main conversion functionality that was
previously part of the large cli.py file.
"""

import sys
import time
import webbrowser
import re
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.progress import Progress

from ..ui.console_ui import ui
from ..core.file_ops import FileOperations, PathValidator, ErrorHandler
from ..parser import parse
from ..renderer import render
from ..config import load_config


class ConvertCommand:
    """Convert command implementation"""
    
    def __init__(self):
        self.file_ops = FileOperations()
        self.path_validator = PathValidator()
        self.error_handler = ErrorHandler()
    
    def execute(self, input_file: Optional[str], output: str, no_preview: bool,
                watch: bool, config: Optional[str], show_test_cases: bool,
                template_name: Optional[str], include_source: bool) -> Path:
        """
        Execute convert command
        
        Args:
            input_file: Input file path
            output: Output directory
            no_preview: Skip browser preview
            watch: Enable watch mode
            config: Config file path
            show_test_cases: Show test cases
            template_name: Template name to use
            include_source: Include source toggle
        
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
            
            # Load configuration
            config_obj = load_config(config)
            if config:
                config_obj.validate_config()
            
            ui.processing_start("読み込み中", str(input_path))
            
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
                    template_name, include_source
                )
            
            return output_file
            
        except FileNotFoundError:
            self.error_handler.handle_file_not_found(input_file or "")
            sys.exit(1)
        except UnicodeDecodeError:
            self.error_handler.handle_encoding_error(input_file or "")
            sys.exit(1)
        except PermissionError as e:
            self.error_handler.handle_permission_error(str(e))
            sys.exit(1)
        except Exception as e:
            self.error_handler.handle_unexpected_error(str(e))
            sys.exit(1)
    
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
        with Progress() as progress:
            file_size = len(text)
            task = progress.add_task("[cyan]テキストを解析中", total=100)
            
            start_time = time.time()
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
        with Progress() as progress:
            task = progress.add_task("[yellow]HTMLを生成中", total=100)
            
            start_time = time.time()
            if source_text:
                html = render(ast, config, template=template, title=title,
                            source_text=source_text, source_filename=source_filename)
            else:
                html = render(ast, config, template=template, title=title)
            elapsed = time.time() - start_time
            
            if elapsed < 0.5:
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
        
        # Show statistics
        stats = {
            'total_nodes': len(ast),
            'file_size': len(text)
        }
        ui.statistics(stats)
    
    def _handle_watch_mode(self, input_file: str, output: str, config_obj,
                          show_test_cases: bool, template_name: Optional[str],
                          include_source: bool) -> None:
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


def create_convert_command():
    """Create the convert click command"""
    
    @click.command()
    @click.argument("input_file", type=click.Path(exists=True), required=False)
    @click.option("-o", "--output", default="dist", help="出力ディレクトリ")
    @click.option("--no-preview", is_flag=True, help="HTML生成後にブラウザを開かない")
    @click.option("--watch", is_flag=True, help="ファイルの変更を監視して自動再生成")
    @click.option("--config", type=click.Path(exists=True), help="設定ファイルのパス")
    @click.option("--show-test-cases", is_flag=True, help="テストケース名を表示（テスト用ファイル変換時）")
    @click.option("--with-source-toggle", is_flag=True, help="記法と結果を切り替えるトグル機能付きで出力")
    @click.option("--experimental", type=str, help="実験的機能を有効化 (例: scroll-sync)")
    def convert(input_file, output, no_preview, watch, config, show_test_cases, 
                with_source_toggle, experimental):
        """テキストファイルをHTMLに変換します"""
        
        # Confirm source toggle feature if not specified
        use_source_toggle = with_source_toggle
        if not with_source_toggle and input_file:
            use_source_toggle = ui.confirm_source_toggle()
        
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
            input_file, output, no_preview, watch, config,
            show_test_cases, template_name, use_source_toggle
        )
    
    return convert