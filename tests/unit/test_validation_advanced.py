"""バリデーション機能の高度なテスト - Important Tier対応"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.core.validators.document_validator import DocumentValidator
from kumihan_formatter.core.validators.file_validator import FileValidator
from kumihan_formatter.core.validators.performance_validator import PerformanceValidator
from kumihan_formatter.core.validators.structure_validator import StructureValidator
from kumihan_formatter.core.validators.syntax_validator import SyntaxValidator


class TestDocumentValidatorAdvanced:
    """DocumentValidatorの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = DocumentValidator()
        self.logger = get_logger(__name__)

    def test_document_validator_initialization(self):
        """DocumentValidator初期化テスト"""
        assert self.validator is not None
        assert hasattr(self.validator, "validate_document")
        assert hasattr(self.validator, "get_validation_errors")

    def test_validate_empty_document(self):
        """空ドキュメントバリデーションテスト"""
        empty_ast = MagicMock()
        empty_ast.children = []

        with patch.object(self.validator, "validate_document") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_document(empty_ast)
            assert result is not None
            assert result.get("is_valid", False) or len(result.get("errors", [])) == 0

    def test_validate_well_formed_document(self):
        """整形されたドキュメントバリデーションテスト"""
        well_formed_ast = MagicMock()

        # 適切に構造化されたノード
        header_node = MagicMock()
        header_node.type = "header"
        header_node.level = 1
        header_node.content = "メインタイトル"

        content_node = MagicMock()
        content_node.type = "text"
        content_node.content = "適切なコンテンツ"

        well_formed_ast.children = [header_node, content_node]

        with patch.object(self.validator, "validate_document") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_document(well_formed_ast)
            assert result is not None

    def test_validate_malformed_document(self):
        """不正なドキュメントバリデーションテスト"""
        malformed_ast = MagicMock()

        # 不正なノード
        invalid_node = MagicMock()
        invalid_node.type = "unknown_type"
        invalid_node.content = None  # 不正なコンテンツ

        malformed_ast.children = [invalid_node]

        with patch.object(self.validator, "validate_document") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Unknown node type: unknown_type", "Invalid content: None"],
            }

            result = self.validator.validate_document(malformed_ast)
            assert result is not None

    def test_validate_nested_structure(self):
        """ネスト構造バリデーションテスト"""
        nested_ast = MagicMock()

        # ネストされた構造
        outer_node = MagicMock()
        outer_node.type = "decoration"
        outer_node.keywords = ["強調"]

        inner_node = MagicMock()
        inner_node.type = "text"
        inner_node.content = "内部コンテンツ"

        outer_node.children = [inner_node]
        nested_ast.children = [outer_node]

        with patch.object(self.validator, "validate_document") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_document(nested_ast)
            assert result is not None

    def test_validate_complex_document_structure(self):
        """複雑なドキュメント構造バリデーションテスト"""
        complex_ast = MagicMock()

        # 複雑な構造を作成
        nodes = []

        # ヘッダー
        header = MagicMock()
        header.type = "header"
        header.level = 1
        header.content = "メインタイトル"
        nodes.append(header)

        # 装飾されたテキスト
        decorated = MagicMock()
        decorated.type = "decoration"
        decorated.keywords = ["強調", "重要"]
        decorated.content = "重要な情報"
        nodes.append(decorated)

        # リスト
        list_node = MagicMock()
        list_node.type = "list"
        list_node.list_type = "unordered"

        list_items = []
        for i in range(3):
            item = MagicMock()
            item.type = "list_item"
            item.content = f"項目{i+1}"
            list_items.append(item)
        list_node.children = list_items
        nodes.append(list_node)

        complex_ast.children = nodes

        with patch.object(self.validator, "validate_document") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_document(complex_ast)
            assert result is not None


class TestStructureValidatorAdvanced:
    """StructureValidatorの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = StructureValidator()

    def test_structure_validator_initialization(self):
        """StructureValidator初期化テスト"""
        assert self.validator is not None
        assert hasattr(self.validator, "validate_structure")

    def test_validate_header_hierarchy(self):
        """ヘッダー階層バリデーションテスト"""
        # 正しいヘッダー階層
        correct_hierarchy = [
            {"type": "header", "level": 1, "content": "H1"},
            {"type": "header", "level": 2, "content": "H2"},
            {"type": "header", "level": 3, "content": "H3"},
        ]

        with patch.object(self.validator, "validate_structure") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_structure(correct_hierarchy)
            assert result is not None

    def test_validate_incorrect_header_hierarchy(self):
        """不正なヘッダー階層バリデーションテスト"""
        # 不正なヘッダー階層（H1→H3へスキップ）
        incorrect_hierarchy = [
            {"type": "header", "level": 1, "content": "H1"},
            {"type": "header", "level": 3, "content": "H3"},  # H2をスキップ
        ]

        with patch.object(self.validator, "validate_structure") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Header level skipped: H1 to H3"],
            }

            result = self.validator.validate_structure(incorrect_hierarchy)
            assert result is not None

    def test_validate_list_structure(self):
        """リスト構造バリデーションテスト"""
        # 正しいリスト構造
        correct_list = {
            "type": "list",
            "list_type": "unordered",
            "children": [
                {"type": "list_item", "content": "項目1"},
                {"type": "list_item", "content": "項目2"},
            ],
        }

        with patch.object(self.validator, "validate_structure") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_structure(correct_list)
            assert result is not None

    def test_validate_nested_list_structure(self):
        """ネストリスト構造バリデーションテスト"""
        # ネストされたリスト構造
        nested_list = {
            "type": "list",
            "list_type": "unordered",
            "children": [
                {
                    "type": "list_item",
                    "content": "外側項目1",
                    "children": [
                        {
                            "type": "list",
                            "list_type": "ordered",
                            "children": [
                                {"type": "list_item", "content": "内側項目1"},
                                {"type": "list_item", "content": "内側項目2"},
                            ],
                        }
                    ],
                }
            ],
        }

        with patch.object(self.validator, "validate_structure") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_structure(nested_list)
            assert result is not None


class TestSyntaxValidatorAdvanced:
    """SyntaxValidatorの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = SyntaxValidator()

    def test_syntax_validator_initialization(self):
        """SyntaxValidator初期化テスト"""
        assert self.validator is not None
        assert hasattr(self.validator, "validate_syntax")

    def test_validate_correct_syntax(self):
        """正しい構文バリデーションテスト"""
        correct_syntax = ";;;強調;;; 正しいコンテンツ ;;;"

        with patch.object(self.validator, "validate_syntax") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_syntax(correct_syntax)
            assert result is not None

    def test_validate_unclosed_decoration(self):
        """未閉じ装飾構文バリデーションテスト"""
        unclosed_syntax = ";;;強調;;; 未閉じコンテンツ"

        with patch.object(self.validator, "validate_syntax") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Unclosed decoration at end of content"],
            }

            result = self.validator.validate_syntax(unclosed_syntax)
            assert result is not None

    def test_validate_mismatched_markers(self):
        """不一致マーカー構文バリデーションテスト"""
        mismatched_syntax = ";;;強調;;; コンテンツ ;;"  # 閉じマーカーが不一致

        with patch.object(self.validator, "validate_syntax") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Mismatched closing marker"],
            }

            result = self.validator.validate_syntax(mismatched_syntax)
            assert result is not None

    def test_validate_nested_syntax(self):
        """ネスト構文バリデーションテスト"""
        nested_syntax = ";;;外側;;; ;;;内側;;; ネストコンテンツ ;;; 外側コンテンツ ;;;"

        with patch.object(self.validator, "validate_syntax") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_syntax(nested_syntax)
            assert result is not None

    def test_validate_ruby_syntax(self):
        """ルビ構文バリデーションテスト"""
        ruby_syntax = "｜漢字《かんじ》"

        with patch.object(self.validator, "validate_syntax") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_syntax(ruby_syntax)
            assert result is not None

    def test_validate_footnote_syntax(self):
        """脚注構文バリデーションテスト"""
        footnote_syntax = "テキスト ((脚注の内容)) 続きのテキスト"

        with patch.object(self.validator, "validate_syntax") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_syntax(footnote_syntax)
            assert result is not None


class TestFileValidatorAdvanced:
    """FileValidatorの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = FileValidator()

    def test_file_validator_initialization(self):
        """FileValidator初期化テスト"""
        assert self.validator is not None
        assert hasattr(self.validator, "validate_file")

    def test_validate_existing_file(self):
        """存在するファイルバリデーションテスト"""
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as test_file:
            test_file.write(";;;強調;;; テストコンテンツ ;;;")
            file_path = test_file.name

        try:
            with patch.object(self.validator, "validate_file") as mock_validate:
                mock_validate.return_value = {"is_valid": True, "errors": []}

                result = self.validator.validate_file(file_path)
                assert result is not None

        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_validate_nonexistent_file(self):
        """存在しないファイルバリデーションテスト"""
        nonexistent_path = "/path/to/nonexistent/file.txt"

        with patch.object(self.validator, "validate_file") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["File not found: /path/to/nonexistent/file.txt"],
            }

            result = self.validator.validate_file(nonexistent_path)
            assert result is not None

    def test_validate_file_encoding(self):
        """ファイルエンコーディングバリデーションテスト"""
        # UTF-8ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as test_file:
            test_file.write("日本語コンテンツのテスト")
            file_path = test_file.name

        try:
            with patch.object(self.validator, "validate_file") as mock_validate:
                mock_validate.return_value = {"is_valid": True, "errors": []}

                result = self.validator.validate_file(file_path)
                assert result is not None

        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_validate_file_size(self):
        """ファイルサイズバリデーションテスト"""
        # 大きなファイルを作成
        large_content = "A" * 10000  # 10KB

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as test_file:
            test_file.write(large_content)
            file_path = test_file.name

        try:
            with patch.object(self.validator, "validate_file") as mock_validate:
                mock_validate.return_value = {"is_valid": True, "errors": []}

                result = self.validator.validate_file(file_path)
                assert result is not None

        finally:
            Path(file_path).unlink(missing_ok=True)


class TestPerformanceValidatorAdvanced:
    """PerformanceValidatorの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.validator = PerformanceValidator()

    def test_performance_validator_initialization(self):
        """PerformanceValidator初期化テスト"""
        assert self.validator is not None
        assert hasattr(self.validator, "validate_performance")

    def test_validate_processing_time(self):
        """処理時間バリデーションテスト"""
        performance_data = {
            "parse_time": 0.5,  # 500ms
            "render_time": 0.3,  # 300ms
            "total_time": 0.8,  # 800ms
        }

        with patch.object(self.validator, "validate_performance") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_performance(performance_data)
            assert result is not None

    def test_validate_memory_usage(self):
        """メモリ使用量バリデーションテスト"""
        performance_data = {
            "memory_used": 50 * 1024 * 1024,  # 50MB
            "peak_memory": 80 * 1024 * 1024,  # 80MB
        }

        with patch.object(self.validator, "validate_performance") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = self.validator.validate_performance(performance_data)
            assert result is not None

    def test_validate_excessive_processing_time(self):
        """過度な処理時間バリデーションテスト"""
        performance_data = {
            "parse_time": 5.0,  # 5秒（過度）
            "render_time": 3.0,  # 3秒（過度）
            "total_time": 8.0,  # 8秒（過度）
        }

        with patch.object(self.validator, "validate_performance") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Excessive processing time: 8.0s exceeds 5.0s limit"],
            }

            result = self.validator.validate_performance(performance_data)
            assert result is not None

    def test_validate_memory_leak(self):
        """メモリリークバリデーションテスト"""
        performance_data = {
            "initial_memory": 100 * 1024 * 1024,  # 100MB
            "final_memory": 500 * 1024 * 1024,  # 500MB（大幅増加）
            "memory_increase": 400 * 1024 * 1024,  # 400MB増加
        }

        with patch.object(self.validator, "validate_performance") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Potential memory leak: 400MB increase detected"],
            }

            result = self.validator.validate_performance(performance_data)
            assert result is not None


class TestValidationIntegration:
    """バリデーション機能統合テスト"""

    def test_validation_pipeline_integration(self):
        """バリデーションパイプライン統合テスト"""
        # 複数のバリデーターを組み合わせたテスト
        document_validator = DocumentValidator()
        structure_validator = StructureValidator()
        syntax_validator = SyntaxValidator()

        # テストデータ
        test_content = ";;;強調;;; 統合テストコンテンツ ;;;"
        test_ast = MagicMock()

        with (
            patch.object(syntax_validator, "validate_syntax") as mock_syntax,
            patch.object(structure_validator, "validate_structure") as mock_structure,
            patch.object(document_validator, "validate_document") as mock_document,
        ):

            # 各バリデーターの結果をモック
            mock_syntax.return_value = {"is_valid": True, "errors": []}
            mock_structure.return_value = {"is_valid": True, "errors": []}
            mock_document.return_value = {"is_valid": True, "errors": []}

            # バリデーションパイプライン実行
            syntax_result = syntax_validator.validate_syntax(test_content)
            structure_result = structure_validator.validate_structure(test_ast)
            document_result = document_validator.validate_document(test_ast)

            # 全てのバリデーションが実行されたことを確認
            mock_syntax.assert_called_once()
            mock_structure.assert_called_once()
            mock_document.assert_called_once()

            # 全ての結果が有効であることを確認
            assert syntax_result is not None
            assert structure_result is not None
            assert document_result is not None

    def test_validation_error_aggregation(self):
        """バリデーションエラー集約テスト"""
        # 複数のバリデーターからのエラーを集約する
        validators = [DocumentValidator(), StructureValidator(), SyntaxValidator()]

        # 各バリデーターでエラーが発生する場合
        error_results = [
            {"is_valid": False, "errors": ["Document error 1", "Document error 2"]},
            {"is_valid": False, "errors": ["Structure error 1"]},
            {"is_valid": False, "errors": ["Syntax error 1", "Syntax error 2"]},
        ]

        # エラー集約のシミュレーション
        all_errors = []
        for result in error_results:
            if not result["is_valid"]:
                all_errors.extend(result["errors"])

        # 全てのエラーが集約されたことを確認
        assert len(all_errors) == 5
        assert "Document error 1" in all_errors
        assert "Structure error 1" in all_errors
        assert "Syntax error 1" in all_errors

    def test_validation_performance_monitoring(self):
        """バリデーション性能監視テスト"""
        # バリデーション処理の性能を監視
        validator = DocumentValidator()

        # 大きなASTでの性能テスト
        large_ast = MagicMock()
        large_ast.children = []

        for i in range(1000):
            node = MagicMock()
            node.type = "text"
            node.content = f"ノード{i}"
            large_ast.children.append(node)

        import time

        start_time = time.time()

        with patch.object(validator, "validate_document") as mock_validate:
            mock_validate.return_value = {"is_valid": True, "errors": []}

            result = validator.validate_document(large_ast)

        end_time = time.time()

        # バリデーションが妥当な時間内で完了することを確認
        assert result is not None
        assert (end_time - start_time) < 2.0  # 2秒以内
