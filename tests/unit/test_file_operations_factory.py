"""FileOperationsFactory の遅延初期化テスト"""

from kumihan_formatter.core.utilities.file_operations_factory import (
    FileOperationsComponents,
)


def test_lazy_initialization():
    comp = FileOperationsComponents()
    # いずれも初期化前はNoneのはず（内部）
    assert comp._core is None
    assert comp._path_utils is None
    assert comp._io_handler is None

    # アクセス時に遅延初期化
    core = comp.core
    path = comp.path_utils
    io = comp.io_handler

    assert core is not None
    assert path is not None
    assert io is not None
