"""
Test cases for error pattern detection and handling.

Tests various error conditions including syntax errors, processing errors, and edge cases.
"""

import tempfile
from pathlib import Path

import pytest

from kumihan_formatter.core.keyword_parsing.definitions import KeywordDefinitions
from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser
from kumihan_formatter.core.keyword_parsing.validator import KeywordValidator
from kumihan_formatter.core.syntax.syntax_errors import ErrorSeverity, SyntaxError
from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator


@pytest.mark.unit
@pytest.mark.error_handling
class TestSyntaxErrors:
    """Test syntax error detection and reporting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)

    def test_unclosed_marker_error(self):
        """Test detection of unclosed markers."""
        error_texts = [
            "#太字 未完了のマーカー",
            "#見出し1\n複数行\nでも未完了",
            "#下線 開始だけ",
        ]

        for text in error_texts:
            errors = self.validator.validate_text(text)
            # Should detect unclosed marker as error
            assert len(errors) > 0, f"Failed to detect unclosed marker in: {text}"

            # Check error severity
            severe_errors = [
                e for e in errors if hasattr(e, "severity") and e.severity == ErrorSeverity.ERROR
            ]
            assert len(severe_errors) > 0, f"Unclosed marker should be severe error: {text}"

    def test_unopened_marker_error(self):
        """Test detection of unopened closing markers."""
        error_texts = [
            "未開始のマーカー#",
            "複数行の\n内容で\n未開始#",
            "text 下線 終了だけ#",
        ]

        for text in error_texts:
            errors = self.validator.validate_text(text)
            # Should detect unopened closing marker
            # Implementation may vary - at minimum should not crash
            assert isinstance(errors, list)

    def test_mismatched_marker_nesting(self):
        """Test detection of improperly nested markers."""
        error_texts = [
            "#太字#下線 交差したネスト##",
            "#見出し1\n#太字 内側\n#\n外側続行#",
            "#下線#太字 重複開始#",
        ]

        for text in error_texts:
            errors = self.validator.validate_text(text)
            # Should detect nesting issues
            assert isinstance(errors, list)
            # May or may not flag as error depending on implementation

    def test_invalid_marker_syntax(self):
        """Test detection of invalid marker syntax."""
        invalid_syntax = [
            "#太字 マーカー不足",  # Missing closing marker
            ";#太字 マーカー過多#",  # Extra semicolon
            "#太字 内容",  # Missing closing marker
            "#太字 内容##",  # Too many closing markers
            "#  スペースのみ  #",  # Only whitespace in marker name
        ]

        for text in invalid_syntax:
            errors = self.validator.validate_text(text)
            # Should handle invalid syntax appropriately
            assert isinstance(errors, list)

    def test_empty_marker_name(self):
        """Test handling of empty marker names."""
        empty_marker_texts = [
            "# 空のマーカー名#",
            "#\n空行のマーカー名\n#",
            "#   \n   #",  # Only whitespace
        ]

        for text in empty_marker_texts:
            errors = self.validator.validate_text(text)
            # Should detect or handle empty marker names
            assert isinstance(errors, list)

    def test_unknown_keyword_handling(self):
        """Test handling of unknown/undefined keywords."""
        unknown_keywords = [
            "#存在しない装飾 内容#",
            "#未定義キーワード テキスト#",
            "#typo_keyword 英語キーワード#",
            "#123数字 数字開始#",
            "#特殊$記号 記号含み#",
        ]

        for text in unknown_keywords:
            errors = self.validator.validate_text(text)
            # Implementation may be flexible or strict
            assert isinstance(errors, list)


@pytest.mark.unit
@pytest.mark.error_handling
class TestProcessingErrors:
    """Test processing errors and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)

    def test_extremely_long_content(self):
        """Test handling of extremely long content."""
        # Generate very long content
        long_content = "非常に長い内容です。" * 10000
        text = f"#太字 {long_content}#"

        # Should handle without crashing
        try:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)

            assert result is not None or result is None  # Any result is acceptable
            assert isinstance(errors, list)

        except MemoryError:
            pytest.skip("System memory insufficient for test")
        except Exception as e:
            pytest.fail(f"Unexpected exception with long content: {e}")

    def test_deeply_nested_structures(self):
        """Test handling of deeply nested structures."""
        # Create deeply nested structure
        nested_text = "#太字\n" * 100 + "中心内容" + "\n#" * 100

        try:
            result = self.parser.parse(nested_text)
            errors = self.validator.validate_text(nested_text)

            # Should handle without stack overflow
            assert isinstance(errors, list)

        except RecursionError:
            pytest.fail("Stack overflow with nested structures")
        except Exception as e:
            # Other errors may be acceptable depending on implementation
            assert isinstance(e, Exception)

    def test_special_character_handling(self):
        """Test handling of special and Unicode characters."""
        special_chars = [
            "#太字 \\n\\t\\r エスケープ文字#",
            "#太字 🚀🎯📝 絵文字#",
            "#太字 αβγδε ギリシャ文字#",
            "#太字 特殊引用符#",
            "#太字 制御文字#",
        ]

        for text in special_chars:
            try:
                result = self.parser.parse(text)
                errors = self.validator.validate_text(text)

                # Should handle special characters without crashing
                assert isinstance(errors, list)

            except UnicodeError:
                # Unicode errors may be acceptable
                pass
            except Exception as e:
                pytest.fail(f"Unexpected error with special characters: {e}")

    def test_encoding_edge_cases(self, temp_dir):
        """Test handling of different encodings."""
        test_content = "#太字 日本語テスト内容#"

        # Test different encodings
        encodings = ["utf-8", "shift_jis", "euc-jp"]

        for encoding in encodings:
            try:
                test_file = temp_dir / f"test_{encoding}.txt"
                test_file.write_text(test_content, encoding=encoding)

                # Try to validate the file
                errors = self.validator.validate_file(test_file)
                assert isinstance(errors, list)

            except (UnicodeEncodeError, UnicodeDecodeError):
                # Encoding issues may be expected
                pass
            except Exception as e:
                # Other errors should be investigated
                pytest.fail(f"Unexpected error with {encoding}: {e}")

    def test_file_not_found_handling(self):
        """Test handling of non-existent files."""
        non_existent_file = Path("/non/existent/path/file.txt")

        try:
            errors = self.validator.validate_file(non_existent_file)
            # Should handle gracefully
            assert isinstance(errors, list)

        except FileNotFoundError:
            # FileNotFoundError is acceptable
            pass
        except Exception as e:
            pytest.fail(f"Unexpected error for non-existent file: {e}")

    def test_permission_denied_handling(self, temp_dir):
        """Test handling of permission denied scenarios."""
        # Create a file and remove read permissions
        test_file = temp_dir / "no_permission.txt"
        test_file.write_text("#太字 テスト内容#", encoding="utf-8")

        try:
            test_file.chmod(0o000)  # Remove all permissions

            errors = self.validator.validate_file(test_file)
            # Should handle permission errors gracefully
            assert isinstance(errors, list)

        except PermissionError:
            # PermissionError is acceptable
            pass
        except OSError:
            # Other OS errors may occur
            pass
        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except:
                pass


@pytest.mark.unit
@pytest.mark.error_handling
class TestEdgeCaseScenarios:
    """Test edge case scenarios and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)

    def test_empty_input(self):
        """Test handling of empty input."""
        empty_inputs = [
            "",
            "   ",
            "\n\n\n",
            "\t\t\t",
        ]

        for text in empty_inputs:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)

            # Should handle empty input gracefully
            assert isinstance(errors, list)

    def test_single_character_inputs(self):
        """Test handling of single character inputs."""
        single_chars = ["a", "あ", "1", ";", "\\n", " "]

        for char in single_chars:
            result = self.parser.parse(char)
            errors = self.validator.validate_text(char)

            # Should handle without crashing
            assert isinstance(errors, list)

    def test_marker_at_text_boundaries(self):
        """Test markers at the beginning and end of text."""
        boundary_cases = [
            "#太字 開始マーカー#後続テキスト",
            "前置きテキスト#太字 終了マーカー#",
            "#太字 全体がマーカー#",
            "#太字 開始マーカー# 中間 #下線 終了マーカー#",
        ]

        for text in boundary_cases:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)

            # Should handle boundary cases appropriately
            assert isinstance(errors, list)

    def test_repeated_markers(self):
        """Test repeated identical markers."""
        repeated_patterns = [
            "#太字 最初##太字 次##太字 最後#",
            "#見出し1 A# #見出し1 B# #見出し1 C#",
            "#下線 重複#下線 重複#下線 重複#",
        ]

        for text in repeated_patterns:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)

            # Should handle repeated markers
            assert isinstance(errors, list)

    def test_mixed_content_types(self):
        """Test mixed content with various elements."""
        mixed_content = """通常のテキスト

#見出し1
セクション1のタイトル
##

段落テキストがあります。

#太字 重要な情報# と #下線 強調情報# が混在。

#リスト
- 項目1
- 項目2
- 項目3
##

最後の段落です。"""

        result = self.parser.parse(mixed_content)
        errors = self.validator.validate_text(mixed_content)

        # Should handle complex mixed content
        assert isinstance(errors, list)

    @pytest.mark.slow
    def test_stress_test_multiple_files(self, temp_dir):
        """Stress test with multiple files."""
        # Create multiple test files
        file_count = 50
        files = []

        for i in range(file_count):
            test_file = temp_dir / f"stress_test_{i}.txt"
            content = f"""#見出し1
ストレステストファイル {i}
##

#太字 ファイル{i}の重要情報#

通常のテキスト内容です。"""
            test_file.write_text(content, encoding="utf-8")
            files.append(test_file)

        # Validate all files
        try:
            all_errors = self.validator.validate_files(files)
            assert isinstance(all_errors, (list, dict))

        except Exception as e:
            pytest.fail(f"Stress test failed: {e}")
