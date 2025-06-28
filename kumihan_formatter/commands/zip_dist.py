"""ZIP distribution command implementation

This module contains the ZIP distribution functionality that was
previously part of the large cli.py file.
"""

import sys
import shutil
import zipfile
import tempfile
import webbrowser
from pathlib import Path
from typing import Optional

import click

from ..ui.console_ui import ui
from ..core.file_ops import FileOperations, PathValidator, ErrorHandler
from ..core.distribution_manager import create_user_distribution


class ZipDistCommand:
    """ZIP distribution command implementation"""
    
    def __init__(self):
        self.file_ops = FileOperations(ui=ui)
        self.path_validator = PathValidator()
        self.error_handler = ErrorHandler()
    
    def execute(self, source_dir: str, output: str, zip_name: str, 
                no_zip: bool, no_preview: bool, convert_docs: bool = True,
                include_developer_docs: bool = False) -> None:
        """
        Execute ZIP distribution command
        
        Args:
            source_dir: Source directory path
            output: Output directory path
            zip_name: ZIP file name (without extension)
            no_zip: If True, create directory only
            no_preview: If True, skip browser preview
            convert_docs: If True, convert markdown docs to user-friendly formats
            include_developer_docs: If True, include developer documentation
        """
        try:
            # Validate paths
            source_path = self.path_validator.validate_source_directory(source_dir)
            output_path = self.path_validator.validate_output_directory(output)
            
            ui.zip_start(str(source_path))
            
            # Load exclusion patterns
            exclude_patterns = self.file_ops.load_distignore_patterns()
            if exclude_patterns:
                ui.zip_exclusion_loaded(len(exclude_patterns))
            
            # Process files
            self._process_files(source_path, output_path, zip_name, 
                              exclude_patterns, no_zip, no_preview, 
                              convert_docs, include_developer_docs)
            
            ui.zip_final_success()
            
        except Exception as e:
            self._handle_error(e)
            sys.exit(1)
    
    def _process_files(self, source_path: Path, output_path: Path, zip_name: str,
                      exclude_patterns: list, no_zip: bool, no_preview: bool,
                      convert_docs: bool, include_developer_docs: bool) -> None:
        """Process and package files"""
        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "distribution"
            temp_path.mkdir(parents=True, exist_ok=True)
            
            if convert_docs:
                # Enhanced document processing with user-friendly conversion
                ui.info("エンドユーザー向け文書変換を実行中...")
                stats = create_user_distribution(
                    source_path, temp_path, 
                    convert_docs=True,
                    include_developer_docs=include_developer_docs,
                    ui=ui
                )
                ui.info(f"文書変換完了: HTML {stats['converted_to_html']}件, TXT {stats['converted_to_txt']}件")
            else:
                # Traditional file copy with exclusions
                self._copy_source_files(source_path, temp_path, exclude_patterns)
            
            # Create final output
            if no_zip:
                self._create_directory_output(temp_path, output_path, zip_name, no_preview)
            else:
                self._create_zip_output(temp_path, output_path, zip_name, no_preview)
    
    def _copy_source_files(self, source_path: Path, temp_path: Path, 
                          exclude_patterns: list) -> None:
        """Copy source files to temporary directory"""
        ui.zip_copying()
        
        copied_count, excluded_count = self.file_ops.copy_directory_with_exclusions(
            source_path, temp_path, exclude_patterns
        )
        
        ui.zip_copy_complete(copied_count, excluded_count)
    
    def _create_directory_output(self, temp_path: Path, output_path: Path, 
                               zip_name: str, no_preview: bool) -> None:
        """Create directory-only output"""
        final_dir = output_path / zip_name
        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.copytree(temp_path, final_dir)
        
        ui.zip_directory_complete(str(final_dir))
        
        if not no_preview:
            self._show_preview(final_dir)
    
    def _create_zip_output(self, temp_path: Path, output_path: Path, 
                          zip_name: str, no_preview: bool) -> None:
        """Create ZIP file output"""
        zip_file_path = output_path / f"{zip_name}.zip"
        
        ui.zip_creating(zip_file_path.name)
        
        # Create ZIP file
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    archive_name = file_path.relative_to(temp_path)
                    zipf.write(file_path, archive_name)
        
        # Show ZIP file information
        zip_size = zip_file_path.stat().st_size
        size_mb = zip_size / (1024 * 1024)
        ui.zip_complete(str(zip_file_path), size_mb)
        
        if not no_preview:
            self._show_zip_preview(zip_file_path, output_path, zip_name)
    
    def _show_preview(self, directory: Path) -> None:
        """Show preview for directory output"""
        preview_file = self.file_ops.find_preview_file(directory)
        
        if preview_file:
            ui.browser_preview()
            webbrowser.open(preview_file.resolve().as_uri())
        else:
            ui.no_preview_files()
    
    def _show_zip_preview(self, zip_file_path: Path, output_path: Path, zip_name: str) -> None:
        """Show preview for ZIP output"""
        preview_dir = output_path / f"{zip_name}_preview"
        if preview_dir.exists():
            shutil.rmtree(preview_dir)
        
        # Extract ZIP for preview
        with zipfile.ZipFile(zip_file_path, 'r') as zipf:
            zipf.extractall(preview_dir)
        
        preview_file = self.file_ops.find_preview_file(preview_dir)
        
        if preview_file:
            ui.browser_preview()
            webbrowser.open(preview_file.resolve().as_uri())
        else:
            ui.no_preview_files()
    
    def _handle_error(self, error: Exception) -> None:
        """Handle command errors"""
        import traceback
        ui.error(f"配布パッケージ作成エラー: {error}")
        ui.dim(traceback.format_exc())


def create_zip_dist_command():
    """Create the zip-dist click command"""
    
    @click.command()
    @click.argument("source_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
    @click.option("-o", "--output", default="zip_distribution", help="ZIP配布用出力ディレクトリ")
    @click.option("--zip-name", default="kumihan-formatter-distribution", help="ZIPファイル名（拡張子なし）")
    @click.option("--no-zip", is_flag=True, help="ZIPファイルを作成せず、ディレクトリのみ作成")
    @click.option("--no-preview", is_flag=True, help="生成後にブラウザでプレビューしない")
    @click.option("--no-convert-docs", is_flag=True, help="文書変換をスキップ（従来の単純コピー方式）")
    @click.option("--include-dev-docs", is_flag=True, help="開発者向け文書も配布に含める")
    def zip_dist(source_dir, output, zip_name, no_zip, no_preview, no_convert_docs, include_dev_docs):
        """配布用ZIPパッケージを作成します
        
        指定されたディレクトリの内容を配布用ZIPファイルとして整理・パッケージ化します。
        開発用ファイルは自動的に除外され、エンドユーザー向けの配布物が作成されます。
        同人作家など技術知識のないユーザー向けに最適化されています。
        
        新機能：
        - Markdownファイルを読みやすいHTML・TXTファイルに自動変換
        - ユーザー向けと開発者向け文書を適切に分離
        - 美しい文書インデックスページを自動生成
        """
        command = ZipDistCommand()
        command.execute(
            source_dir, output, zip_name, no_zip, no_preview,
            convert_docs=not no_convert_docs,
            include_developer_docs=include_dev_docs
        )
    
    return zip_dist