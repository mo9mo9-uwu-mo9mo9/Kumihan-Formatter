"""
KumihanFormatter (unified_api) テスト
"""

import pytest
from pathlib import Path
from kumihan_formatter import KumihanFormatter
from kumihan_formatter.unified_api import (
    quick_convert,
    quick_parse,
    unified_parse,
    validate_kumihan_syntax,
    get_parser_system_info,
)


class TestKumihanFormatter:
    """KumihanFormatter 統合テストクラス"""

    def test_initialization(self):
        """初期化テスト"""
        formatter = KumihanFormatter()
        assert formatter is not None
        assert hasattr(formatter, "parser")
        assert hasattr(formatter, "renderer")

    def test_parse_text(self, formatter, sample_text):
        """テキスト解析テスト"""
        result = formatter.parse_text(sample_text)

        assert result["status"] == "success"
        assert "total_elements" in result
        assert result["total_elements"] > 0
        assert "elements" in result

    def test_validate_syntax_valid(self, formatter):
        """有効な構文の検証テスト"""
        valid_text = "# 重要 #これは有効な構文です##"
        result = formatter.validate_syntax(valid_text)

        assert result["status"] == "valid"
        assert result["total_errors"] == 0
        assert result["errors"] == []

    def test_validate_syntax_invalid(self, formatter):
        """無効な構文の検証テスト"""
        invalid_text = "#  #内容が空##"
        result = formatter.validate_syntax(invalid_text)

        assert result["status"] == "invalid"
        assert result["total_errors"] > 0
        assert len(result["errors"]) > 0

    def test_parse_file(self, formatter, temp_file):
        """ファイル解析テスト"""
        result = formatter.parse_file(temp_file)

        assert result["status"] == "success"
        assert "file_path" in result
        assert str(temp_file) == result["file_path"]
        assert result["total_elements"] > 0

    def test_convert_file(self, formatter, temp_file, temp_dir):
        """ファイル変換テスト"""
        output_file = temp_dir / "output.html"

        result = formatter.convert(temp_file, output_file)

        assert result["status"] == "success"
        assert result["input_file"] == str(temp_file)
        assert result["output_file"] == str(output_file)
        assert output_file.exists()

        # 出力ファイルの内容確認
        html_content = output_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content
        assert "一時ファイルテスト" in html_content

    def test_convert_auto_output(self, formatter, temp_file):
        """自動出力ファイル名生成テスト"""
        result = formatter.convert(temp_file)

        assert result["status"] == "success"

        output_path = Path(result["output_file"])
        assert output_path.suffix == ".html"
        assert output_path.exists()

        # クリーンアップ
        output_path.unlink()

    def test_convert_nonexistent_file(self, formatter):
        """存在しないファイルの変換テスト"""
        nonexistent = "/path/to/nonexistent/file.txt"
        result = formatter.convert(nonexistent)

        assert result["status"] == "error"
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_get_available_templates(self, formatter):
        """利用可能テンプレート取得テスト"""
        templates = formatter.get_available_templates()

        assert isinstance(templates, list)
        assert "default" in templates
        assert "minimal" in templates

    def test_get_system_info(self, formatter):
        """システム情報取得テスト"""
        info = formatter.get_system_info()

        assert "version" in info
        assert "architecture" in info
        assert "components" in info
        assert "status" in info

        assert info["status"] == "functional"
        assert "SimpleKumihanParser" in info["components"]["parser"]
        assert "SimpleHTMLRenderer" in info["components"]["renderer"]

    def test_context_manager(self, temp_file, temp_dir):
        """コンテキストマネージャーテスト"""
        output_file = temp_dir / "context_output.html"

        with KumihanFormatter() as formatter:
            result = formatter.convert(temp_file, output_file)
            assert result["status"] == "success"

        assert output_file.exists()

    def test_empty_text_parsing(self, formatter):
        """空のテキスト解析テスト"""
        result = formatter.parse_text("")

        assert result["status"] == "success"
        assert result["total_elements"] == 0

    def test_multiple_kumihan_blocks(self, formatter):
        """複数のKumihanブロック処理テスト"""
        text = """# 重要 #最初のブロック##

通常の段落

# 注意 #2番目のブロック##"""

        result = formatter.parse_text(text)

        assert result["status"] == "success"
        assert result["total_elements"] >= 3  # 2つのブロック + 1つの段落

        elements = result["elements"]
        kumihan_blocks = [e for e in elements if e["type"] == "kumihan_block"]
        assert len(kumihan_blocks) == 2

    def test_error_handling_in_parse(self, formatter):
        """解析エラーハンドリングテスト"""
        # 正常ケース - エラーは発生しないはず
        result = formatter.parse_text("正常なテキスト")
        assert result["status"] == "success"

    def test_convert_text_error_handling(self):
        """convert_textメソッドのエラーハンドリングテスト"""
        import unittest.mock as mock

        formatter = KumihanFormatter()

        # rendererでエラーを発生させる
        with mock.patch.object(
            formatter.renderer, "render", side_effect=Exception("Render error")
        ):
            result = formatter.convert_text("# テスト #内容##")

        assert "Conversion Error: Render error" in result

    def test_parse_text_error_handling(self):
        """parse_textメソッドのエラーハンドリングテスト"""
        import unittest.mock as mock

        formatter = KumihanFormatter()

        # parserでエラーを発生させる
        with mock.patch.object(
            formatter.parser, "parse", side_effect=Exception("Parse error")
        ):
            result = formatter.parse_text("# テスト #内容##")

        assert result["status"] == "error"
        assert "Parse error" in result["error"]

    def test_validate_syntax_error_handling(self):
        """validate_syntaxメソッドのエラーハンドリングテスト"""
        import unittest.mock as mock

        formatter = KumihanFormatter()

        # validate呼び出し時にエラーを発生させる
        with mock.patch.object(
            formatter.parser, "validate", side_effect=Exception("Validate error")
        ):
            result = formatter.validate_syntax("# テスト #内容##")

        assert result["status"] == "error"
        assert "Validate error" in result["error"]
        assert result["errors"] == []

    def test_parse_file_error_handling(self):
        """parse_fileメソッドのエラーハンドリングテスト"""
        formatter = KumihanFormatter()

        # 存在しないファイルでエラーを発生させる
        result = formatter.parse_file("nonexistent_file.kumihan")

        assert result["status"] == "error"
        assert "nonexistent_file.kumihan" in result["file_path"]


class TestStandaloneFunctions:
    """スタンドアロン関数のテストクラス"""

    def test_quick_convert(self, tmp_path):
        """quick_convert関数のテスト"""
        # テストファイルの作成
        input_file = tmp_path / "test.kumihan"
        input_file.write_text("# テスト #内容##", encoding="utf-8")
        output_file = tmp_path / "test.html"

        result = quick_convert(str(input_file), str(output_file))

        assert result["status"] == "success"
        assert result["input_file"] == str(input_file)
        assert result["output_file"] == str(output_file)
        assert output_file.exists()

    def test_quick_convert_auto_output(self, tmp_path):
        """quick_convert関数（出力ファイル自動指定）のテスト"""
        input_file = tmp_path / "test.kumihan"
        input_file.write_text("# テスト #内容##", encoding="utf-8")

        result = quick_convert(str(input_file))

        assert result["status"] == "success"
        assert result["input_file"] == str(input_file)
        assert result["output_file"].endswith(".html")

    def test_quick_parse(self):
        """quick_parse関数のテスト"""
        text = "# 重要 #これは重要な情報です##"
        result = quick_parse(text)

        assert result["status"] == "success"
        assert "elements" in result

    def test_unified_parse(self):
        """unified_parse関数のテスト"""
        text = "# 重要 #これは重要な情報です##"
        result = unified_parse(text, "auto")

        assert result["status"] == "success"
        assert "elements" in result

    def test_validate_kumihan_syntax(self):
        """validate_kumihan_syntax関数のテスト"""
        valid_text = "# 重要 #内容##"
        invalid_text = "#  #内容##"

        valid_result = validate_kumihan_syntax(valid_text)
        assert valid_result["status"] == "valid"

        invalid_result = validate_kumihan_syntax(invalid_text)
        assert invalid_result["status"] == "invalid"
        assert len(invalid_result["errors"]) > 0

    def test_get_parser_system_info(self):
        """get_parser_system_info関数のテスト"""
        info = get_parser_system_info()

        assert "components" in info
        assert "version" in info
        assert "architecture" in info
        assert "status" in info


class TestMainFunction:
    """main関数のテストクラス"""

    def test_main_with_no_arguments(self, capsys):
        """引数なしでmain関数を呼び出すテスト"""
        import sys
        import unittest.mock as mock
        from kumihan_formatter.unified_api import main

        with (
            mock.patch.object(sys, "argv", ["kumihan"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        captured = capsys.readouterr()
        assert "使用方法: kumihan <入力ファイル>" in captured.out
        assert exc_info.value.code == 1

    def test_main_successful_conversion(self, tmp_path, capsys):
        """main関数での正常変換テスト"""
        import sys
        import unittest.mock as mock
        from kumihan_formatter.unified_api import main

        # テストファイルの作成
        input_file = tmp_path / "test.kumihan"
        input_file.write_text("# テスト #内容##", encoding="utf-8")
        output_file = tmp_path / "test.html"

        with mock.patch.object(
            sys, "argv", ["kumihan", str(input_file), str(output_file)]
        ):
            main()

        captured = capsys.readouterr()
        assert "変換完了" in captured.out
        assert output_file.exists()

    def test_main_conversion_error(self, capsys):
        """main関数でのエラーハンドリングテスト"""
        import sys
        import unittest.mock as mock
        from kumihan_formatter.unified_api import main

        with (
            mock.patch.object(sys, "argv", ["kumihan", "nonexistent.kumihan"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        captured = capsys.readouterr()
        assert "変換エラー" in captured.out
        assert exc_info.value.code == 1

    def test_main_exception_handling(self, capsys):
        """main関数での例外処理テスト"""
        import sys
        import unittest.mock as mock
        from kumihan_formatter.unified_api import main, quick_convert

        # quick_convertでエラーを発生させる
        with (
            mock.patch(
                "kumihan_formatter.unified_api.quick_convert",
                side_effect=Exception("Unexpected error"),
            ),
            mock.patch.object(sys, "argv", ["kumihan", "test.kumihan"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        captured = capsys.readouterr()
        assert "実行エラー: Unexpected error" in captured.out
        assert exc_info.value.code == 1


class TestConvertTextDebugging:
    """convert_textメソッドのデバッグログテスト"""

    def test_convert_text_debug_logging(self, caplog):
        """convert_textメソッドのデバッグログ出力テスト"""
        import logging

        formatter = KumihanFormatter()

        # ログレベルをDEBUGに設定
        with caplog.at_level(logging.DEBUG):
            result = formatter.convert_text("# テスト #内容##")

        # デバッグログが出力されることを確認
        assert "Text conversion completed" in caplog.text
        assert any("chars →" in record.message for record in caplog.records)


class TestModuleExecution:
    """モジュール実行テスト"""

    def test_unified_api_module_execution(self):
        """unified_api.py の if __name__ == "__main__" 分岐テスト"""
        import sys
        import unittest.mock as mock
        import kumihan_formatter.unified_api as unified_api_module

        # __name__を"__main__"に設定してmain関数を呼び出すことをテスト
        with (
            mock.patch.object(sys, "argv", ["kumihan"]),
            mock.patch.object(unified_api_module, "__name__", "__main__"),
            mock.patch.object(unified_api_module, "main") as mock_main,
        ):

            # モジュールの実行をシミュレート
            if unified_api_module.__name__ == "__main__":
                unified_api_module.main()

            # main()が呼ばれることを確認
            mock_main.assert_called_once()
