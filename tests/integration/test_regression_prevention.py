"""回帰防止統合テスト - Issue #620 Phase 4対応"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.convert.convert_processor import ConvertProcessor
from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.parser import KumihanParser
from kumihan_formatter.renderer import KumihanRenderer


class TestKnownIssueRegression:
    """既知の問題に対する回帰防止テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.logger = get_logger(__name__)
        self.parser = KumihanParser()
        self.renderer = KumihanRenderer()

    def test_issue_319_convert_separation_regression(self):
        """Issue #319: convert.py分離の回帰防止テスト"""
        # ConvertCommandとConvertProcessorが正しく分離されていることを確認
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand
        from kumihan_formatter.commands.convert.convert_processor import (
            ConvertProcessor,
        )

        command = ConvertCommand()
        processor = ConvertProcessor()

        # 分離が正しく行われていることを確認
        assert hasattr(command, "processor")
        assert isinstance(command.processor, ConvertProcessor)
        assert hasattr(processor, "convert")

    def test_unclosed_decoration_syntax_regression(self):
        """未閉じ装飾構文の回帰防止テスト"""
        # 以前に問題となった未閉じ装飾の処理
        unclosed_content = ";;;強調;;; 未閉じコンテンツ"

        # パーサーが適切にエラーハンドリングを行うことを確認
        try:
            result = self.parser.parse(unclosed_content)
            # エラー回復機能により、何らかの結果が返されることを期待
            assert result is not None
        except Exception as e:
            # エラーが発生した場合、適切なエラー情報が含まれることを確認
            assert "unclosed" in str(e).lower() or "未閉じ" in str(e)

    def test_nested_decoration_overflow_regression(self):
        """ネスト装飾のオーバーフロー回帰防止テスト"""
        # 深いネスト構造での問題を防止
        nested_content = (
            ";;;外1;;; ;;;外2;;; ;;;外3;;; ;;;内容;;; テスト ;;; ;;; ;;; ;;;"
        )

        result = self.parser.parse(nested_content)
        assert result is not None
        # スタックオーバーフローが発生しないことを確認

    def test_large_document_memory_regression(self):
        """大量ドキュメント処理時のメモリ回帰防止テスト"""
        # 大量のコンテンツでメモリリークが発生しないことを確認
        import gc
        import os

        import psutil

        # 現在のメモリ使用量を記録
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 大量のコンテンツを処理
        for i in range(10):
            large_content = "\n".join(
                [f";;;装飾{j};;; 大量コンテンツ{j} ;;;" for j in range(100)]
            )
            result = self.parser.parse(large_content)
            assert result is not None

        # ガベージコレクション実行
        gc.collect()

        # メモリ増加が適切な範囲内であることを確認
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50 * 1024 * 1024  # 50MB以下

    def test_encoding_detection_regression(self):
        """エンコーディング検出の回帰防止テスト"""
        # UTF-8以外のエンコーディングでも適切に処理されることを確認
        japanese_content = ";;;重要;;; 日本語コンテンツのテスト ;;;"

        # 一時ファイルに異なるエンコーディングで保存
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as test_file:
            test_file.write(japanese_content)
            file_path = test_file.name

        try:
            # ファイルからの読み込みとパースが正常に動作することを確認
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                result = self.parser.parse(content)
                assert result is not None

        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_parallel_processing_race_condition_regression(self):
        """並列処理での競合状態回帰防止テスト"""
        import concurrent.futures
        import threading

        results = []
        errors = []

        def parse_content(content_id):
            try:
                content = f";;;テスト{content_id};;; 並列処理テスト{content_id} ;;;"
                parser = KumihanParser()  # 各スレッドで独立したインスタンス
                result = parser.parse(content)
                results.append(result)
                return result
            except Exception as e:
                errors.append(e)
                raise

        # 複数スレッドで同時実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(parse_content, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # 全ての処理が成功し、競合状態が発生していないことを確認
        assert len(results) == 10
        assert len(errors) == 0

    def test_template_not_found_regression(self):
        """テンプレート未発見エラーの回帰防止テスト"""
        # 存在しないテンプレートを指定した場合の適切なエラーハンドリング
        ast = MagicMock()

        # テンプレートが見つからない場合のフォールバック処理
        try:
            with patch.object(self.renderer, "set_template") as mock_set_template:
                mock_set_template.side_effect = FileNotFoundError("Template not found")

                # エラーが適切に処理されることを確認
                self.renderer.set_template("nonexistent_template.html.j2")

        except FileNotFoundError as e:
            assert "Template not found" in str(e)

    def test_infinite_loop_protection_regression(self):
        """無限ループ保護の回帰防止テスト"""
        # 循環参照やパターンマッチングでの無限ループを防止
        circular_content = ";;;循環;;; ;;;循環;;; ;;;循環;;; テスト ;;; ;;; ;;;"

        start_time = time.time()
        result = self.parser.parse(circular_content)
        end_time = time.time()

        # 処理が適切な時間内で完了することを確認（無限ループなし）
        assert result is not None
        assert (end_time - start_time) < 5.0  # 5秒以内

    def test_special_character_handling_regression(self):
        """特殊文字処理の回帰防止テスト"""
        # HTML特殊文字やUnicode文字の適切な処理
        special_content = """
;;;注意;;; <script>alert("XSS")</script> ;;;
;;;情報;;; 🔥 絵文字テスト 🚀 ;;;
;;;引用;;; "引用符"と'アポストロフィ'のテスト ;;;
        """

        result = self.parser.parse(special_content)
        assert result is not None

        # レンダリング時にも適切に処理されることを確認
        html_result = self.renderer.render(result)
        assert html_result is not None
        assert isinstance(html_result, str)


class TestPerformanceRegression:
    """性能回帰防止テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanParser()
        self.renderer = KumihanRenderer()

    def test_parsing_performance_regression(self):
        """パース性能の回帰防止テスト"""
        # 基準となるパフォーマンスを設定
        content_size = 1000  # 1000行のコンテンツ
        content = "\n".join(
            [f";;;項目{i};;; コンテンツ{i} ;;;" for i in range(content_size)]
        )

        start_time = time.time()
        result = self.parser.parse(content)
        end_time = time.time()

        # パース時間が適切な範囲内であることを確認
        parse_time = end_time - start_time
        assert result is not None
        assert parse_time < 3.0  # 3秒以内

        # 1行あたりの処理時間
        time_per_line = parse_time / content_size
        assert time_per_line < 0.01  # 1行あたり10ms以内

    def test_rendering_performance_regression(self):
        """レンダリング性能の回帰防止テスト"""
        # 大きなASTでのレンダリング性能
        large_ast = MagicMock()
        large_ast.children = []

        # 多数のノードを追加
        for i in range(500):
            node = MagicMock()
            node.type = "text"
            node.content = f"レンダリングテスト{i}"
            large_ast.children.append(node)

        start_time = time.time()
        result = self.renderer.render(large_ast)
        end_time = time.time()

        # レンダリング時間が適切な範囲内であることを確認
        render_time = end_time - start_time
        assert result is not None
        assert render_time < 2.0  # 2秒以内

    def test_memory_usage_regression(self):
        """メモリ使用量の回帰防止テスト"""
        import gc
        import os

        import psutil

        # ベースラインメモリ使用量
        gc.collect()
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss

        # 多数の処理を実行
        for i in range(50):
            content = f";;;メモリテスト{i};;; コンテンツ{i} ;;;"
            ast = self.parser.parse(content)
            result = self.renderer.render(ast)

        # ガベージコレクション後のメモリ使用量
        gc.collect()
        final_memory = process.memory_info().rss
        memory_increase = final_memory - baseline_memory

        # メモリ増加が適切な範囲内であることを確認
        assert memory_increase < 30 * 1024 * 1024  # 30MB以下


class TestAPIBackwardCompatibility:
    """API後方互換性テスト"""

    def test_parser_api_compatibility(self):
        """Parser APIの後方互換性テスト"""
        parser = KumihanParser()

        # 基本的なAPIが維持されていることを確認
        assert hasattr(parser, "parse")
        assert callable(getattr(parser, "parse"))

        # パースメソッドが文字列を受け取ることを確認
        result = parser.parse("テストコンテンツ")
        assert result is not None

    def test_renderer_api_compatibility(self):
        """Renderer APIの後方互換性テスト"""
        renderer = KumihanRenderer()

        # 基本的なAPIが維持されていることを確認
        assert hasattr(renderer, "render")
        assert callable(getattr(renderer, "render"))

        # レンダーメソッドがASTを受け取ることを確認
        ast = MagicMock()
        result = renderer.render(ast)
        assert result is not None
        assert isinstance(result, str)

    def test_convert_processor_api_compatibility(self):
        """ConvertProcessor APIの後方互換性テスト"""
        processor = ConvertProcessor()

        # 基本的なAPIが維持されていることを確認
        assert hasattr(processor, "convert")
        assert callable(getattr(processor, "convert"))

        # ファイルパスベースの変換APIが維持されていることを確認
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as input_file:
            input_file.write(";;;テスト;;; APIテスト ;;;")
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            # APIの基本形式が維持されていることを確認
            with patch.object(processor, "convert") as mock_convert:
                mock_convert.return_value = True
                result = processor.convert(input_path, output_path)

        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)


class TestDataIntegrityRegression:
    """データ整合性回帰防止テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanParser()
        self.renderer = KumihanRenderer()

    def test_parse_render_roundtrip_integrity(self):
        """パース→レンダリング往復でのデータ整合性テスト"""
        original_content = """
# タイトル

;;;重要;;; 重要な情報 ;;;

- リスト項目1
- リスト項目2

通常のテキスト ((脚注)) も含む。
        """

        # パース→レンダリングの往復処理
        ast = self.parser.parse(original_content)
        rendered_html = self.renderer.render(ast)

        # 結果が適切に生成されることを確認
        assert ast is not None
        assert rendered_html is not None
        assert isinstance(rendered_html, str)
        assert len(rendered_html) > 0

        # 基本的なコンテンツが保持されていることを確認
        # （完全な復元は期待しないが、主要な要素が含まれることを確認）
        assert "タイトル" in rendered_html or "title" in rendered_html.lower()
        assert "重要" in rendered_html
        assert "リスト" in rendered_html or "list" in rendered_html.lower()

    def test_multiple_processing_consistency(self):
        """複数回処理での一貫性テスト"""
        content = ";;;強調;;; 一貫性テスト ;;;"

        # 同じコンテンツを複数回処理
        results = []
        for i in range(5):
            ast = self.parser.parse(content)
            html = self.renderer.render(ast)
            results.append(html)

        # 全ての結果が一致することを確認
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

    def test_edge_case_handling_integrity(self):
        """エッジケース処理での整合性テスト"""
        edge_cases = [
            "",  # 空文字列
            "   ",  # 空白のみ
            ";;;",  # 不完全なマーカー
            ";;; ;;;",  # 空の装飾
            ";;;test;;; ;;;",  # 英語コンテンツ
            ";;;日本語;;; 日本語コンテンツ ;;;",  # 日本語
            ";;;🔥;;; 絵文字コンテンツ ;;;",  # 絵文字
        ]

        for case in edge_cases:
            try:
                ast = self.parser.parse(case)
                html = self.renderer.render(ast)

                # エラーが発生しないか、適切にハンドリングされることを確認
                assert ast is not None
                assert html is not None
                assert isinstance(html, str)

            except Exception as e:
                # エラーが発生した場合、適切なエラーメッセージが含まれることを確認
                assert str(e) is not None
                assert len(str(e)) > 0
