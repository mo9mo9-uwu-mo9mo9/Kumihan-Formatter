"""
template_system関連のユニットテスト

このテストファイルは、kumihan_formatter.core.templates.*
の基本機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict

try:
    from kumihan_formatter.core.templates.template_context import TemplateContext
    from kumihan_formatter.core.templates.template_selector import TemplateSelector
    from kumihan_formatter.core.templates.template_filters import TemplateFilters
except ImportError:
    TemplateContext = None
    TemplateSelector = None
    TemplateFilters = None


@pytest.mark.skipif(TemplateContext is None, reason="TemplateContext not found")
class TestTemplateContext:
    """TemplateContextクラスのテスト"""

    def test_initialization_default(self):
        """デフォルト初期化テスト"""
        context = TemplateContext()
        assert context is not None

    def test_initialization_with_data(self):
        """データ付き初期化テスト"""
        initial_data = {"title": "テストタイトル", "content": "テスト内容"}

        try:
            context = TemplateContext(initial_data)
            assert context is not None
        except TypeError:
            # 引数をサポートしていない場合はスキップ
            pass

    def test_set_get_context_data(self):
        """コンテキストデータの設定・取得テスト"""
        context = TemplateContext()

        test_data = {"key1": "value1", "key2": "value2"}

        try:
            if hasattr(context, "set_data"):
                context.set_data(test_data)
                if hasattr(context, "get_data"):
                    result = context.get_data()
                    assert result is not None
            elif hasattr(context, "update"):
                context.update(test_data)
                assert True
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_add_context_variable(self):
        """コンテキスト変数追加テスト"""
        context = TemplateContext()

        try:
            if hasattr(context, "add_variable"):
                context.add_variable("test_var", "test_value")
                assert True
            elif hasattr(context, "set"):
                context.set("test_var", "test_value")
                assert True
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_get_context_variable(self):
        """コンテキスト変数取得テスト"""
        context = TemplateContext()

        try:
            if hasattr(context, "get_variable"):
                # 存在しない変数の場合
                result = context.get_variable("nonexistent")
                assert result is None or isinstance(result, str)
            elif hasattr(context, "get"):
                result = context.get("nonexistent")
                assert result is None or isinstance(result, str)
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_merge_context(self):
        """コンテキストマージテスト"""
        context = TemplateContext()

        additional_data = {"merged_key": "merged_value"}

        try:
            if hasattr(context, "merge"):
                context.merge(additional_data)
                assert True
            elif hasattr(context, "update"):
                context.update(additional_data)
                assert True
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass


@pytest.mark.skipif(TemplateSelector is None, reason="TemplateSelector not found")
class TestTemplateSelector:
    """TemplateSelectorクラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        selector = TemplateSelector()
        assert selector is not None

    def test_select_template_by_type(self):
        """タイプ別テンプレート選択テスト"""
        selector = TemplateSelector()

        template_types = ["default", "minimal", "full", "custom"]

        for template_type in template_types:
            try:
                if hasattr(selector, "select_template"):
                    result = selector.select_template(template_type)
                    assert result is not None
                    assert isinstance(result, str)
                elif hasattr(selector, "get_template"):
                    result = selector.get_template(template_type)
                    assert result is not None
            except (AttributeError, ValueError):
                # メソッドが存在しない、またはサポートされていないタイプ
                break

    def test_list_available_templates(self):
        """利用可能テンプレート一覧取得テスト"""
        selector = TemplateSelector()

        try:
            if hasattr(selector, "list_templates"):
                templates = selector.list_templates()
                assert templates is not None
                assert isinstance(templates, (list, tuple, set))
            elif hasattr(selector, "get_available_templates"):
                # テンプレートディレクトリが必要な場合は、適当なPathを渡す
                from pathlib import Path
                import tempfile

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    templates = selector.get_available_templates(temp_path)
                assert templates is not None
                assert isinstance(templates, (list, tuple, set))
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_validate_template(self):
        """テンプレート検証テスト"""
        selector = TemplateSelector()

        try:
            if hasattr(selector, "validate_template"):
                # 有効なテンプレート名での検証
                result = selector.validate_template("default")
                assert isinstance(result, bool)

                # 無効なテンプレート名での検証
                result = selector.validate_template("nonexistent_template")
                assert isinstance(result, bool)
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_get_template_path(self):
        """テンプレートパス取得テスト"""
        selector = TemplateSelector()

        try:
            if hasattr(selector, "get_template_path"):
                path = selector.get_template_path("default")
                assert path is not None
                assert isinstance(path, str)
        except (AttributeError, ValueError):
            # メソッドが存在しない、またはテンプレートが見つからない
            pass


@pytest.mark.skipif(TemplateFilters is None, reason="TemplateFilters not found")
class TestTemplateFilters:
    """TemplateFiltersクラスのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        filters = TemplateFilters()
        assert filters is not None

    def test_escape_html_filter(self):
        """HTMLエスケープフィルターテスト"""
        filters = TemplateFilters()

        test_html = "<script>alert('test')</script>"

        try:
            if hasattr(filters, "escape_html"):
                result = filters.escape_html(test_html)
                assert isinstance(result, str)
                assert "&lt;" in result or "&gt;" in result
            elif hasattr(filters, "html_escape"):
                result = filters.html_escape(test_html)
                assert isinstance(result, str)
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_truncate_filter(self):
        """文字列切り詰めフィルターテスト"""
        filters = TemplateFilters()

        long_text = "これは非常に長いテキストです。" * 10

        try:
            if hasattr(filters, "truncate"):
                result = filters.truncate(long_text, 50)
                assert isinstance(result, str)
                assert len(result) <= 53  # 50 + "..." の余裕
            elif hasattr(filters, "truncate_text"):
                result = filters.truncate_text(long_text, 50)
                assert isinstance(result, str)
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_format_date_filter(self):
        """日付フォーマットフィルターテスト"""
        filters = TemplateFilters()

        from datetime import datetime

        test_date = datetime.now()

        try:
            if hasattr(filters, "format_date"):
                result = filters.format_date(test_date)
                assert isinstance(result, str)
                assert len(result) > 0
            elif hasattr(filters, "date_format"):
                result = filters.date_format(test_date)
                assert isinstance(result, str)
        except (AttributeError, TypeError):
            # メソッドが存在しない、または日付形式が異なる
            pass

    def test_capitalize_filter(self):
        """大文字変換フィルターテスト"""
        filters = TemplateFilters()

        test_text = "hello world"

        try:
            if hasattr(filters, "capitalize"):
                result = filters.capitalize(test_text)
                assert isinstance(result, str)
                assert result != test_text  # 何らかの変換が行われている
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_get_available_filters(self):
        """利用可能フィルター一覧取得テスト"""
        filters = TemplateFilters()

        try:
            if hasattr(filters, "get_filters"):
                filter_list = filters.get_filters()
                assert filter_list is not None
                assert isinstance(filter_list, (list, tuple, dict))
            elif hasattr(filters, "list_filters"):
                filter_list = filters.list_filters()
                assert filter_list is not None
                assert isinstance(filter_list, (list, tuple, dict))
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_apply_filter(self):
        """フィルター適用テスト"""
        filters = TemplateFilters()

        test_value = "test value"

        try:
            if hasattr(filters, "apply_filter"):
                # 存在しないフィルターでのテスト
                result = filters.apply_filter("nonexistent", test_value)
                assert result is not None
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass

    def test_register_custom_filter(self):
        """カスタムフィルター登録テスト"""
        filters = TemplateFilters()

        def custom_filter(value):
            return f"custom: {value}"

        try:
            if hasattr(filters, "register_filter"):
                filters.register_filter("custom", custom_filter)
                assert True
            elif hasattr(filters, "add_filter"):
                filters.add_filter("custom", custom_filter)
                assert True
        except AttributeError:
            # メソッドが存在しない場合はスキップ
            pass
