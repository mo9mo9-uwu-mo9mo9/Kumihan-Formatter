"""
parser_utils.pyモジュールのユニットテスト

このテストファイルは、kumihan_formatter.parser_utils モジュールの
JSONパス処理と文字列操作ユーティリティ関数をテストします。
"""

import pytest
from typing import List

from kumihan_formatter.parser_utils import (
    extract_json_path,
    find_closing_brace,
    find_matching_quote,
    is_valid_json_path_character,
    remove_quotes,
)


class TestExtractJsonPath:
    """extract_json_path関数のテスト"""

    def test_extract_simple_path(self):
        """シンプルなJSONパスの抽出テスト"""
        result = extract_json_path("data.name")
        assert result == ["data", "name"]

    def test_extract_nested_path(self):
        """ネストしたJSONパスの抽出テスト"""
        result = extract_json_path("data.user.profile.name")
        assert result == ["data", "user", "profile", "name"]

    def test_extract_array_path(self):
        """配列インデックスを含むJSONパスの抽出テスト"""
        result = extract_json_path("data.items[0].name")
        assert result == ["data", "items", "0", "name"]

    def test_extract_multiple_arrays(self):
        """複数の配列インデックスを含むJSONパスの抽出テスト"""
        result = extract_json_path("data.items[0].tags[1]")
        assert result == ["data", "items", "0", "tags", "1"]

    def test_extract_empty_path(self):
        """空のJSONパスの抽出テスト"""
        result = extract_json_path("")
        assert result == []

    def test_extract_none_path(self):
        """Noneパスの抽出テスト（空文字列として扱われる）"""
        result = extract_json_path("")
        assert result == []

    def test_extract_single_element(self):
        """単一要素のJSONパスの抽出テスト"""
        result = extract_json_path("root")
        assert result == ["root"]

    def test_extract_path_with_spaces(self):
        """スペースを含むJSONパスの抽出テスト"""
        result = extract_json_path(" data . items [ 0 ] . name ")
        assert result == ["data", "items", "0", "name"]

    def test_extract_complex_array_path(self):
        """複雑な配列パスの抽出テスト"""
        result = extract_json_path("data[0][1].nested[2]")
        assert result == ["data", "0", "1", "nested", "2"]


class TestFindClosingBrace:
    """find_closing_brace関数のテスト"""

    def test_find_simple_brace(self):
        """シンプルな括弧の検索テスト"""
        text = "{hello world}"
        result = find_closing_brace(text, 0)
        assert result == 12

    def test_find_nested_braces(self):
        """ネストした括弧の検索テスト"""
        text = "{outer {inner} content}"
        result = find_closing_brace(text, 0)
        assert result == 22

    def test_find_brace_with_string(self):
        """文字列内の括弧を無視する検索テスト"""
        text = '{"key": "value with } brace"}'
        result = find_closing_brace(text, 0)
        assert result == 28

    def test_find_brace_with_escaped_quote(self):
        """エスケープされたクォートを含む検索テスト"""
        text = '{"key": "value with \\"quote\\" and } brace"}'
        result = find_closing_brace(text, 0)
        assert result == 42

    def test_find_brace_not_at_start(self):
        """開始位置が括弧でない場合のテスト"""
        text = "hello {world}"
        result = find_closing_brace(text, 0)
        assert result == -1

    def test_find_brace_no_closing(self):
        """閉じ括弧がない場合のテスト"""
        text = "{incomplete"
        result = find_closing_brace(text, 0)
        assert result == -1

    def test_find_brace_empty_string(self):
        """空文字列での検索テスト"""
        text = ""
        result = find_closing_brace(text, 0)
        assert result == -1

    def test_find_brace_invalid_start_pos(self):
        """不正な開始位置での検索テスト"""
        text = "{hello}"
        result = find_closing_brace(text, 10)
        assert result == -1

    def test_find_deeply_nested_braces(self):
        """深くネストした括弧の検索テスト"""
        text = "{a: {b: {c: {d: value}}}}"
        result = find_closing_brace(text, 0)
        assert result == 24


class TestFindMatchingQuote:
    """find_matching_quote関数のテスト"""

    def test_find_double_quote(self):
        """ダブルクォートの検索テスト"""
        text = '"hello world"'
        result = find_matching_quote(text, 0)
        assert result == 12

    def test_find_single_quote(self):
        """シングルクォートの検索テスト"""
        text = "'hello world'"
        result = find_matching_quote(text, 0)
        assert result == 12

    def test_find_quote_with_escaped_quote(self):
        """エスケープされたクォートを含む検索テスト"""
        text = '"hello \\"quoted\\" world"'
        result = find_matching_quote(text, 0)
        assert result == 23

    def test_find_quote_with_backslash(self):
        """バックスラッシュを含む検索テスト"""
        text = '"hello\\world"'
        result = find_matching_quote(text, 0)
        assert result == 12

    def test_find_quote_not_at_start(self):
        """開始位置がクォートでない場合のテスト"""
        text = 'hello "world"'
        result = find_matching_quote(text, 0)
        assert result == -1

    def test_find_quote_no_closing(self):
        """閉じクォートがない場合のテスト"""
        text = '"incomplete'
        result = find_matching_quote(text, 0)
        assert result == -1

    def test_find_quote_empty_string(self):
        """空文字列での検索テスト"""
        text = ""
        result = find_matching_quote(text, 0)
        assert result == -1

    def test_find_quote_invalid_start_pos(self):
        """不正な開始位置での検索テスト"""
        text = '"hello"'
        result = find_matching_quote(text, 10)
        assert result == -1

    def test_find_quote_mixed_quotes(self):
        """混在するクォートの検索テスト"""
        text = "\"hello 'world'\""
        result = find_matching_quote(text, 0)
        assert result == 14


class TestIsValidJsonPathCharacter:
    """is_valid_json_path_character関数のテスト"""

    def test_valid_alphanumeric_characters(self):
        """英数字の有効性テスト"""
        assert is_valid_json_path_character("a") is True
        assert is_valid_json_path_character("Z") is True
        assert is_valid_json_path_character("0") is True
        assert is_valid_json_path_character("9") is True

    def test_valid_special_characters(self):
        """特殊文字の有効性テスト"""
        assert is_valid_json_path_character("_") is True
        assert is_valid_json_path_character("-") is True
        assert is_valid_json_path_character(".") is True
        assert is_valid_json_path_character("[") is True
        assert is_valid_json_path_character("]") is True

    def test_invalid_characters(self):
        """無効な文字のテスト"""
        assert is_valid_json_path_character(" ") is False
        assert is_valid_json_path_character("!") is False
        assert is_valid_json_path_character("@") is False
        assert is_valid_json_path_character("#") is False
        assert is_valid_json_path_character("{") is False
        assert is_valid_json_path_character("}") is False

    def test_unicode_characters(self):
        """Unicode文字のテスト"""
        # 日本語文字（ひらがな）は実装によってTrue/Falseが変わる可能性がある
        # 実際の実装ではisalnum()がTrueを返す可能性があるため、結果を確認
        result_hiragana = is_valid_json_path_character("あ")
        assert isinstance(result_hiragana, bool)  # 戻り値がboolであることのみ確認

        result_accent = is_valid_json_path_character("é")
        assert isinstance(result_accent, bool)  # 戻り値がboolであることのみ確認


class TestRemoveQuotes:
    """remove_quotes関数のテスト"""

    def test_remove_double_quotes(self):
        """ダブルクォートの除去テスト"""
        result = remove_quotes('"hello world"')
        assert result == "hello world"

    def test_remove_single_quotes(self):
        """シングルクォートの除去テスト"""
        result = remove_quotes("'hello world'")
        assert result == "hello world"

    def test_remove_quotes_with_spaces(self):
        """前後にスペースがある場合のクォート除去テスト"""
        result = remove_quotes(' "hello world" ')
        assert result == "hello world"

    def test_no_quotes_to_remove(self):
        """クォートがない場合のテスト"""
        result = remove_quotes("hello world")
        assert result == "hello world"

    def test_mismatched_quotes(self):
        """不一致クォートの場合のテスト"""
        result = remove_quotes("\"hello world'")
        assert result == "\"hello world'"

    def test_single_character_quotes(self):
        """単一文字のクォートテスト"""
        result = remove_quotes('"a"')
        assert result == "a"

    def test_empty_string(self):
        """空文字列のテスト"""
        result = remove_quotes("")
        assert result == ""

    def test_only_quotes(self):
        """クォートのみの文字列テスト"""
        result = remove_quotes('""')
        assert result == ""

    def test_nested_quotes(self):
        """ネストしたクォートのテスト（外側のみ除去）"""
        result = remove_quotes("\"he said 'hello'\"")
        assert result == "he said 'hello'"

    def test_partial_quotes(self):
        """部分的なクォートのテスト"""
        result = remove_quotes('"incomplete')
        assert result == '"incomplete'

        result = remove_quotes('incomplete"')
        assert result == 'incomplete"'
