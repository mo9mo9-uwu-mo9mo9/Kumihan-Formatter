"""
parser_utils.py の単体テスト

AI開発効率化・個人開発最適化のためのテストケース
"""

import pytest
from typing import List

from kumihan_formatter.parser_utils import (
    extract_json_path,
    remove_quotes,
    find_closing_brace,
    find_matching_quote,
    is_valid_json_path_character,
)


class TestExtractJsonPath:
    """extract_json_path関数のテストクラス"""

    @pytest.mark.unit
    @pytest.mark.parametrize("json_path,expected", [
        ("data.items[0].name", ["data", "items", "0", "name"]),
        ("data.items", ["data", "items"]),
        ("data", ["data"]),
        ("items[0]", ["items", "0"]),
        ("data.items[0][1].value", ["data", "items", "0", "1", "value"]),
        ("", []),
        ("data.", ["data"]),
        (".data", ["data"]),
        ("data..items", ["data", "items"]),
    ])
    def test_extract_json_path_valid_cases(self, json_path: str, expected: List[str]):
        """有効なJSONパスのテスト"""
        result = extract_json_path(json_path)
        assert result == expected

    @pytest.mark.unit
    def test_extract_json_path_empty_string(self):
        """空文字列のテスト"""
        result = extract_json_path("")
        assert result == []

    @pytest.mark.unit  
    def test_extract_json_path_whitespace_handling(self):
        """空白文字の処理テスト"""
        result = extract_json_path("data . items[ 0 ] . name")
        assert result == ["data", "items", "0", "name"]

    @pytest.mark.unit
    def test_extract_json_path_type_safety(self):
        """型安全性のテスト"""
        test_cases = ["data.items", "simple", "complex.nested[0].value"]
        for json_path in test_cases:
            result = extract_json_path(json_path)
            assert isinstance(result, list)
            # 各要素は文字列であることを確認
            assert all(isinstance(item, str) for item in result)


class TestRemoveQuotes:
    """remove_quotes関数のテストクラス"""

    @pytest.mark.unit
    @pytest.mark.parametrize("input_text,expected", [
        ('"hello"', "hello"),
        ("'hello'", "hello"),
        ('"hello world"', "hello world"),
        ("'hello world'", "hello world"),
        ("hello", "hello"),
        ('""', ""),
        ("''", ""),
        ('"hello', '"hello'),     # 非対称クォート
        ("hello'", "hello'"),     # 非対称クォート
        ('"hello\'', '"hello\''), # 混在クォート
        ("", ""),
        ("   ", ""),
        ('  "hello"  ', "hello"), # 前後の空白込み
    ])
    def test_remove_quotes_cases(self, input_text: str, expected: str):
        """クォート除去のテストケース"""
        result = remove_quotes(input_text)
        assert result == expected

    @pytest.mark.unit
    def test_remove_quotes_nested_quotes(self):
        """ネストしたクォートの処理"""
        result = remove_quotes('"he said \\"hello\\""')
        # 実装では内部のエスケープは処理しない
        assert result == 'he said \\"hello\\"'

    @pytest.mark.unit
    def test_remove_quotes_length_property(self):
        """出力が入力より長くならないことを検証"""
        test_cases = ['"hello"', "'world'", 'no quotes', '""', "''", '"partial', "mix'ed\""]
        for text in test_cases:
            result = remove_quotes(text)
            assert len(result) <= len(text)


class TestUtilityFunctions:
    """その他のユーティリティ関数のテストクラス"""

    @pytest.mark.unit
    @pytest.mark.parametrize("text,start_pos,expected", [
        ('{"key": "value"}', 0, 15),  # 実際の実装に合わせて修正
        ('[1, 2, 3]', 0, -1),        # [で始まるものは-1を返す
        ('{"nested": {"key": "value"}}', 0, 27),  # 実際の実装に合わせて修正
        ('no braces here', 0, -1),
        ('{"simple"}', 0, 9),
    ])
    def test_find_closing_brace_basic_cases(self, text: str, start_pos: int, expected: int):
        """find_closing_brace基本ケースのテスト"""
        result = find_closing_brace(text, start_pos)
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("char,expected", [
        ('a', True),
        ('1', True),
        ('_', True),
        ('.', True),   # 実装では有効文字
        ('[', True),   # 実装では有効文字
        (']', True),   # 実装では有効文字
        ('-', True),   # 実装では有効文字
        (' ', False),
        ('!', False),
        ('@', False),
    ])
    def test_is_valid_json_path_character(self, char: str, expected: bool):
        """is_valid_json_path_character関数のテスト"""
        result = is_valid_json_path_character(char)
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("text,start_pos,expected", [
        ('"hello world"', 0, 12),
        ("'hello world'", 0, 12),
        ('"unclosed quote', 0, -1),
        ('no quotes here', 0, -1),  # 最初の文字がクォートではない
        ('"simple"', 0, 7),  # 実際の実装に合わせて修正
    ])
    def test_find_matching_quote_cases(self, text: str, start_pos: int, expected: int):
        """find_matching_quote関数のテスト"""
        result = find_matching_quote(text, start_pos)
        assert result == expected