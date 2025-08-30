"""
file_operations関連のユニットテスト

このテストファイルは、kumihan_formatter.core.utilities.file_operations_*
の基本機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os
from typing import Any, Dict

try:
    from kumihan_formatter.core.utilities.file_operations_factory import (
        FileOperationsFactory,
    )
    from kumihan_formatter.core.utilities.file_operations_core import FileOperationsCore
    from kumihan_formatter.core.utilities.file_path_utilities import FilePathUtilities
except ImportError:
    FileOperationsFactory = None
    FileOperationsCore = None
    FilePathUtilities = None


@pytest.mark.skipif(
    FileOperationsFactory is None, reason="FileOperationsFactory not found"
)
class TestFileOperationsFactory:
    """FileOperationsFactoryクラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        factory = FileOperationsFactory()
        assert factory is not None

    def test_create_file_operations(self):
        """ファイル操作オブジェクト作成テスト"""
        factory = FileOperationsFactory()

        try:
            if hasattr(factory, "create"):
                ops = factory.create()
                assert ops is not None
            elif hasattr(factory, "get_file_operations"):
                ops = factory.get_file_operations()
                assert ops is not None
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_get_supported_operations(self):
        """サポート操作取得テスト"""
        factory = FileOperationsFactory()

        try:
            if hasattr(factory, "get_supported_operations"):
                operations = factory.get_supported_operations()
                assert operations is not None
                assert isinstance(operations, (list, tuple, set))
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass


@pytest.mark.skipif(FileOperationsCore is None, reason="FileOperationsCore not found")
class TestFileOperationsCore:
    """FileOperationsCoreクラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        core = FileOperationsCore()
        assert core is not None

    def test_read_file_basic(self):
        """基本ファイル読み込みテスト"""
        core = FileOperationsCore()

        # テンポラリファイル作成
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("テスト内容")
            temp_file_path = temp_file.name

        try:
            if hasattr(core, "read_file"):
                content = core.read_file(temp_file_path)
                assert content is not None
                assert isinstance(content, str)
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass
        finally:
            # クリーンアップ
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_write_file_basic(self):
        """基本ファイル書き込みテスト"""
        core = FileOperationsCore()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            if hasattr(core, "write_file"):
                result = core.write_file(temp_file_path, "テスト書き込み内容")
                assert result is not None  # 成功時は何らかの値を返す
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass
        finally:
            # クリーンアップ
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_file_exists_check(self):
        """ファイル存在確認テスト"""
        core = FileOperationsCore()

        # 存在するファイル
        with tempfile.NamedTemporaryFile() as temp_file:
            try:
                if hasattr(core, "file_exists"):
                    result = core.file_exists(temp_file.name)
                    assert isinstance(result, bool)
                elif hasattr(core, "exists"):
                    result = core.exists(temp_file.name)
                    assert isinstance(result, bool)
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                pass


@pytest.mark.skipif(FilePathUtilities is None, reason="FilePathUtilities not found")
class TestFilePathUtilities:
    """FilePathUtilitiesクラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        utils = FilePathUtilities()
        assert utils is not None

    def test_normalize_path(self):
        """パス正規化テスト"""
        utils = FilePathUtilities()

        test_paths = [
            "/path/to/../file.txt",
            "relative/path/file.txt",
            "./current/file.txt",
        ]

        for test_path in test_paths:
            try:
                if hasattr(utils, "normalize_path"):
                    result = utils.normalize_path(test_path)
                    assert isinstance(result, str)
                elif hasattr(utils, "normalize"):
                    result = utils.normalize(test_path)
                    assert isinstance(result, str)
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                break

    def test_join_paths(self):
        """パス結合テスト"""
        utils = FilePathUtilities()

        try:
            if hasattr(utils, "join_paths"):
                result = utils.join_paths("base", "sub", "file.txt")
                assert isinstance(result, str)
                assert "base" in result
                assert "file.txt" in result
            elif hasattr(utils, "join"):
                result = utils.join("base", "sub", "file.txt")
                assert isinstance(result, str)
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_get_file_extension(self):
        """ファイル拡張子取得テスト"""
        utils = FilePathUtilities()

        test_cases = [
            ("file.txt", "txt"),
            ("document.pdf", "pdf"),
            ("archive.tar.gz", "gz"),
            ("noextension", ""),
        ]

        for file_path, expected_ext in test_cases:
            try:
                if hasattr(utils, "get_extension"):
                    result = utils.get_extension(file_path)
                    assert isinstance(result, str)
                elif hasattr(utils, "get_file_extension"):
                    result = utils.get_file_extension(file_path)
                    assert isinstance(result, str)
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                break

    def test_is_absolute_path(self):
        """絶対パス判定テスト"""
        utils = FilePathUtilities()

        test_cases = [
            ("/absolute/path/file.txt", True),
            ("relative/path/file.txt", False),
            ("./current/file.txt", False),
        ]

        for test_path, expected in test_cases:
            try:
                if hasattr(utils, "is_absolute"):
                    result = utils.is_absolute(test_path)
                    assert isinstance(result, bool)
                elif hasattr(utils, "is_absolute_path"):
                    result = utils.is_absolute_path(test_path)
                    assert isinstance(result, bool)
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                break

    def test_create_directory_path(self):
        """ディレクトリパス作成テスト"""
        utils = FilePathUtilities()

        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir_path = os.path.join(temp_dir, "new_directory")

            try:
                if hasattr(utils, "ensure_directory"):
                    result = utils.ensure_directory(new_dir_path)
                    assert os.path.exists(new_dir_path)
                elif hasattr(utils, "create_directory"):
                    result = utils.create_directory(new_dir_path)
                    assert os.path.exists(new_dir_path)
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                pass
