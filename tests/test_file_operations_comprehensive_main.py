"""
file_operations.py の包括的テスト

Issue #591 Critical Tier Testing対応
- 80%以上のテストカバレッジ
- 100%エッジケーステスト
- 統合テスト・回帰テスト
"""

import base64
import shutil
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.file_operations import (
    FileIOHandler,
    FileOperations,
    FileOperationsComponents,
    FileOperationsCore,
    FilePathUtilities,
    create_file_io_handler,
    create_file_operations,
    create_file_path_utilities,
)


class TestFileOperationsUnifiedInterface:
    """統合インターフェースのテスト"""

    def test_file_operations_inheritance(self):
        """FileOperationsがFileOperationsCoreを継承していることを確認"""
        assert issubclass(FileOperations, FileOperationsCore)

    def test_file_operations_static_method_delegation(self):
        """静的メソッドの委譲が正しく設定されていることを確認"""
        # FilePathUtilitiesからの委譲
        assert hasattr(FileOperations, "load_distignore_patterns")
        assert hasattr(FileOperations, "should_exclude")
        assert hasattr(FileOperations, "get_file_size_info")
        assert hasattr(FileOperations, "estimate_processing_time")

        # FileIOHandlerからの委譲
        assert hasattr(FileOperations, "write_text_file")
        assert hasattr(FileOperations, "read_text_file")

    def test_file_operations_module_exports(self):
        """__all__に必要なエクスポートが含まれていることを確認"""
        from kumihan_formatter.core import file_operations

        expected_exports = [
            "FileOperations",
            "FileOperationsCore",
            "FilePathUtilities",
            "FileIOHandler",
            "create_file_operations",
            "create_file_path_utilities",
            "create_file_io_handler",
            "FileOperationsComponents",
        ]

        for export in expected_exports:
            assert export in file_operations.__all__

    def test_backward_compatibility_methods(self):
        """後方互換性メソッドが利用可能であることを確認"""
        file_ops = FileOperations()

        # FilePathUtilitiesメソッドが利用可能
        assert callable(file_ops.load_distignore_patterns)
        assert callable(file_ops.should_exclude)
        assert callable(file_ops.get_file_size_info)
        assert callable(file_ops.estimate_processing_time)

        # FileIOHandlerメソッドが利用可能
        assert callable(file_ops.write_text_file)
        assert callable(file_ops.read_text_file)


class TestFileOperationsCore:
    """FileOperationsCoreのテスト"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """テンポラリディレクトリのフィクスチャ"""
        return tmp_path

    @pytest.fixture
    def mock_ui(self):
        """モックUIのフィクスチャ"""
        ui = MagicMock()
        return ui

    @pytest.fixture
    def file_ops_core(self, mock_ui):
        """FileOperationsCoreのフィクスチャ"""
        return FileOperationsCore(mock_ui)

    def test_init_with_ui(self, mock_ui):
        """UI付きで初期化できることを確認"""
        core = FileOperationsCore(mock_ui)
        assert core.ui is mock_ui
        assert core.logger is not None

    def test_init_without_ui(self):
        """UIなしで初期化できることを確認"""
        core = FileOperationsCore()
        assert core.ui is None
        assert core.logger is not None

    def test_copy_images_no_image_nodes(self, file_ops_core, temp_dir):
        """画像ノードがない場合のテスト"""
        input_path = temp_dir / "input.txt"
        output_path = temp_dir / "output"
        ast = []

        # 例外が発生しないことを確認
        file_ops_core.copy_images(input_path, output_path, ast)

    def test_copy_images_missing_images_dir(self, file_ops_core, temp_dir, mock_ui):
        """imagesディレクトリが存在しない場合のテスト"""
        input_path = temp_dir / "input.txt"
        input_path.touch()
        output_path = temp_dir / "output"

        # モック画像ノード
        mock_node = MagicMock()
        mock_node.type = "image"
        mock_node.content = "test.png"
        ast = [mock_node]

        file_ops_core.copy_images(input_path, output_path, ast)

        # 警告が出力されることを確認
        mock_ui.warning.assert_called_once()

    def test_copy_images_successful_copy(self, file_ops_core, temp_dir):
        """画像コピーが成功するケースのテスト"""
        # テスト用ディレクトリ構成作成
        input_path = temp_dir / "input.txt"
        input_path.touch()
        images_dir = temp_dir / "images"
        images_dir.mkdir()

        # テスト画像作成
        test_image = images_dir / "test.png"
        test_image.write_bytes(b"fake image data")

        output_path = temp_dir / "output"

        # モック画像ノード
        mock_node = MagicMock()
        mock_node.type = "image"
        mock_node.content = "test.png"
        ast = [mock_node]

        file_ops_core.copy_images(input_path, output_path, ast)

        # コピーされた画像が存在することを確認
        copied_image = output_path / "images" / "test.png"
        assert copied_image.exists()
        assert copied_image.read_bytes() == b"fake image data"

    def test_copy_images_duplicate_handling(self, file_ops_core, temp_dir):
        """重複画像の処理テスト"""
        # テスト用設定
        input_path = temp_dir / "input.txt"
        input_path.touch()
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        test_image = images_dir / "test.png"
        test_image.write_bytes(b"image data")

        output_path = temp_dir / "output"

        # 同じ画像ファイルが複数回参照されるケース
        mock_node1 = MagicMock()
        mock_node1.type = "image"
        mock_node1.content = "test.png"

        mock_node2 = MagicMock()
        mock_node2.type = "image"
        mock_node2.content = "test.png"

        ast = [mock_node1, mock_node2]

        file_ops_core.copy_images(input_path, output_path, ast)

        # 重複が検出され、UIに報告されることを確認
        if file_ops_core.ui:
            file_ops_core.ui.duplicate_files.assert_called_once()

    def test_copy_images_missing_file_handling(self, file_ops_core, temp_dir):
        """存在しない画像ファイルの処理テスト"""
        input_path = temp_dir / "input.txt"
        input_path.touch()
        images_dir = temp_dir / "images"
        images_dir.mkdir()

        output_path = temp_dir / "output"

        # 存在しない画像ファイル
        mock_node = MagicMock()
        mock_node.type = "image"
        mock_node.content = "nonexistent.png"
        ast = [mock_node]

        file_ops_core.copy_images(input_path, output_path, ast)

        # 欠損ファイルが報告されることを確認
        if file_ops_core.ui:
            file_ops_core.ui.files_missing.assert_called_once()

    def test_create_sample_images(self, temp_dir):
        """サンプル画像作成のテスト"""
        images_dir = temp_dir / "sample_images"

        # Base64エンコードされた小さなテスト画像
        # 1x1ピクセルの透明PNG
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77kwAAAABJRU5ErkJggg=="
        sample_images = {"test.png": sample_base64}

        FileOperationsCore.create_sample_images(images_dir, sample_images)

        # ディレクトリと画像ファイルが作成されていることを確認
        assert images_dir.exists()
        test_image = images_dir / "test.png"
        assert test_image.exists()

        # ファイルの内容が正しいことを確認
        expected_data = base64.b64decode(sample_base64)
        assert test_image.read_bytes() == expected_data

    def test_copy_directory_with_exclusions(self, temp_dir):
        """除外パターン付きディレクトリコピーのテスト"""
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        dest_dir = temp_dir / "dest"

        # テストファイル作成
        (source_dir / "include.txt").write_text("include")
        (source_dir / "exclude.tmp").write_text("exclude")
        (source_dir / "subdir").mkdir()
        (source_dir / "subdir" / "include2.txt").write_text("include2")
        (source_dir / "subdir" / "exclude2.tmp").write_text("exclude2")

        exclude_patterns = ["*.tmp"]

        copied, excluded = FileOperationsCore.copy_directory_with_exclusions(
            source_dir, dest_dir, exclude_patterns
        )

        # コピー結果の確認
        assert copied == 2  # include.txt, include2.txt
        assert excluded == 2  # exclude.tmp, exclude2.tmp

        # ファイルが正しくコピーされていることを確認
        assert (dest_dir / "include.txt").exists()
        assert (dest_dir / "subdir" / "include2.txt").exists()
        assert not (dest_dir / "exclude.tmp").exists()
        assert not (dest_dir / "subdir" / "exclude2.tmp").exists()

    def test_find_preview_file(self, temp_dir):
        """プレビューファイル検索のテスト"""
        # プレビューファイルが存在しない場合
        assert FileOperationsCore.find_preview_file(temp_dir) is None

        # index.htmlが存在する場合
        (temp_dir / "index.html").touch()
        result = FileOperationsCore.find_preview_file(temp_dir)
        assert result == temp_dir / "index.html"

        # 複数のプレビューファイルがある場合の優先順位テスト
        (temp_dir / "README.html").touch()
        (temp_dir / "readme.html").touch()
        result = FileOperationsCore.find_preview_file(temp_dir)
        assert result == temp_dir / "index.html"  # index.htmlが最優先

    def test_ensure_directory(self, temp_dir):
        """ディレクトリ作成のテスト"""
        test_dir = temp_dir / "new" / "nested" / "directory"
        assert not test_dir.exists()

        FileOperationsCore.ensure_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

        # 既存ディレクトリの場合でもエラーが出ないことを確認
        FileOperationsCore.ensure_directory(test_dir)
        assert test_dir.exists()

    def test_check_large_file_warning_small_file(self, file_ops_core, temp_dir):
        """小さなファイルの場合の警告チェック"""
        small_file = temp_dir / "small.txt"
        small_file.write_text("small content")

        result = file_ops_core.check_large_file_warning(small_file, max_size_mb=1.0)
        assert result is True

        # UIの警告メソッドが呼ばれていないことを確認
        if file_ops_core.ui:
            file_ops_core.ui.warning.assert_not_called()

    @patch(
        "kumihan_formatter.core.file_path_utilities.FilePathUtilities.get_file_size_info"
    )
    def test_check_large_file_warning_large_file(
        self, mock_get_file_size, file_ops_core, temp_dir
    ):
        """大きなファイルの場合の警告チェック"""
        large_file = temp_dir / "large.txt"
        large_file.write_text("content")

        # ファイルサイズ情報をモック
        mock_get_file_size.return_value = {"size_mb": 100.0}

        result = file_ops_core.check_large_file_warning(large_file, max_size_mb=50.0)
        assert result is True

        # UIの警告メソッドが呼ばれることを確認
        if file_ops_core.ui:
            file_ops_core.ui.warning.assert_called_once()
            file_ops_core.ui.info.assert_called_once()


class TestFileOperationsFactory:
    """ファクトリー関数のテスト"""

    def test_create_file_operations_with_ui(self):
        """UI付きFileOperationsCore作成のテスト"""
        mock_ui = MagicMock()
        core = create_file_operations(mock_ui)

        assert isinstance(core, FileOperationsCore)
        assert core.ui is mock_ui

    def test_create_file_operations_without_ui(self):
        """UI無しFileOperationsCore作成のテスト"""
        core = create_file_operations()

        assert isinstance(core, FileOperationsCore)
        assert core.ui is None

    def test_create_file_path_utilities(self):
        """FilePathUtilities作成のテスト"""
        utils = create_file_path_utilities()
        assert isinstance(utils, FilePathUtilities)

    def test_create_file_io_handler(self):
        """FileIOHandler作成のテスト"""
        handler = create_file_io_handler()
        assert isinstance(handler, FileIOHandler)


class TestFileOperationsComponents:
    """FileOperationsComponents統合管理のテスト"""

    def test_init_with_ui(self):
        """UI付き初期化のテスト"""
        mock_ui = MagicMock()
        components = FileOperationsComponents(mock_ui)
        assert components.ui is mock_ui

    def test_init_without_ui(self):
        """UI無し初期化のテスト"""
        components = FileOperationsComponents()
        assert components.ui is None

    def test_lazy_initialization_core(self):
        """コアの遅延初期化テスト"""
        components = FileOperationsComponents()

        # 初期状態ではNone
        assert components._core is None

        # 最初のアクセスで初期化される
        core = components.core
        assert isinstance(core, FileOperationsCore)
        assert components._core is core

        # 2回目のアクセスでは同じインスタンスが返される
        core2 = components.core
        assert core2 is core

    def test_lazy_initialization_path_utils(self):
        """パスユーティリティの遅延初期化テスト"""
        components = FileOperationsComponents()

        assert components._path_utils is None

        path_utils = components.path_utils
        assert isinstance(path_utils, FilePathUtilities)
        assert components._path_utils is path_utils

        path_utils2 = components.path_utils
        assert path_utils2 is path_utils

    def test_lazy_initialization_io_handler(self):
        """I/Oハンドラーの遅延初期化テスト"""
        components = FileOperationsComponents()

        assert components._io_handler is None

        io_handler = components.io_handler
        assert isinstance(io_handler, FileIOHandler)
        assert components._io_handler is io_handler

        io_handler2 = components.io_handler
        assert io_handler2 is io_handler


class TestFileOperationsEdgeCases:
    """エッジケーステスト - 100%カバレッジ"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_empty_ast_copy_images(self, temp_dir):
        """空のASTでのcopy_imagesテスト"""
        file_ops = FileOperationsCore()
        input_path = temp_dir / "input.txt"
        output_path = temp_dir / "output"

        # 空のAST
        file_ops.copy_images(input_path, output_path, [])

        # 出力ディレクトリが作成されないことを確認
        assert not (output_path / "images").exists()

    def test_non_image_nodes_in_ast(self, temp_dir):
        """AST内に画像以外のノードがある場合のテスト"""
        file_ops = FileOperationsCore()
        input_path = temp_dir / "input.txt"
        output_path = temp_dir / "output"

        # 画像以外のノード
        text_node = MagicMock()
        text_node.type = "text"
        text_node.content = "some text"

        ast = [text_node]

        file_ops.copy_images(input_path, output_path, ast)

        # 画像処理が行われないことを確認
        assert not (output_path / "images").exists()

    def test_mixed_node_types_in_ast(self, temp_dir):
        """AST内に画像ノードと他のノードが混在する場合のテスト"""
        file_ops = FileOperationsCore()
        input_path = temp_dir / "input.txt"
        input_path.touch()

        # imagesディレクトリとテスト画像作成
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        (images_dir / "test.png").write_bytes(b"test image")

        output_path = temp_dir / "output"

        # 混在ノード
        text_node = MagicMock()
        text_node.type = "text"
        text_node.content = "text"

        image_node = MagicMock()
        image_node.type = "image"
        image_node.content = "test.png"

        heading_node = MagicMock()
        heading_node.type = "heading"
        heading_node.content = "Title"

        ast = [text_node, image_node, heading_node]

        file_ops.copy_images(input_path, output_path, ast)

        # 画像のみがコピーされることを確認
        assert (output_path / "images" / "test.png").exists()

    def test_create_sample_images_empty_dict(self, temp_dir):
        """空の辞書でのサンプル画像作成テスト"""
        images_dir = temp_dir / "empty_samples"

        FileOperationsCore.create_sample_images(images_dir, {})

        # ディレクトリは作成されるが、ファイルは作成されない
        assert images_dir.exists()
        assert list(images_dir.iterdir()) == []

    def test_create_sample_images_invalid_base64(self, temp_dir):
        """無効なBase64データでのサンプル画像作成テスト"""
        images_dir = temp_dir / "invalid_samples"
        invalid_samples = {"invalid.png": "invalid_base64_data!!!"}

        with pytest.raises(Exception):  # base64.b64decode例外
            FileOperationsCore.create_sample_images(images_dir, invalid_samples)

    def test_copy_directory_empty_exclusions(self, temp_dir):
        """空の除外パターンでのディレクトリコピーテスト"""
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        dest_dir = temp_dir / "dest"

        # テストファイル作成
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.py").write_text("content2")

        copied, excluded = FileOperationsCore.copy_directory_with_exclusions(
            source_dir, dest_dir, []
        )

        # 全ファイルがコピーされることを確認
        assert copied == 2
        assert excluded == 0
        assert (dest_dir / "file1.txt").exists()
        assert (dest_dir / "file2.py").exists()

    def test_copy_directory_all_excluded(self, temp_dir):
        """全ファイルが除外される場合のテスト"""
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        dest_dir = temp_dir / "dest"

        # テストファイル作成
        (source_dir / "temp1.tmp").write_text("temp1")
        (source_dir / "temp2.tmp").write_text("temp2")

        exclude_patterns = ["*.tmp"]

        copied, excluded = FileOperationsCore.copy_directory_with_exclusions(
            source_dir, dest_dir, exclude_patterns
        )

        # 全ファイルが除外されることを確認
        assert copied == 0
        assert excluded == 2

    def test_copy_directory_nested_structure(self, temp_dir):
        """深い階層のディレクトリ構造でのコピーテスト"""
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        dest_dir = temp_dir / "dest"

        # 複雑な階層構造作成
        (source_dir / "level1").mkdir()
        (source_dir / "level1" / "level2").mkdir()
        (source_dir / "level1" / "level2" / "level3").mkdir()

        (source_dir / "level1" / "file1.txt").write_text("file1")
        (source_dir / "level1" / "level2" / "file2.txt").write_text("file2")
        (source_dir / "level1" / "level2" / "level3" / "file3.txt").write_text("file3")

        copied, excluded = FileOperationsCore.copy_directory_with_exclusions(
            source_dir, dest_dir, []
        )

        assert copied == 3
        assert excluded == 0

        # 階層構造が保持されることを確認
        assert (dest_dir / "level1" / "file1.txt").exists()
        assert (dest_dir / "level1" / "level2" / "file2.txt").exists()
        assert (dest_dir / "level1" / "level2" / "level3" / "file3.txt").exists()


class TestFileOperationsIntegration:
    """統合テスト"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    @pytest.mark.integration
    def test_full_file_operations_workflow(self, temp_dir):
        """完全なファイル操作ワークフローの統合テスト"""
        # UIモック
        mock_ui = MagicMock()

        # FileOperationsComponents使用
        components = FileOperationsComponents(mock_ui)

        # 1. ディレクトリ作成
        source_dir = temp_dir / "project"
        components.core.ensure_directory(source_dir)

        # 2. サンプル画像作成
        images_dir = source_dir / "images"
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77kwAAAABJRU5ErkJggg=="
        sample_images = {"logo.png": sample_base64}
        components.core.create_sample_images(images_dir, sample_images)

        # 3. 入力ファイル作成
        input_file = source_dir / "input.md"
        input_file.write_text("# Document\n![Logo](logo.png)")

        # 4. 画像ノードモック作成
        image_node = MagicMock()
        image_node.type = "image"
        image_node.content = "logo.png"
        ast = [image_node]

        # 5. 画像コピー実行
        output_dir = temp_dir / "output"
        components.core.copy_images(input_file, output_dir, ast)

        # 6. 結果検証
        assert (output_dir / "images" / "logo.png").exists()

        # 7. プレビューファイル検索
        preview_file = components.core.find_preview_file(output_dir)
        assert preview_file is None  # プレビューファイルは作成されていない

        # UIメソッドが適切に呼ばれたことを確認
        mock_ui.file_copied.assert_called_once()

    @pytest.mark.integration
    def test_backward_compatibility_integration(self, temp_dir):
        """後方互換性の統合テスト"""
        # 統合インターフェースのFileOperations使用
        file_ops = FileOperations()

        # 委譲メソッドが正常に動作することを確認
        test_file = temp_dir / "test.txt"
        test_content = "Test content for compatibility"

        # FileIOHandlerメソッド使用（staticメソッドとして呼び出し）
        FileOperations.write_text_file(test_file, test_content)
        read_content = FileOperations.read_text_file(test_file)

        assert read_content == test_content

        # FilePathUtilitiesメソッド使用（staticメソッドとして呼び出し）
        size_info = FileOperations.get_file_size_info(test_file)
        assert size_info["size_bytes"] > 0
        assert size_info["size_mb"] > 0

    @pytest.mark.integration
    def test_error_handling_integration(self, temp_dir):
        """エラーハンドリングの統合テスト"""
        mock_ui = MagicMock()
        file_ops = FileOperationsCore(mock_ui)

        # 存在しないディレクトリでの画像コピー
        nonexistent_input = temp_dir / "nonexistent" / "input.txt"
        output_dir = temp_dir / "output"

        image_node = MagicMock()
        image_node.type = "image"
        image_node.content = "missing.png"
        ast = [image_node]

        # エラーが適切に処理されることを確認
        file_ops.copy_images(nonexistent_input, output_dir, ast)

        # 警告が出力されることを確認
        mock_ui.warning.assert_called()


class TestFileOperationsRegression:
    """回帰テスト"""

    def test_file_operations_docstring_regression(self):
        """ファイル操作モジュールのドキュメント文字列回帰テスト"""
        from kumihan_formatter.core import file_operations

        # 基本的なドキュメント情報が含まれていることを確認
        assert file_operations.__doc__ is not None
        docstring = file_operations.__doc__
        assert "分割された各コンポーネントを統合" in docstring
        assert "後方互換性を確保" in docstring
        assert "Issue #492 Phase 5A" in docstring

    def test_import_structure_regression(self):
        """インポート構造の回帰テスト"""
        # 主要コンポーネントがインポート可能であることを確認
        try:
            from kumihan_formatter.core.file_operations import (
                FileIOHandler,
                FileOperations,
                FileOperationsCore,
                FilePathUtilities,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"必要なコンポーネントのインポートに失敗: {e}")

    def test_method_signature_regression(self):
        """メソッドシグネチャの回帰テスト"""
        # FileOperationsCoreの主要メソッドのシグネチャチェック
        import inspect

        core = FileOperationsCore()

        # copy_imagesメソッドのシグネチャ確認
        copy_images_sig = inspect.signature(core.copy_images)
        expected_params = ["input_path", "output_path", "ast"]
        actual_params = list(copy_images_sig.parameters.keys())
        assert actual_params == expected_params

        # check_large_file_warningメソッドのシグネチャ確認
        check_warning_sig = inspect.signature(core.check_large_file_warning)
        warning_params = list(check_warning_sig.parameters.keys())
        assert "path" in warning_params
        assert "max_size_mb" in warning_params

    @pytest.mark.performance
    def test_performance_regression(self, tmp_path):
        """パフォーマンス回帰テスト"""
        import time

        # 大量のファイル処理のパフォーマンステスト
        source_dir = tmp_path / "perf_source"
        source_dir.mkdir()
        dest_dir = tmp_path / "perf_dest"

        # 100個のテストファイル作成
        for i in range(100):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        start_time = time.time()

        copied, excluded = FileOperationsCore.copy_directory_with_exclusions(
            source_dir, dest_dir, []
        )

        elapsed_time = time.time() - start_time

        # 結果検証
        assert copied == 100
        assert excluded == 0

        # パフォーマンス要件（100ファイルを5秒以内で処理）
        assert elapsed_time < 5.0, f"処理時間が遅すぎます: {elapsed_time:.3f}秒"
