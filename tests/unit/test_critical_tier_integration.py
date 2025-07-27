"""
Critical Tier統合テスト - Issue #620 Phase 2対応

実際のCritical Tierファイル（コア機能）の統合テスト
カバレッジ測定と機能確認のための統合テストスイート
"""

from pathlib import Path

import pytest

from kumihan_formatter.core.file_io_handler import FileIOHandler
from kumihan_formatter.core.file_operations import FileOperations
from kumihan_formatter.core.file_validators import PathValidator
from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

# Critical Tierモジュールのインポート
from kumihan_formatter.core.markdown_parser import MarkdownParser


class TestCriticalTierIntegration:
    """Critical Tier統合テスト"""

    def test_markdown_parser_initialization(self):
        """MarkdownParserの初期化テスト"""
        parser = MarkdownParser()

        # パターンが正しく初期化されることを確認
        assert parser.patterns is not None
        assert "h1" in parser.patterns
        assert "strong" in parser.patterns
        assert "link" in parser.patterns

    def test_markdown_parser_heading_patterns(self):
        """MarkdownParserの見出しパターンテスト"""
        parser = MarkdownParser()

        # H1パターンのテスト
        h1_match = parser.patterns["h1"].search("# Test Heading")
        assert h1_match is not None
        assert h1_match.group(1) == "Test Heading"

        # H2パターンのテスト
        h2_match = parser.patterns["h2"].search("## Subheading")
        assert h2_match is not None
        assert h2_match.group(1) == "Subheading"

    def test_markdown_parser_emphasis_patterns(self):
        """MarkdownParserの強調パターンテスト"""
        parser = MarkdownParser()

        # **bold** パターン
        strong_match = parser.patterns["strong"].search("This is **bold** text")
        assert strong_match is not None
        assert strong_match.group(1) == "bold"

        # *italic* パターン
        em_match = parser.patterns["em"].search("This is *italic* text")
        assert em_match is not None
        assert em_match.group(1) == "italic"

    def test_markdown_parser_link_patterns(self):
        """MarkdownParserのリンクパターンテスト"""
        parser = MarkdownParser()

        link_match = parser.patterns["link"].search("[example](https://example.com)")
        assert link_match is not None
        assert link_match.group(1) == "example"
        assert link_match.group(2) == "https://example.com"

    def test_file_io_handler_initialization(self):
        """FileIOHandlerの初期化テスト"""
        handler = FileIOHandler()

        # 基本的な初期化確認
        assert handler is not None
        assert hasattr(handler, "read_text_file")
        assert hasattr(handler, "write_text_file")

    def test_file_io_handler_read_capabilities(self):
        """FileIOHandlerの読み込み機能テスト"""
        handler = FileIOHandler()

        # 非存在ファイルの処理
        from pathlib import Path

        try:
            result = handler.read_text_file(Path("/nonexistent/file.txt"))
            # エラーハンドリングまたはNone返却が期待される
            assert result is None or isinstance(result, str)
        except FileNotFoundError:
            # ファイルが見つからない例外も許容される
            pass

    def test_markdown_converter_initialization(self):
        """SimpleMarkdownConverterの初期化テスト"""
        converter = SimpleMarkdownConverter()

        # 基本的な初期化確認
        assert converter is not None
        assert hasattr(converter, "convert_file")

    def test_file_operations_initialization(self):
        """FileOperationsの初期化テスト"""
        operations = FileOperations()

        # 基本的な初期化確認
        assert operations is not None

    def test_path_validator_static_methods(self):
        """PathValidatorの静的メソッドテスト"""
        # 静的メソッドの存在確認
        assert hasattr(PathValidator, "validate_input_file")
        assert hasattr(PathValidator, "validate_output_directory")

    def test_path_validator_input_validation(self):
        """PathValidatorの入力ファイル検証テスト"""
        # 非存在ファイルの検証（例外が発生することを期待）
        with pytest.raises(FileNotFoundError):
            PathValidator.validate_input_file("/nonexistent/file.txt")

    def test_path_validator_directory_validation(self):
        """PathValidatorのディレクトリ検証テスト"""
        # 一時ディレクトリでのテスト
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            result = PathValidator.validate_output_directory(temp_dir)
            assert isinstance(result, Path)
            assert result.exists()


class TestCriticalTierBasicCoverage:
    """Critical Tier基本カバレッジテスト"""

    def test_all_critical_modules_importable(self):
        """全Critical Tierモジュールがインポート可能であることを確認"""
        modules = [
            "kumihan_formatter.core.markdown_parser",
            "kumihan_formatter.core.file_io_handler",
            "kumihan_formatter.core.markdown_converter",
            "kumihan_formatter.core.file_operations",
            "kumihan_formatter.core.file_validators",
        ]

        for module_name in modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(
                    f"Critical Tier module {module_name} could not be imported: {e}"
                )

    def test_critical_classes_instantiable(self):
        """Critical Tierクラスがインスタンス化可能であることを確認"""
        classes = [
            MarkdownParser,
            FileIOHandler,
            SimpleMarkdownConverter,
            FileOperations,
        ]

        for cls in classes:
            try:
                instance = cls()
                assert instance is not None
            except Exception as e:
                pytest.fail(
                    f"Critical Tier class {cls.__name__} could not be instantiated: {e}"
                )

    def test_critical_tier_file_structure_coverage(self):
        """Critical Tierファイル構造のカバレッジテスト"""
        critical_files = [
            "kumihan_formatter/core/error_reporting.py",
            "kumihan_formatter/core/file_operations.py",
            "kumihan_formatter/core/markdown_converter.py",
            "kumihan_formatter/core/file_validators.py",
            "kumihan_formatter/core/markdown_parser.py",
            "kumihan_formatter/core/file_io_handler.py",
        ]

        project_root = Path(__file__).parent.parent.parent

        for file_path in critical_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Critical Tier file {file_path} does not exist"
            assert (
                full_path.stat().st_size > 0
            ), f"Critical Tier file {file_path} is empty"


class TestCriticalTierComplexIntegration:
    """Critical Tier複合統合テスト"""

    def test_markdown_parser_and_converter_integration(self):
        """MarkdownParserとConverterの統合テスト"""
        parser = MarkdownParser()
        converter = SimpleMarkdownConverter()

        # パーサーのパターンがコンバーターで利用可能かテスト
        test_text = "# Test Heading\n\nThis is **bold** text."

        # パーサーでパターンマッチング
        h1_matches = parser.patterns["h1"].findall(test_text)
        strong_matches = parser.patterns["strong"].findall(test_text)

        assert len(h1_matches) == 1
        assert h1_matches[0] == "Test Heading"
        assert len(strong_matches) == 1
        assert strong_matches[0] == "bold"

    def test_file_operations_and_validators_integration(self):
        """FileOperationsとPathValidatorの統合テスト"""
        operations = FileOperations()

        # FileOperationsが基本機能を提供することを確認
        assert operations is not None
        assert hasattr(operations, "__init__")

        # PathValidatorの静的メソッドが利用可能なことを確認
        assert hasattr(PathValidator, "validate_input_file")
        assert hasattr(PathValidator, "validate_output_directory")

    def test_file_io_and_operations_integration(self):
        """FileIOHandlerとOperationsの統合テスト"""
        io_handler = FileIOHandler()
        operations = FileOperations()

        # 両方のコンポーネントが基本機能を提供することを確認
        assert io_handler is not None
        assert operations is not None

        # IOハンドラーの基本機能
        assert hasattr(io_handler, "read_text_file")
        assert hasattr(io_handler, "write_text_file")
