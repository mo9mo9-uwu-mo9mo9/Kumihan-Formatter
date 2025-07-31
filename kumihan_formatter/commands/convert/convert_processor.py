"""
変換コマンド - 処理機能

HTML変換・パース・レンダリングの責任を担当
Issue #319対応 - convert.py から分離
"""

import re
import time
from pathlib import Path
from typing import Any

from rich.progress import Progress

from ...core.file_io_handler import FileIOHandler
from ...core.file_ops import FileOperations
from ...core.utilities.logger import get_logger
from ...parser import parse, StreamingParser
from ...renderer import render
from ...ui.console_ui import get_console_ui


class ConvertProcessor:
    """変換処理クラス

    責任: ファイルの解析・変換・HTML生成
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.file_ops = FileOperations(ui=get_console_ui())
        self.logger.debug("ConvertProcessor initialized")

    def validate_files(self, input_file: str, output_file: str) -> None:
        """ファイルバリデーション

        Args:
            input_file: 入力ファイルパス
            output_file: 出力ファイルパス

        Raises:
            FileNotFoundError: 入力ファイルが存在しない場合
            ValueError: ファイルパスが無効な場合
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if not input_path.is_file():
            raise ValueError(f"Input path is not a file: {input_file}")

        # 出力ディレクトリの存在確認（必要に応じて作成）
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"File validation passed: {input_file} -> {output_file}")

    def convert_file(  # type: ignore
        self,
        input_path: Path,
        output_dir: str,
        config_obj=None,
        show_test_cases: bool = False,
        template: str | None = None,
        include_source: bool = False,
    ) -> Path:
        """ファイルを変換してHTMLを生成"""
        self.logger.info(f"Starting file conversion: {input_path} -> {output_dir}")
        start_time = time.time()

        # ファイル読み込み
        get_console_ui().processing_start("読み込み中", str(input_path))
        text = FileIOHandler.read_text_file(input_path)
        self.logger.debug(f"File read successfully: {len(text)} characters")

        # テストケース表示
        if show_test_cases:
            self.logger.debug("Showing test cases")
            self._show_test_cases(text)

        # パース処理
        get_console_ui().processing_start("解析中", "テキスト構造を解析しています...")
        self.logger.info("Starting parse phase")
        ast = self._parse_with_progress(text, config_obj, input_path)
        self.logger.debug(f"Parse completed: {len(ast) if ast else 0} nodes")

        # 出力ファイルパスの決定
        output_file = self._determine_output_path(input_path, output_dir)
        self.logger.debug(f"Output path determined: {output_file}")

        # レンダリング処理
        get_console_ui().processing_start("変換中", "HTMLを生成しています...")
        self.logger.info("Starting render phase")

        # ソース表示用の引数を準備
        source_args = {}
        if include_source:
            source_args = {"source_text": text, "source_filename": input_path.name}
            self.logger.debug("Source display enabled")

        html = self._render_with_progress(
            ast, config_obj, template, title=input_path.stem, **source_args
        )
        self.logger.debug(f"Render completed: {len(html)} characters")

        # ファイル保存
        get_console_ui().processing_start(
            "保存中", f"ファイルを保存しています: {output_file.name}"
        )
        self.logger.info(f"Saving output file: {output_file}")
        FileIOHandler.write_text_file(output_file, html)

        # 統計情報表示
        self._show_conversion_stats(ast, text, output_file, input_path)

        duration = time.time() - start_time
        self.logger.info(f"Conversion completed in {duration:.2f} seconds")

        return output_file

    def _determine_output_path(self, input_path: Path, output_dir: str) -> Path:
        """出力ファイルパスを決定"""
        self.logger.debug(f"Determining output path for: {input_path}")
        output_path = Path(output_dir)

        # 出力ディレクトリが存在しない場合は作成
        if not output_path.exists():
            self.logger.info(f"Creating output directory: {output_path}")
            output_path.mkdir(parents=True, exist_ok=True)

        # HTMLファイル名を生成
        html_filename = f"{input_path.stem}.html"
        return output_path / html_filename

    def _parse_with_progress(self, text: str, config: Any, input_path: Path) -> Any:
        """プログレス表示付きでパース処理を実行（ストリーミング対応）"""
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        line_count = len(text.split('\n'))
        self.logger.debug(f"Parsing file: {size_mb:.2f} MB, {line_count} lines")

        # ストリーミング処理の判定閾値
        use_streaming = size_mb > 1.0 or line_count > 200
        
        if use_streaming:
            return self._parse_with_streaming_progress(text, config, input_path, size_mb, line_count)
        else:
            return self._parse_with_traditional_progress(text, config, size_mb)
    
    def _parse_with_streaming_progress(self, text: str, config: Any, input_path: Path, size_mb: float, line_count: int) -> Any:
        """ストリーミングパーサーを使用した解析（リアルタイムプログレス）"""
        from ...parser import StreamingParser
        
        self.logger.info(f"Using streaming parser for large file: {size_mb:.1f}MB, {line_count} lines")
        
        parser = StreamingParser(config=config)
        nodes = []
        
        with Progress() as progress:
            # 詳細なプログレス表示
            task = progress.add_task(
                f"[cyan]大容量ファイル解析 ({size_mb:.1f}MB, {line_count:,}行)", 
                total=100
            )
            
            start_time = time.time()
            
            def progress_callback(progress_info: dict) -> None:
                """ストリーミング解析のプログレス更新"""
                current = progress_info['current_line']
                total = progress_info['total_lines']
                percent = progress_info['progress_percent']
                eta = progress_info['eta_seconds']
                
                # プログレスバー更新
                progress.update(task, completed=percent)
                
                # 詳細情報をログ出力
                if current % 100 == 0:  # 100行ごとに詳細ログ
                    self.logger.debug(f"Progress: {current}/{total} lines ({percent:.1f}%), ETA: {eta}s")
            
            try:
                # ストリーミング解析実行
                for node in parser.parse_streaming_from_text(text, progress_callback):
                    nodes.append(node)
                    
                    # キャンセルチェック（将来の拡張用）
                    if hasattr(parser, '_cancelled') and parser._cancelled:
                        self.logger.info("Parse cancelled by user")
                        break
                
                # 完了処理
                progress.update(task, completed=100)
                
                elapsed = time.time() - start_time
                self.logger.info(f"Streaming parse completed: {len(nodes)} nodes in {elapsed:.2f}s")
                
                # パフォーマンスサマリー取得
                if hasattr(parser, 'performance_monitor'):
                    performance_summary = parser.performance_monitor.get_performance_summary()
                    self.logger.info(
                        f"Performance Summary: "
                        f"{performance_summary['items_per_second']:.0f} items/sec, "
                        f"peak memory: {performance_summary['peak_memory_mb']:.1f}MB, "
                        f"avg CPU: {performance_summary['avg_cpu_percent']:.1f}%"
                    )
                
                # エラーサマリー
                errors = parser.get_errors()
                if errors:
                    self.logger.warning(f"Parse completed with {len(errors)} errors")
                    
            except Exception as e:
                self.logger.error(f"Streaming parse failed: {e}")
                # フォールバック: 従来の解析方式
                self.logger.info("Falling back to traditional parser")
                from ...parser import parse
                nodes = parse(text, config)
        
        return nodes
    
    def _parse_with_traditional_progress(self, text: str, config: Any, size_mb: float) -> Any:
        """従来のパーサーを使用した解析（既存の動作を維持）"""
        from ...parser import parse
        
        with Progress() as progress:
            if size_mb > 10:  # 10MB以上
                task = progress.add_task(
                    f"[cyan]大規模ファイルを解析中 ({size_mb:.1f}MB)", total=100
                )
            else:
                task = progress.add_task("[cyan]テキストを解析中", total=100)

            start_time = time.time()

            # 大きなファイルの場合は分割表示をシミュレート
            if size_mb > 50:  # 50MB以上は段階的表示
                for i in range(10):
                    progress.update(task, completed=i * 10)
                    time.sleep(0.1)

                ast = parse(text, config)
                progress.update(task, completed=100)
            else:
                ast = parse(text, config)
                elapsed = time.time() - start_time
                self.logger.debug(f"Parse completed in {elapsed:.2f} seconds")

                if elapsed < 0.5:
                    for i in range(0, 101, 20):
                        progress.update(task, completed=i)
                        time.sleep(0.05)
                progress.update(task, completed=100)

        return ast

    def _render_with_progress(  # type: ignore
        self,
        ast: Any,
        config,
        template: str | None,
        title: str,
        source_text: str | None = None,
        source_filename: str | None = None,
    ) -> str:
        """プログレス表示付きでレンダリング処理を実行"""
        node_count = len(ast) if ast else 0
        self.logger.debug(f"Rendering {node_count} nodes")

        with Progress() as progress:
            if node_count > 1000:  # 1000ノード以上
                task = progress.add_task(
                    f"[yellow]大規模データを変換中 ({node_count:,}要素)", total=100
                )
            else:
                task = progress.add_task("[yellow]HTMLを生成中", total=100)

            start_time = time.time()

            # 大きなASTの場合は段階的表示
            if node_count > 5000:  # 5000ノード以上は段階的表示
                for i in range(0, 101, 10):
                    progress.update(task, completed=i)
                    time.sleep(0.05)

            if source_text:
                html = render(
                    ast,
                    config,
                    template=template,
                    title=title,
                    source_text=source_text,
                    source_filename=source_filename,
                )
            else:
                html = render(ast, config, template=template, title=title)

            elapsed = time.time() - start_time
            self.logger.debug(f"Render completed in {elapsed:.2f} seconds")

            if elapsed < 0.5 and node_count <= 5000:
                for i in range(0, 101, 25):
                    progress.update(task, completed=i)
                    time.sleep(0.04)
            progress.update(task, completed=100)

        return html

    def _show_test_cases(self, text: str) -> None:
        """テキストからテストケースを抽出して表示"""
        test_case_pattern = r"# \[TEST-(\d+)\] ([^:]+): (.+)"
        test_cases = re.findall(test_case_pattern, text)
        self.logger.debug(f"Found {len(test_cases)} test cases")

        if test_cases:
            get_console_ui().test_cases_detected(len(test_cases), test_cases)

    def _show_conversion_stats(
        self, ast: Any, text: str, output_file: Path, input_path: Path
    ) -> None:
        """変換統計情報を表示"""
        # エラー統計
        error_count = sum(1 for node in ast if getattr(node, "type", None) == "error")
        self.logger.info(f"Conversion stats: {error_count} errors found")
        if error_count > 0:
            # サンプルファイルかどうかをチェック
            is_sample = input_path.name in ["02-basic.txt", "03-comprehensive.txt"]
            get_console_ui().validation_warning(error_count, is_sample)

        get_console_ui().conversion_complete(str(output_file))

        # 大きなファイルの場合は詳細統計を表示
        from ...core.file_path_utilities import FilePathUtilities

        input_size_info = FilePathUtilities.get_file_size_info(input_path)
        output_size_info = FilePathUtilities.get_file_size_info(output_file)

        stats = {
            "input_size_mb": input_size_info["size_mb"],
            "output_size_mb": output_size_info["size_mb"],
            "line_count": len(text.split("\n")),
            "node_count": len(ast) if ast else 0,
            "error_count": error_count,
        }

        # 大きなファイルの場合のみ詳細統計を表示
        if stats["input_size_mb"] > 1.0 or stats["node_count"] > 500:
            self.logger.info(
                f"Detailed stats: input={stats['input_size_mb']:.2f}MB, "
                f"output={stats['output_size_mb']:.2f}MB, "
                f"nodes={stats['node_count']}"
            )
            get_console_ui().show_detailed_stats(stats)  # type: ignore
