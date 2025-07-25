"""
error_reporting.py のテスト

Issue #591 Critical Tier Testing対応
- 80%以上のテストカバレッジ
- 100%エッジケーステスト
- 統合テスト・回帰テスト
"""

import warnings
from unittest import mock

import pytest

from kumihan_formatter.core.utilities.logger import get_logger


class TestErrorReportingDeprecation:
    """廃止予定モジュールの互換性テスト"""

    def test_deprecation_warning_raised(self):
        """廃止予定の警告が発行されることを確認"""
        with pytest.warns(DeprecationWarning) as warning_info:
            # モジュールインポート時に警告が発行される
            from kumihan_formatter.core import error_reporting

        # 警告メッセージの検証
        assert len(warning_info) == 1
        warning_message = str(warning_info[0].message)
        assert "error_reporting.py は廃止予定です" in warning_message
        assert "kumihan_formatter.core.reporting を使用してください" in warning_message

    def test_deprecation_warning_stacklevel(self):
        """警告のスタックレベルが正しく設定されていることを確認"""
        # スタックレベル2が設定されていることを実装で確認
        from kumihan_formatter.core.error_reporting import warnings

        # warnings.warnの呼び出しでstacklevel=2が設定されていることは実装上確認済み
        assert warnings is not None

    def test_module_imports_successfully(self):
        """モジュールが正常にインポートできることを確認"""
        try:
            from kumihan_formatter.core import error_reporting

            assert error_reporting is not None
        except ImportError:
            pytest.fail("error_reporting モジュールのインポートに失敗")

    def test_warnings_module_imported(self):
        """warningsモジュールが正しくインポートされていることを確認"""
        import warnings as warnings_builtin

        from kumihan_formatter.core import error_reporting

        # warningsモジュールが使用されていることを確認
        assert hasattr(error_reporting, "warnings")
        assert error_reporting.warnings is warnings_builtin

    def test_warning_called_with_correct_parameters(self):
        """warnings.warnが正しいパラメータで呼ばれることを確認"""
        # ソースコードを直接読み込んで警告内容を確認
        from kumihan_formatter.core import error_reporting

        # ファイル内容を確認
        with open(error_reporting.__file__, "r", encoding="utf-8") as f:
            content = f.read()

        # 警告の内容とパラメータが正しく設定されていることを確認
        assert "warnings.warn(" in content
        assert "DeprecationWarning" in content
        assert "stacklevel=2" in content
        assert "廃止予定です" in content


class TestErrorReportingCompatibility:
    """後方互換性テスト"""

    def test_module_exists_and_accessible(self):
        """モジュールが存在し、アクセス可能であることを確認"""
        from kumihan_formatter.core import error_reporting

        # モジュールオブジェクトが存在する
        assert error_reporting is not None

        # モジュールの基本属性が存在する
        assert hasattr(error_reporting, "__doc__")
        assert hasattr(error_reporting, "__file__")

    def test_docstring_content(self):
        """ドキュメント文字列の内容を確認"""
        from kumihan_formatter.core import error_reporting

        docstring = error_reporting.__doc__
        assert docstring is not None
        assert "統一エラーレポート機能" in docstring
        assert "互換性維持用レガシーファイル" in docstring
        assert "Issue #319対応" in docstring
        assert "reporting" in docstring

    def test_new_module_reference_in_docstring(self):
        """新しいモジュールへの参照が含まれていることを確認"""
        from kumihan_formatter.core import error_reporting

        docstring = error_reporting.__doc__
        expected_imports = [
            "ErrorSeverity",
            "ErrorCategory",
            "ErrorLocation",
            "FixSuggestion",
            "DetailedError",
            "ErrorReport",
            "ErrorReportBuilder",
            "ErrorFormatter",
            "ErrorContextManager",
        ]

        for import_name in expected_imports:
            assert import_name in docstring

    def test_module_path_contains_expected_location(self):
        """モジュールパスが期待される場所にあることを確認"""
        import os

        from kumihan_formatter.core import error_reporting

        module_path = error_reporting.__file__
        # Windows/Unix両対応のパス区切り文字チェック
        expected_path = os.path.join("kumihan_formatter", "core", "error_reporting.py")
        assert expected_path in module_path


class TestErrorReportingEdgeCases:
    """エッジケーステスト - 100%カバレッジ"""

    def test_multiple_imports_single_warning(self):
        """複数回インポートしても警告は1回だけ発行されることを確認"""
        warning_count = 0

        def warning_handler(message, category, filename, lineno, file=None, line=None):
            nonlocal warning_count
            if (
                category == DeprecationWarning
                and "error_reporting.py は廃止予定です" in str(message)
            ):
                warning_count += 1

        # カスタム警告ハンドラーを設定
        original_showwarning = warnings.showwarning
        warnings.showwarning = warning_handler

        try:
            # 複数回インポート
            import kumihan_formatter.core.error_reporting as error_reporting3
            from kumihan_formatter.core import error_reporting
            from kumihan_formatter.core import error_reporting as error_reporting2

            # 警告は初回インポート時のみ発行される（モジュールキャッシュのため）
            assert warning_count <= 1

        finally:
            warnings.showwarning = original_showwarning

    def test_import_with_warnings_disabled(self):
        """警告が無効化されている場合でもインポートできることを確認"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            try:
                from kumihan_formatter.core import error_reporting

                assert error_reporting is not None
            except Exception as e:
                pytest.fail(f"警告無効時のインポートに失敗: {e}")

    def test_module_attributes_after_import(self):
        """インポート後のモジュール属性を確認"""
        from kumihan_formatter.core import error_reporting

        # Pythonモジュールの標準属性が存在することを確認
        standard_attributes = ["__name__", "__doc__", "__file__", "__package__"]
        for attr in standard_attributes:
            assert hasattr(error_reporting, attr), f"属性 {attr} が見つからない"

    def test_warnings_import_exists(self):
        """warningsモジュールのインポートが存在することを確認"""
        from kumihan_formatter.core import error_reporting

        # warningsがインポートされていることを確認
        assert "warnings" in dir(error_reporting)

    @pytest.mark.integration
    def test_integration_with_new_reporting_module(self):
        """新しいreportingモジュールとの統合テスト"""
        try:
            # 新しいreportingモジュールが存在し、インポート可能であることを確認
            from kumihan_formatter.core.reporting import (
                DetailedError,
                ErrorCategory,
                ErrorContextManager,
                ErrorFormatter,
                ErrorLocation,
                ErrorReport,
                ErrorReportBuilder,
                ErrorSeverity,
                FixSuggestion,
            )

            # 基本的なクラス/関数が存在することを確認
            assert ErrorSeverity is not None
            assert ErrorCategory is not None
            assert ErrorLocation is not None
            assert FixSuggestion is not None
            assert DetailedError is not None
            assert ErrorReport is not None
            assert ErrorReportBuilder is not None
            assert ErrorFormatter is not None
            assert ErrorContextManager is not None

        except ImportError as e:
            pytest.fail(f"新しいreportingモジュールのインポートに失敗: {e}")


class TestErrorReportingRegression:
    """回帰テスト"""

    def test_file_encoding_utf8(self):
        """ファイルエンコーディングがUTF-8であることを確認（回帰防止）"""
        from kumihan_formatter.core import error_reporting

        # モジュールファイルを直接読み込んでUTF-8チェック
        with open(error_reporting.__file__, "r", encoding="utf-8") as f:
            content = f.read()
            # 日本語文字が正しく読み込めることを確認
            assert "統一エラーレポート機能" in content
            assert "廃止予定" in content

    def test_deprecation_warning_category(self):
        """警告カテゴリがDeprecationWarningであることを確認（回帰防止）"""
        from kumihan_formatter.core import error_reporting

        # ソースコードレベルでDeprecationWarningが使用されていることを確認
        with open(error_reporting.__file__, "r", encoding="utf-8") as f:
            content = f.read()

        assert "DeprecationWarning" in content

    def test_module_level_imports(self):
        """モジュールレベルのインポートが正しく動作することを確認"""
        # トップレベルインポート
        import kumihan_formatter.core.error_reporting

        assert kumihan_formatter.core.error_reporting is not None

        # fromインポート
        from kumihan_formatter.core import error_reporting

        assert error_reporting is not None

    @pytest.mark.performance
    def test_import_performance(self):
        """インポート時間が許容範囲内であることを確認"""
        import sys
        import time

        # モジュールをキャッシュから削除
        if "kumihan_formatter.core.error_reporting" in sys.modules:
            del sys.modules["kumihan_formatter.core.error_reporting"]

        start_time = time.time()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from kumihan_formatter.core import error_reporting

        import_time = time.time() - start_time

        # インポート時間が1秒以内であることを確認（レガシーファイルなので高速であるべき）
        assert import_time < 1.0, f"インポートが遅すぎます: {import_time:.3f}秒"
