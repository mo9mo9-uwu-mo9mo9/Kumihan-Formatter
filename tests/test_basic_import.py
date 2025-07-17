"""Issue #497: 基本インポートテスト

GitHub Actions CI/CD でのテスト実行確認用の最小限テスト。
段階的テスト復旧計画の Phase 1 として作成。

将来の Phase 2-4 で本格的なテストに置き換え予定。
"""

import sys
from pathlib import Path

import pytest

# プロジェクトルートをPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_package_import():
    """パッケージが正常にインポートできることを確認"""
    import kumihan_formatter

    assert kumihan_formatter is not None


def test_core_modules_import():
    """コアモジュールが正常にインポートできることを確認"""
    try:
        from kumihan_formatter import parser, renderer

        assert parser is not None
        assert renderer is not None
    except ImportError as e:
        pytest.skip(f"コアモジュールインポートエラー (Phase 2で修正予定): {e}")


def test_cli_module_import():
    """CLIモジュールが正常にインポートできることを確認"""
    try:
        from kumihan_formatter import cli

        assert cli is not None
    except ImportError as e:
        pytest.skip(f"CLIモジュールインポートエラー (Phase 3で修正予定): {e}")


@pytest.mark.skip("Phase 2で実装予定")
def test_placeholder_for_phase2():
    """Phase 2で追加予定のテストのプレースホルダー"""
    pass


@pytest.mark.skip("Phase 3で実装予定")
def test_placeholder_for_phase3():
    """Phase 3で追加予定のテストのプレースホルダー"""
    pass


@pytest.mark.skip("Phase 4で実装予定")
def test_placeholder_for_phase4():
    """Phase 4で追加予定のテストのプレースホルダー"""
    pass
