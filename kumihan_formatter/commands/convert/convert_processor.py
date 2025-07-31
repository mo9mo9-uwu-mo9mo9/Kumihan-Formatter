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
from ...parser import StreamingParser, parse, parse_with_error_config
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
        progress_level: str = "detailed",
        show_progress_tooltip: bool = True,
        enable_cancellation: bool = True,
        progress_style: str = "bar",
        progress_log: str | None = None,
        continue_on_error: bool = False,
        graceful_errors: bool = False,
        # Phase3: エラー設定管理
        error_config_manager: Any = None,
    ) -> Path:
        """ファイルを変換してHTMLを生成（Issue #695対応: 高度プログレス管理）"""
        from ...core.utilities.progress_manager import ProgressContextManager

        self.logger.info(f"Starting file conversion: {input_path} -> {output_dir}")

        # 未実装機能の警告
        if progress_style != "bar":
            self.logger.warning(
                f"Progress style '{progress_style}' is not implemented yet. Using default 'bar' style."
            )

        # プログレスレベルをenumに変換
        verbosity_map = {
            "silent": ProgressContextManager.VerbosityLevel.SILENT,
            "minimal": ProgressContextManager.VerbosityLevel.MINIMAL,
            "detailed": ProgressContextManager.VerbosityLevel.DETAILED,
            "verbose": ProgressContextManager.VerbosityLevel.VERBOSE,
        }
        verbosity = verbosity_map.get(
            progress_level.lower(), ProgressContextManager.VerbosityLevel.DETAILED
        )

        # 推定処理ステップ数を計算
        text = FileIOHandler.read_text_file(input_path)
        estimated_steps = self._estimate_processing_steps(
            text, show_test_cases, include_source
        )

        # プログレスコンテキストマネージャで全体処理を管理
        with ProgressContextManager(
            task_name=f"変換処理: {input_path.name}",
            total_items=estimated_steps,
            verbosity=verbosity,
            show_tooltips=show_progress_tooltip,
            enable_cancellation=enable_cancellation,
            progress_style=progress_style,
            progress_log=progress_log,
        ) as progress:

            current_step = 0

            # ステップ1: ファイル読み込み
            progress.update(current_step, "初期化", "ファイル読み込み中...")
            if progress.is_cancelled():
                self.logger.info("Conversion cancelled during file reading")
                raise KeyboardInterrupt("ユーザーによりキャンセルされました")

            self.logger.debug(f"File read successfully: {len(text)} characters")
            current_step += 1

            # ステップ2: テストケース表示（オプション）
            if show_test_cases:
                progress.update(current_step, "テストケース", "テストケースを表示中...")
                if progress.is_cancelled():
                    raise KeyboardInterrupt("ユーザーによりキャンセルされました")

                self.logger.debug("Showing test cases")
                self._show_test_cases(text)
                current_step += 1

            # ステップ3: パース処理
            progress.update(current_step, "解析", "テキスト構造を解析中...")
            if progress.is_cancelled():
                raise KeyboardInterrupt("ユーザーによりキャンセルされました")

            self.logger.info("Starting parse phase")
            ast, parser = self._parse_with_enhanced_progress(
                text,
                config_obj,
                input_path,
                progress,
                continue_on_error,
                graceful_errors,
                error_config_manager,
            )
            if not ast:
                progress.add_error("パース処理が失敗しました")
                raise ValueError("パース処理に失敗しました")

            self.logger.debug(f"Parse completed: {len(ast)} nodes")
            current_step += int(estimated_steps * 0.4)  # パース処理は全体の約40%

            # ステップ4: 出力パス決定
            progress.update(current_step, "準備", "出力ファイルパスを決定中...")
            output_file = self._determine_output_path(input_path, output_dir)
            self.logger.debug(f"Output path determined: {output_file}")
            current_step += 1

            # ステップ5: レンダリング処理
            progress.update(current_step, "変換", "HTML生成中...")
            if progress.is_cancelled():
                raise KeyboardInterrupt("ユーザーによりキャンセルされました")

            self.logger.info("Starting render phase")

            # ソース表示用の引数を準備
            source_args = {}
            if include_source:
                source_args = {"source_text": text, "source_filename": input_path.name}
                self.logger.debug("Source display enabled")
                current_step += 1
                progress.update(current_step, "変換", "ソース表示を準備中...")

            # Issue #700: パーサーからgraceful errorsを取得
            parser_errors = []
            if (
                graceful_errors
                and parser
                and hasattr(parser, "get_graceful_errors")
            ):
                parser_errors = parser.get_graceful_errors()
                self.logger.info(
                    f"Retrieved {len(parser_errors)} graceful errors from parser"
                )

            html = self._render_with_enhanced_progress(
                ast,
                config_obj,
                template,
                input_path.stem,
                progress,
                graceful_errors=graceful_errors,
                parser_errors=parser_errors,
                **source_args,
            )
            self.logger.debug(f"Render completed: {len(html)} characters")
            current_step += int(estimated_steps * 0.4)  # レンダリングも約40%

            # ステップ6: ファイル保存
            progress.update(current_step, "保存", f"ファイル保存中: {output_file.name}")
            if progress.is_cancelled():
                raise KeyboardInterrupt("ユーザーによりキャンセルされました")

            self.logger.info(f"Saving output file: {output_file}")
            FileIOHandler.write_text_file(output_file, html)
            current_step += 1

            # ステップ7: 統計情報表示
            progress.update(current_step, "完了", "統計情報を生成中...")
            self._show_conversion_stats(ast, text, output_file, input_path)

            # 最終ステップ
            progress.update(estimated_steps, "完了", "変換処理が完了しました")

            self.logger.info("Conversion completed successfully")
            return output_file

    def _estimate_processing_steps(
        self, text: str, show_test_cases: bool, include_source: bool
    ) -> int:
        """処理ステップ数を推定（Issue #695対応）"""
        base_steps = 5  # 読み込み、パース、出力パス決定、レンダリング、保存

        # テキストサイズに基づく追加ステップ
        text_size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        if text_size_mb > 1.0:
            base_steps += int(text_size_mb * 10)  # 1MB毎に10ステップ追加

        # オプション機能による追加ステップ
        if show_test_cases:
            base_steps += 2
        if include_source:
            base_steps += 3

        # 行数に基づく追加推定
        line_count = text.count("\n") + 1
        if line_count > 1000:
            base_steps += int(line_count / 100)  # 100行毎に1ステップ

        return max(base_steps, 10)  # 最低10ステップ

    def _parse_with_enhanced_progress(
        self,
        text: str,
        config_obj,
        input_path: Path,
        progress_manager,
        continue_on_error: bool = False,
        graceful_errors: bool = False,
        error_config_manager: Any = None,
    ):
        """プログレス管理付きパース処理（Issue #695対応）"""
        from ...parser import Parser

        # Phase3: エラー設定管理対応
        if error_config_manager:
            effective_graceful_errors = error_config_manager.config.graceful_errors or error_config_manager.config.continue_on_error
        else:
            effective_graceful_errors = graceful_errors
            
        parser = Parser(graceful_errors=effective_graceful_errors)

        # ファイルサイズベースでストリーミング解析を選択
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        line_count = text.count("\n") + 1

        if size_mb > 5.0 or line_count > 10000:  # 大容量ファイル
            self.logger.info(
                f"Large file detected ({size_mb:.1f}MB, {line_count} lines), using streaming parse"
            )

            # ストリーミング解析用プログレスコールバック
            def enhanced_progress_callback(progress_info: dict):
                if progress_manager.is_cancelled():
                    parser.cancel_parsing()
                    return

                current = progress_info["current_line"]
                total = progress_info["total_lines"]
                percent = progress_info["progress_percent"]

                # プログレスマネージャーに反映
                estimated_current = int(
                    (current / total) * progress_manager.total_items * 0.4
                )
                progress_manager.update(
                    estimated_current, "解析", f"行 {current}/{total} ({percent:.1f}%)"
                )

            # ストリーミング解析実行
            nodes = list(
                parser.parse_streaming_from_text(text, enhanced_progress_callback)
            )
            # Issue #700: パーサーオブジェクトも返す
            return (nodes, parser)
        else:
            # 従来の解析方式
            nodes = parser.parse(text)
            # Issue #700: パーサーオブジェクトも返す
            return (nodes, parser)

    def _render_with_enhanced_progress(
        self,
        ast,
        config_obj,
        template: str | None,
        title: str,
        progress_manager,
        graceful_errors: bool = False,
        parser_errors: list = None,
        **source_args,
    ) -> str:
        """プログレス管理付きレンダリング処理（Issue #695対応）"""
        from ...renderer import Renderer

        renderer = Renderer()

        # レンダリング進捗の段階的更新
        node_count = len(ast) if ast else 0
        processed_nodes = 0

        def render_progress_callback():
            nonlocal processed_nodes
            processed_nodes += 1

            if progress_manager.is_cancelled():
                raise KeyboardInterrupt("レンダリングがキャンセルされました")

            if processed_nodes % max(1, node_count // 20) == 0:  # 5%刻みで更新
                percent = (
                    (processed_nodes / node_count) * 100 if node_count > 0 else 100
                )
                base_progress = int(
                    progress_manager.total_items * 0.6
                )  # 60%位置から開始
                current_progress = base_progress + int(
                    (percent / 100) * progress_manager.total_items * 0.3
                )

                progress_manager.update(
                    current_progress,
                    "変換",
                    f"ノード {processed_nodes}/{node_count} ({percent:.1f}%)",
                )

        # レンダリング実行
        try:
            # プログレスコールバックを設定
            if hasattr(renderer, "set_progress_callback"):
                renderer.set_progress_callback(render_progress_callback)

            # Issue #700: graceful error handling対応
            if graceful_errors and parser_errors:
                # HTMLレンダラーにエラー情報を設定
                html_renderer = renderer.html_renderer
                if hasattr(html_renderer, "set_graceful_errors"):
                    html_renderer.set_graceful_errors(parser_errors, embed_in_html=True)
                    self.logger.info(
                        f"Set {len(parser_errors)} graceful errors for HTML embedding"
                    )

            html = renderer.render(ast, template=template, title=title, **source_args)

            return html

        except Exception as e:
            progress_manager.add_error(f"レンダリングエラー: {str(e)}")
            raise

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

    def _parse_with_progress(self, text: str, config: Any, input_path: Path, error_config_manager: Any = None) -> Any:
        """プログレス表示付きでパース処理を実行（ストリーミング対応）"""
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        line_count = len(text.split("\n"))
        self.logger.debug(f"Parsing file: {size_mb:.2f} MB, {line_count} lines")

        # ストリーミング処理の判定閾値
        use_streaming = size_mb > 1.0 or line_count > 200

        if use_streaming:
            return self._parse_with_streaming_progress(
                text, config, input_path, size_mb, line_count, error_config_manager
            )
        else:
            return self._parse_with_traditional_progress(text, config, size_mb, error_config_manager)

    def _parse_with_streaming_progress(
        self, text: str, config: Any, input_path: Path, size_mb: float, line_count: int, error_config_manager: Any = None
    ) -> Any:
        """ストリーミングパーサーを使用した解析（リアルタイムプログレス）"""
        self.logger.info(
            f"Using streaming parser for large file: {size_mb:.1f}MB, {line_count} lines"
        )

        # Phase3: エラー設定管理対応（StreamingParserは将来拡張予定）
        parser = StreamingParser(config=config)
        
        # 現時点ではStreamingParserはgraceful_errorsをサポートしていないため、
        # エラー設定がある場合は警告を出す
        if error_config_manager and (error_config_manager.config.graceful_errors or error_config_manager.config.continue_on_error):
            self.logger.warning("StreamingParser does not yet support graceful error handling. Errors will be handled traditionally.")
        nodes = []

        with Progress() as progress:
            # 詳細なプログレス表示
            task = progress.add_task(
                f"[cyan]大容量ファイル解析 ({size_mb:.1f}MB, {line_count:,}行)",
                total=100,
            )

            start_time = time.time()

            def progress_callback(progress_info: dict) -> None:
                """ストリーミング解析のプログレス更新"""
                current = progress_info["current_line"]
                total = progress_info["total_lines"]
                percent = progress_info["progress_percent"]
                eta = progress_info["eta_seconds"]

                # プログレスバー更新
                progress.update(task, completed=percent)

                # 詳細情報をログ出力
                if current % 100 == 0:  # 100行ごとに詳細ログ
                    self.logger.debug(
                        f"Progress: {current}/{total} lines ({percent:.1f}%), ETA: {eta}s"
                    )

            try:
                # ストリーミング解析実行
                for node in parser.parse_streaming_from_text(text, progress_callback):
                    nodes.append(node)

                    # キャンセルチェック（将来の拡張用）
                    if hasattr(parser, "_cancelled") and parser._cancelled:
                        self.logger.info("Parse cancelled by user")
                        break

                # 完了処理
                progress.update(task, completed=100)

                elapsed = time.time() - start_time
                self.logger.info(
                    f"Streaming parse completed: {len(nodes)} nodes in {elapsed:.2f}s"
                )

                # パフォーマンスサマリー取得
                if hasattr(parser, "performance_monitor"):
                    performance_summary = (
                        parser.performance_monitor.get_performance_summary()
                    )
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
                if error_config_manager:
                    nodes, errors = parse_with_error_config(text, config, error_config_manager)
                    # パーサーにエラーを設定
                    if hasattr(parser, 'graceful_syntax_errors'):
                        parser.graceful_syntax_errors.extend(errors)
                else:
                    nodes = parse(text, config)

        return nodes

    def _parse_with_traditional_progress(
        self, text: str, config: Any, size_mb: float, error_config_manager: Any = None
    ) -> Any:
        """従来のパーサーを使用した解析（既存の動作を維持）"""

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

                if error_config_manager:
                    ast, errors = parse_with_error_config(text, config, error_config_manager)
                else:
                    ast = parse(text, config)
                progress.update(task, completed=100)
            else:
                if error_config_manager:
                    ast, errors = parse_with_error_config(text, config, error_config_manager)
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
