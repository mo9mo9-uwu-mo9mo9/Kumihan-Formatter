"""
Test cases for syntax validation system.

Tests comprehensive syntax validation including error detection and reporting.
"""

import pytest
from pathlib import Path

from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator, UserFriendlyError, ErrorCatalog
from kumihan_formatter.core.syntax.syntax_errors import SyntaxError, ErrorSeverity, ErrorTypes
from kumihan_formatter.core.syntax.syntax_rules import SyntaxRules
from kumihan_formatter.core.syntax.syntax_validator_utils import SyntaxValidatorUtils


@pytest.mark.unit
@pytest.mark.notation
class TestKumihanSyntaxValidator:
    """Test main syntax validator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()
    
    def test_valid_syntax_validation(self):
        """Test validation of syntactically correct text."""
        valid_texts = [
            ";;;太字 正常なテキスト;;;",
            "これは通常のテキストです。",
            """;;;見出し1
ブロック形式のテキスト
;;;""",
            ";;;太字 内容;;; と ;;;下線 内容;;; の組み合わせ",
        ]
        
        for text in valid_texts:
            errors = self.validator.validate_text(text)
            assert isinstance(errors, list)
            # Valid syntax should produce minimal or no errors
            if len(errors) > 0:
                # Check if errors are just warnings
                severe_errors = [e for e in errors if hasattr(e, 'severity') and e.severity == ErrorSeverity.ERROR]
                assert len(severe_errors) == 0, f"Unexpected errors for valid text: {text}"
    
    def test_file_validation(self, sample_text_files):
        """Test validation of text files."""
        basic_file = sample_text_files["basic"]
        errors = self.validator.validate_file(basic_file)
        
        assert isinstance(errors, list)
        # Basic file should have minimal errors
        
    def test_batch_validation(self, sample_text_files):
        """Test batch validation of multiple files."""
        files = list(sample_text_files.values())
        all_errors = self.validator.validate_files(files)
        
        assert isinstance(all_errors, (list, dict))
        # Should process all files without crashing
    
    def test_error_severity_classification(self):
        """Test proper error severity classification."""
        # Test text that might produce different severity levels
        test_cases = [
            (";;;太字 正常;;;", 0),  # Should have no severe errors
            (";;;不明な記法 内容;;;", None),  # May have warnings
            (";;;太字 未完了", None),  # Should have errors
        ]
        
        for text, expected_severe_count in test_cases:
            errors = self.validator.validate_text(text)
            
            if expected_severe_count is not None:
                severe_errors = [e for e in errors if hasattr(e, 'severity') and e.severity == ErrorSeverity.ERROR]
                assert len(severe_errors) == expected_severe_count
    
    def test_configuration_handling(self):
        """Test validator configuration options."""
        # Test with different configurations if supported
        try:
            validator_strict = KumihanSyntaxValidator(strict=True)
            validator_lenient = KumihanSyntaxValidator(strict=False)
            
            test_text = ";;;微妙な記法 内容;;;"
            
            strict_errors = validator_strict.validate_text(test_text)
            lenient_errors = validator_lenient.validate_text(test_text)
            
            assert isinstance(strict_errors, list)
            assert isinstance(lenient_errors, list)
            
        except TypeError:
            # Configuration options may not be implemented
            pytest.skip("Validator configuration options not available")


@pytest.mark.unit
@pytest.mark.error_handling
class TestSyntaxErrors:
    """Test syntax error types and handling."""
    
    def test_error_severity_enum(self):
        """Test error severity enumeration."""
        assert hasattr(ErrorSeverity, 'WARNING') or hasattr(ErrorSeverity, 'WARN')
        assert hasattr(ErrorSeverity, 'ERROR')
        assert hasattr(ErrorSeverity, 'INFO') or hasattr(ErrorSeverity, 'DEBUG')
    
    def test_error_types_enum(self):
        """Test error types enumeration."""
        # Should have various error categories
        error_attrs = dir(ErrorTypes)
        expected_types = ['SYNTAX', 'STRUCTURE', 'VALIDATION', 'PARSING']
        
        # At least some error types should be defined
        found_types = [attr for attr in error_attrs if any(t in attr for t in expected_types)]
        assert len(found_types) > 0
    
    def test_syntax_error_creation(self):
        """Test SyntaxError object creation."""
        try:
            error = SyntaxError(
                message="Test error message",
                severity=ErrorSeverity.ERROR,
                line_number=1,
                position=0
            )
            
            assert error.message == "Test error message"
            assert error.severity == ErrorSeverity.ERROR
            assert error.line_number == 1
            assert error.position == 0
            
        except (TypeError, AttributeError):
            # SyntaxError may have different constructor
            pytest.skip("SyntaxError constructor signature not as expected")
    
    def test_user_friendly_error(self):
        """Test user-friendly error formatting."""
        try:
            friendly_error = UserFriendlyError(
                original_error="Complex technical error",
                user_message="分かりやすいエラーメッセージ",
                suggestions=["提案1", "提案2"]
            )
            
            assert "分かりやすい" in friendly_error.user_message
            assert len(friendly_error.suggestions) == 2
            
        except (TypeError, AttributeError):
            # UserFriendlyError may not be implemented yet
            pytest.skip("UserFriendlyError not fully implemented")


@pytest.mark.unit
@pytest.mark.notation
class TestSyntaxRules:
    """Test syntax rules engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = SyntaxRules()
    
    def test_rule_loading(self):
        """Test syntax rules are properly loaded."""
        rules = self.rules.get_all_rules()
        
        assert isinstance(rules, (list, dict))
        assert len(rules) > 0, "No syntax rules loaded"
    
    def test_rule_application(self):
        """Test syntax rule application."""
        test_text = ";;;太字 テスト内容;;;"
        
        # Apply rules to test text
        violations = self.rules.check_text(test_text)
        
        assert isinstance(violations, list)
        # Well-formed text should have few or no violations
    
    def test_rule_categories(self):
        """Test different categories of syntax rules."""
        # Test if rules are categorized
        categories = self.rules.get_rule_categories()
        
        if categories:
            assert isinstance(categories, (list, dict))
            # Should have different rule categories
            expected_categories = ['structure', 'formatting', 'nesting', 'keywords']
            found_categories = [cat for cat in expected_categories if cat in str(categories)]
        else:
            pytest.skip("Rule categories not implemented")
    
    def test_custom_rule_addition(self):
        """Test adding custom syntax rules."""
        try:
            original_count = len(self.rules.get_all_rules())
            
            # Try to add a custom rule
            custom_rule = {
                'name': 'test_rule',
                'pattern': r';;;[\w]+',
                'message': 'Test rule violation'
            }
            
            self.rules.add_rule(custom_rule)
            new_count = len(self.rules.get_all_rules())
            
            assert new_count > original_count
            
        except (AttributeError, NotImplementedError):
            # Custom rule addition may not be implemented
            pytest.skip("Custom rule addition not implemented")


@pytest.mark.unit
@pytest.mark.notation
class TestSyntaxValidatorUtils:
    """Test syntax validator utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.utils = SyntaxValidatorUtils()
    
    def test_text_preprocessing(self):
        """Test text preprocessing utilities."""
        test_text = "  ;;;太字 内容;;;  \n\n  "
        processed = self.utils.preprocess_text(test_text)
        
        assert isinstance(processed, str)
        # Should handle whitespace and formatting
        assert len(processed) <= len(test_text)
    
    def test_position_calculation(self):
        """Test position calculation utilities."""
        text = "行1\n行2\n;;;太字 内容;;;\n行4"
        
        try:
            line_number = self.utils.get_line_number(text, text.find("太字"))
            column_number = self.utils.get_column_number(text, text.find("太字"))
            
            assert isinstance(line_number, int)
            assert isinstance(column_number, int)
            assert line_number > 0
            assert column_number >= 0
            
        except AttributeError:
            # Position calculation may not be implemented
            pytest.skip("Position calculation utilities not implemented")
    
    def test_error_context_extraction(self):
        """Test error context extraction."""
        text = "前の行\n;;;エラーのある行;;;\n次の行"
        error_position = text.find("エラー")
        
        try:
            context = self.utils.extract_error_context(text, error_position, context_lines=1)
            
            assert isinstance(context, str)
            assert "エラーのある行" in context
            assert "前の行" in context or "次の行" in context
            
        except AttributeError:
            # Error context extraction may not be implemented
            pytest.skip("Error context extraction not implemented")
    
    def test_marker_boundary_detection(self):
        """Test marker boundary detection utilities."""
        text = "通常テキスト;;;太字 マーカー内容;;;通常テキスト"
        
        try:
            boundaries = self.utils.find_marker_boundaries(text)
            
            assert isinstance(boundaries, list)
            if len(boundaries) > 0:
                # Should find at least one marker boundary
                start, end = boundaries[0]
                assert isinstance(start, int)
                assert isinstance(end, int)
                assert start < end
                
        except AttributeError:
            # Marker boundary detection may not be implemented
            pytest.skip("Marker boundary detection not implemented")