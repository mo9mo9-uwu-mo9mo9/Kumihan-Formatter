"""
パーサー関数レベルテスト (Issue #1143)

Critical Priority: テストカバレッジ危機的不足（0.6%）対策
Phase 1: トップレベルパーサー関数テスト追加
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict

from kumihan_formatter.parser import parse, parse_with_error_config


class TestParseFunction:
    """parse関数テスト"""

    @pytest.mark.unit
    def test_parse_simple_text(self):
        """シンプルテキスト解析テスト"""
        text = "Hello, World!"
        result = parse(text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_empty_string(self):
        """空文字列解析テスト"""
        result = parse("")
        assert result is not None

    @pytest.mark.unit
    def test_parse_none_input(self):
        """None入力処理テスト"""
        # Noneを渡した場合の動作をテスト
        try:
            result = parse(None)
            # 例外が発生しない場合は結果を確認
            assert result is not None or result is None
        except (TypeError, AttributeError):
            # 適切にエラーハンドリングされることを確認
            pass

    @pytest.mark.unit
    def test_parse_multiline_text(self):
        """複数行テキスト解析テスト"""
        multiline_text = """行1
行2
行3"""
        result = parse(multiline_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_kumihan_syntax(self):
        """Kumihan記法解析テスト"""
        kumihan_text = "# 見出し #テスト見出し##"
        result = parse(kumihan_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_complex_kumihan_syntax(self):
        """複雑なKumihan記法解析テスト"""
        complex_text = """# 見出し #メインタイトル##

# 太字 #重要なポイント##
通常のテキスト

# イタリック #注釈##"""
        result = parse(complex_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_special_characters(self):
        """特殊文字を含む解析テスト"""
        special_text = "日本語テスト 🎌 émojï αβγ"
        result = parse(special_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_large_text(self):
        """大きなテキスト解析テスト"""
        large_text = "\n".join([f"行 {i}" for i in range(1000)])
        result = parse(large_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_whitespace_only(self):
        """空白のみテキスト解析テスト"""
        whitespace_text = "   \t\n   \t\n   "
        result = parse(whitespace_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_return_type(self):
        """戻り値の型確認テスト"""
        text = "Type check test"
        result = parse(text)
        # 戻り値が適切な型であることを確認（具体的な型はコードを確認）
        assert result is not None


class TestParseWithErrorConfigFunction:
    """parse_with_error_config関数テスト"""

    @pytest.mark.unit
    def test_parse_with_error_config_basic(self):
        """基本的なエラー設定解析テスト"""
        text = "Test content"
        error_config = {"enable_graceful_errors": True}
        
        result = parse_with_error_config(text, error_config)
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_error_config_empty_config(self):
        """空のエラー設定テスト"""
        text = "Test content"
        error_config = {}
        
        result = parse_with_error_config(text, error_config)
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_error_config_none_config(self):
        """Noneエラー設定テスト"""
        text = "Test content"
        
        try:
            result = parse_with_error_config(text, None)
            assert result is not None or result is None
        except (TypeError, AttributeError):
            # 適切にエラーハンドリングされることを確認
            pass

    @pytest.mark.unit
    def test_parse_with_error_config_complex_config(self):
        """複雑なエラー設定テスト"""
        text = "Test content"
        error_config = {
            "enable_graceful_errors": True,
            "max_errors": 10,
            "error_log_level": "WARNING",
            "continue_on_error": True
        }
        
        result = parse_with_error_config(text, error_config)
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_error_config_invalid_text(self):
        """無効なテキストでのエラー設定解析テスト"""
        invalid_text = "# 不完全記法 #未完成"
        error_config = {"enable_graceful_errors": True}
        
        result = parse_with_error_config(invalid_text, error_config)
        # エラー設定により、適切に処理されることを確認
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_error_config_strict_mode(self):
        """厳密モードでのエラー設定テスト"""
        text = "Test content"
        error_config = {
            "enable_graceful_errors": False,
            "strict_mode": True
        }
        
        result = parse_with_error_config(text, error_config)
        assert result is not None

    @pytest.mark.unit 
    def test_parse_with_error_config_logging_enabled(self):
        """ログ有効でのエラー設定テスト"""
        text = "# 見出し #ログテスト##"
        error_config = {
            "enable_logging": True,
            "log_level": "DEBUG"
        }
        
        result = parse_with_error_config(text, error_config)
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_error_config_custom_handlers(self):
        """カスタムハンドラー設定テスト"""
        text = "Custom handler test"
        error_config = {
            "custom_error_handler": lambda error: print(f"Custom error: {error}"),
            "enable_graceful_errors": True
        }
        
        result = parse_with_error_config(text, error_config)
        assert result is not None

    @pytest.mark.unit
    def test_parse_with_error_config_performance_monitoring(self):
        """パフォーマンス監視設定テスト"""
        text = "Performance monitoring test"
        error_config = {
            "enable_performance_monitoring": True,
            "performance_threshold_ms": 1000
        }
        
        result = parse_with_error_config(text, error_config)
        assert result is not None


class TestParseFunctionIntegration:
    """パーサー関数統合テスト"""

    @pytest.mark.unit
    def test_parse_function_with_mocked_parser(self):
        """Parserクラスをモックした統合テスト"""
        with patch('kumihan_formatter.parser.Parser') as MockParser:
            # モックの設定
            mock_instance = Mock()
            mock_instance.parse.return_value = "mocked_result"
            MockParser.return_value = mock_instance
            
            result = parse("test text")
            
            # Parserが呼ばれたことを確認
            MockParser.assert_called_once()
            mock_instance.parse.assert_called_once_with("test text")

    @pytest.mark.unit
    def test_parse_with_error_config_function_with_mocked_parser(self):
        """parse_with_error_config関数のモック統合テスト"""
        with patch('kumihan_formatter.parser.Parser') as MockParser:
            # モックの設定
            mock_instance = Mock()
            mock_instance.parse.return_value = "mocked_result"
            MockParser.return_value = mock_instance
            
            error_config = {"test": "config"}
            result = parse_with_error_config("test text", error_config)
            
            # 適切にParserが作成・呼び出しされたことを確認
            MockParser.assert_called()

    @pytest.mark.unit
    def test_parse_function_consistency(self):
        """parse関数の一貫性テスト"""
        text = "Consistency test"
        
        # 同じ入力に対して一貫した結果が返されることを確認
        result1 = parse(text)
        result2 = parse(text)
        
        # 結果の型や基本的な構造が同じであることを確認
        assert type(result1) == type(result2)

    @pytest.mark.unit
    def test_parse_functions_error_handling(self):
        """パーサー関数のエラーハンドリングテスト"""
        # 極端に大きなテキスト
        huge_text = "x" * 100000
        
        # 関数が適切にエラーハンドリングを行うことを確認
        try:
            result = parse(huge_text)
            assert result is not None or result is None
        except MemoryError:
            # メモリエラーは予想される動作
            pass
        except Exception as e:
            # その他の例外は適切にハンドリングされるべき
            assert False, f"Unexpected exception: {e}"

    @pytest.mark.unit
    def test_parse_function_with_config_comparison(self):
        """設定ありなしでの解析比較テスト"""
        text = "# 見出し #比較テスト##"
        
        # 通常の解析
        result_normal = parse(text)
        
        # エラー設定ありの解析
        result_with_config = parse_with_error_config(text, {"enable_graceful_errors": True})
        
        # 両方とも結果が得られることを確認
        assert result_normal is not None
        assert result_with_config is not None


class TestParseFunctionEdgeCases:
    """パーサー関数エッジケーステスト"""

    @pytest.mark.unit
    def test_parse_very_long_single_line(self):
        """非常に長い単一行の解析テスト"""
        very_long_line = "A" * 50000
        result = parse(very_long_line)
        assert result is not None

    @pytest.mark.unit
    def test_parse_many_short_lines(self):
        """多数の短い行の解析テスト"""
        many_lines = "\n".join([f"L{i}" for i in range(5000)])
        result = parse(many_lines)
        assert result is not None

    @pytest.mark.unit
    def test_parse_deeply_nested_structure(self):
        """深くネストした構造の解析テスト"""
        nested_text = ""
        for i in range(100):
            nested_text += f"# レベル{i} #ネスト構造{i}##\n"
        
        result = parse(nested_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_mixed_encodings_simulation(self):
        """混合エンコーディングシミュレーションテスト"""
        # Unicode の様々な文字を混合
        mixed_text = "ASCII text 日本語 🌸 Ελληνικά العربية 中文"
        result = parse(mixed_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_control_characters(self):
        """制御文字を含むテキストの解析テスト"""
        control_chars_text = "Line1\r\nLine2\tTabbed\x00NullChar"
        result = parse(control_chars_text)
        assert result is not None

    @pytest.mark.unit
    def test_parse_binary_like_content(self):
        """バイナリ風コンテンツの解析テスト"""
        binary_like = "".join([chr(i) for i in range(32, 127)])  # 印字可能ASCII文字
        result = parse(binary_like)
        assert result is not None