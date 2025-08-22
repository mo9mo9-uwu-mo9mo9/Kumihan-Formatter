"""
最適化済み属性パーサーテスト - Issue #1113 大幅削減対応

属性パーサー機能を効率的にテスト：
- HTML属性抽出/解析
- CSS・スタイル処理
- データ属性処理
- カラー・サイズ・スタイル属性
- バリデーション・エラーハンドリング

削減前: 28メソッド/649行 → 削減後: 8メソッド/220行
"""

from typing import Any, Dict
import pytest

from kumihan_formatter.core.parsing.keyword.attribute_parser import AttributeParser


class TestAttributeParserCore:
    """属性パーサーコア機能統合テスト"""

    @pytest.fixture
    def parser(self):
        """パーサーインスタンス"""
        return AttributeParser()

    @pytest.mark.parametrize("input_content,expected_attrs", [
        # 基本HTML属性
        ('class="test" id="sample"', {"class": "test", "id": "sample"}),
        ('title="ツールチップ"', {"title": "ツールチップ"}),

        # 複数クラス・引用符なし
        ('class="btn btn-primary"', {"class": "btn"}),
        ('class=test id=sample', {"class": "test", "id": "sample"}),

        # データ属性
        ('data-toggle="tooltip" data-placement="top"',
         {"data-toggle": "tooltip", "data-placement": "top"}),
        ('data-config=\'{"theme": "dark"}\'', {"data-config": '{"theme": "dark"}'}),

        # ARIA属性
        ('aria-label="閉じる" aria-hidden="true"',
         {"aria-label": "閉じる", "aria-hidden": "true"}),

        # スタイル属性
        ('style="color: red; font-size: 16px;"', {"style": "color: red; font-size: 16px;"}),
        ('style="background: linear-gradient(45deg, red, blue);"',
         {"style": "background: linear-gradient(45deg, red, blue);"}),
    ])
    def test_attribute_parsing_comprehensive(self, parser, input_content, expected_attrs):
        """HTML属性解析統合テスト"""
        result = parser.parse_attributes_from_content(input_content)
        for key, expected_value in expected_attrs.items():
            assert key in result
            assert result[key] == expected_value

    @pytest.mark.parametrize("color_input,expected_valid,expected_invalid", [
        # 有効な色属性
        ("#FF0000", "#FF0000", ""),
        ("rgb(255, 0, 0)", "rgb(255, 0, 0)", ""),
        ("rgba(255, 0, 0, 0.5)", "rgba(255, 0, 0, 0.5)", ""),

        # 無効な色属性
        ("red", "", "red"),
        ("invalid_color", "", "invalid_color"),
    ])
    def test_color_attribute_extraction(self, parser, color_input, expected_valid, expected_invalid):
        """色属性抽出統合テスト"""
        valid, invalid = parser.extract_color_attribute(color_input)
        assert valid == expected_valid
        assert invalid == expected_invalid

    @pytest.mark.parametrize("size_input,expected_result", [
        # 有効サイズ
        ("[size:16px]", "16px"),
        ("[size:1.5em]", "1.5em"),
        ("[size:120%]", "120%"),
        ("[size:large]", "large"),

        # 無効サイズ（属性なし）
        ("[size:invalid]", None),
    ])
    def test_size_attribute_extraction(self, parser, size_input, expected_result):
        """サイズ属性抽出統合テスト"""
        attributes = parser._extract_size_attributes(size_input)
        if expected_result is None:
            assert "size" not in attributes
        else:
            assert attributes.get("size") == expected_result

    @pytest.mark.parametrize("style_input,expected_result", [
        # 有効スタイル
        ("[style:bold]", "bold"),
        ("[style:italic]", "italic"),
        ("[style:uppercase]", "uppercase"),

        # 無効スタイル（属性なし）
        ("[style:invalid]", None),
    ])
    def test_style_attribute_extraction(self, parser, style_input, expected_result):
        """スタイル属性抽出統合テスト"""
        attributes = parser._extract_style_attributes(style_input)
        if expected_result is None:
            assert "style" not in attributes
        else:
            assert attributes.get("style") == expected_result

    @pytest.mark.parametrize("size_value,is_valid", [
        # 有効サイズ
        ("16px", True), ("1.5em", True), ("2rem", True), ("100%", True),
        ("12pt", True), ("50vh", True), ("30vw", True),
        ("small", True), ("medium", True), ("large", True), ("x-large", True),

        # 無効サイズ
        ("16", False), ("px", False), ("invalid", False), ("", False),
        ("16 px", False), ("1.5em!", False),

        # 非文字列
        (123, False), (None, False),
    ])
    def test_size_value_validation(self, parser, size_value, is_valid):
        """サイズ値バリデーション統合テスト"""
        assert parser._is_valid_size_value(size_value) == is_valid

    @pytest.mark.parametrize("style_value,is_valid", [
        # 有効スタイル
        ("normal", True), ("italic", True), ("bold", True), ("underline", True),
        ("strikethrough", True), ("uppercase", True), ("lowercase", True),
        ("BOLD", True),  # 大文字小文字不問

        # 無効スタイル
        ("invalid", False), ("blink", False), ("", False),
        ("bold italic", False), ("under_line", False),

        # 非文字列
        (123, False), (None, False),
    ])
    def test_style_value_validation(self, parser, style_value, is_valid):
        """スタイル値バリデーション統合テスト"""
        assert parser._is_valid_style_value(style_value) == is_valid

    @pytest.mark.parametrize("color_input,expected", [
        # 有効16進色（小文字変換）
        ("#FF0000", "#ff0000"), ("#F00", "#f00"),

        # 有効色名（小文字変換）
        ("RED", "red"), ("green", "green"), ("Blue", "blue"),

        # サポート色名
        ("yellow", "yellow"), ("orange", "orange"), ("purple", "purple"),
        ("pink", "pink"), ("brown", "brown"), ("black", "black"),
        ("white", "white"), ("gray", "gray"), ("grey", "grey"),
        ("cyan", "cyan"), ("magenta", "magenta"),

        # 無効色値
        ("invalid", ""), ("#GGG", ""), ("#12345", ""),
        ("javascript:alert()", ""), ("<script>", ""),
        ("crimson", ""),  # 非サポート色名

        # 非文字列
        (123, ""), (None, ""),
    ])
    def test_color_sanitization(self, parser, color_input, expected):
        """色属性サニタイゼーション統合テスト"""
        result = parser._sanitize_color_attribute(color_input)
        assert result == expected

    @pytest.mark.parametrize("test_input,expected_behavior", [
        # 空・null値処理
        ("", {}), (None, {}), ([], {}), ("   ", {}), ("\t\n", {}),

        # Unicode値処理
        ('title="日本語タイトル"', {"title": "日本語タイトル"}),
        ('data-emoji="🚀🌟"', {"data-emoji": "🚀🌟"}),
        ('data-symbol="©®™"', {"data-symbol": "©®™"}),

        # 特殊文字処理
        ('data-url="https%3A//example.com"', {"data-url": "https%3A//example.com"}),
        ('data-content="SGVsbG8gV29ybGQ="', {"data-content": "SGVsbG8gV29ybGQ="}),

        # HTML実体参照・エスケープ
        ('title="&lt;script&gt;"', {"title": "&lt;script&gt;"}),
        ('data-text="He said &quot;Hello&quot;"', {"data-text": "He said &quot;Hello&quot;"}),
    ])
    def test_edge_cases_and_validation(self, parser, test_input, expected_behavior):
        """エッジケース・バリデーション統合テスト"""
        if isinstance(expected_behavior, dict):
            # 正常な属性解析
            result = parser.parse_attributes_from_content(test_input)
            for key, expected_value in expected_behavior.items():
                assert key in result
                assert result[key] == expected_value
        else:
            # エラー系テスト（色属性など）
            if hasattr(parser, 'extract_color_attribute'):
                result = parser.extract_color_attribute(test_input)
                assert result == ("", test_input)  # 無効値として扱われる
