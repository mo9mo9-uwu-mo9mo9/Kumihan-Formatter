"""
変換コマンド - 処理機能

HTML変換・パース・レンダリングの責任を担当
Issue #319対応 - convert.py から分離
"""

import re
import time
from pathlib import Path
from typing import Any, Optional

from rich.progress import Progress

from ...core.file_ops import FileOperations
from ...core.utilities.logger import get_logger
from ...parser import parse
from ...renderer import render
from ...ui.console_ui import get_console_ui


class ConvertProcessor:
    """変換処理クラス

    責任: ファイルの解析・変換・HTML生成
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.file_ops = FileOperations(ui=get_console_ui())  # type: ignore
        self.logger.debug("ConvertProcessor initialized")

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
        text = self.file_ops.read_text_file(input_path)
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
        self.file_ops.write_text_file(output_file, html)

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

    def _parse_with_progress(self, text: str, config, input_path: Path) -> Any:  # type: ignore
        """プログレス表示付きでパース処理を実行"""
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        self.logger.debug(f"Parsing file of size: {size_mb:.2f} MB")

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
                    f"[yellow]大規模データを変換中 ({node_count:, }要素)", total=100
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
        input_size_info = self.file_ops.get_file_size_info(input_path)
        output_size_info = self.file_ops.get_file_size_info(output_file)

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
                f"Detailed stats: input={stats['input_size_mb']:.2f}MB, output={stats['output_size_mb']:.2f}MB, nodes={stats['node_count']}"
            )
            get_console_ui().show_detailed_stats(stats)  # type: ignore
