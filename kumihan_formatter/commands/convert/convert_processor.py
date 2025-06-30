"""
変換コマンド - 処理機能

HTML変換・パース・レンダリングの責任を担当
Issue #319対応 - convert.py から分離
"""

import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

from rich.progress import Progress

from ...core.file_ops import FileOperations
from ...parser import parse
from ...renderer import render
from ...ui.console_ui import ui


class ConvertProcessor:
    """変換処理クラス

    責任: ファイルの解析・変換・HTML生成
    """

    def __init__(self):
        self.file_ops = FileOperations(ui=ui)

    def convert_file(
        self,
        input_path: Path,
        output_dir: str,
        config_obj=None,
        show_test_cases: bool = False,
        template: Optional[str] = None,
        include_source: bool = False,
    ) -> Path:
        """ファイルを変換してHTMLを生成"""

        # ファイル読み込み
        ui.processing_start("読み込み中", str(input_path))
        text = self.file_ops.read_text_file(input_path)

        # テストケース表示
        if show_test_cases:
            self._show_test_cases(text)

        # パース処理
        ui.processing_start("解析中", "テキスト構造を解析しています...")
        ast = self._parse_with_progress(text, config_obj, input_path)

        # 出力ファイルパスの決定
        output_file = self._determine_output_path(input_path, output_dir)

        # レンダリング処理
        ui.processing_start("変換中", "HTMLを生成しています...")

        # ソース表示用の引数を準備
        source_args = {}
        if include_source:
            source_args = {"source_text": text, "source_filename": input_path.name}

        html = self._render_with_progress(
            ast, config_obj, template, title=input_path.stem, **source_args
        )

        # ファイル保存
        ui.processing_start("保存中", f"ファイルを保存しています: {output_file.name}")
        self.file_ops.write_text_file(output_file, html)

        # 統計情報表示
        self._show_conversion_stats(ast, text, output_file, input_path)

        return output_file

    def _determine_output_path(self, input_path: Path, output_dir: str) -> Path:
        """出力ファイルパスを決定"""
        output_path = Path(output_dir)

        # 出力ディレクトリが存在しない場合は作成
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        # HTMLファイル名を生成
        html_filename = f"{input_path.stem}.html"
        return output_path / html_filename

    def _parse_with_progress(self, text: str, config, input_path: Path) -> Any:
        """プログレス表示付きでパース処理を実行"""
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)

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

                if elapsed < 0.5:
                    for i in range(0, 101, 20):
                        progress.update(task, completed=i)
                        time.sleep(0.05)
                progress.update(task, completed=100)

        return ast

    def _render_with_progress(
        self,
        ast: Any,
        config,
        template: Optional[str],
        title: str,
        source_text: Optional[str] = None,
        source_filename: Optional[str] = None,
    ) -> str:
        """プログレス表示付きでレンダリング処理を実行"""
        node_count = len(ast) if ast else 0

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

        if test_cases:
            ui.test_cases_detected(len(test_cases), test_cases)

    def _show_conversion_stats(
        self, ast: Any, text: str, output_file: Path, input_path: Path
    ) -> None:
        """変換統計情報を表示"""
        # エラー統計
        error_count = sum(1 for node in ast if getattr(node, "type", None) == "error")
        if error_count > 0:
            # サンプルファイルかどうかをチェック
            is_sample = input_path.name in ["02-basic.txt", "03-comprehensive.txt"]
            ui.validation_warning(error_count, is_sample)

        ui.conversion_complete(str(output_file))

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
            ui.show_detailed_stats(stats)
