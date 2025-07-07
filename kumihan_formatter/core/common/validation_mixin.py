"""Validation mixin for consistent validation patterns

This module provides reusable validation logic that can be mixed into
any class needing validation capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

from .error_framework import ErrorSeverity, KumihanError, ValidationError


class ValidationRule:
    """Represents a single validation rule"""

    def __init__(
        self,
        name: str,
        validator: Callable[[Any], bool],
        error_message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        suggestion: Optional[str] = None,
    ):
        """Initialize validation rule

        Args:
            name: Rule identifier
            validator: Function that returns True if valid
            error_message: Message for validation failure
            severity: Error severity level
            suggestion: Suggestion for fixing the issue
        """
        self.name = name
        self.validator = validator
        self.error_message = error_message
        self.severity = severity
        self.suggestion = suggestion

    def validate(self, value: Any) -> Optional[ValidationError]:
        """Validate a value against this rule

        Args:
            value: Value to validate

        Returns:
            ValidationError if invalid, None if valid
        """
        try:
            if self.validator(value):
                return None
        except Exception as e:
            # If validator itself fails, that's an error
            return ValidationError(
                f"Validation rule '{self.name}' failed: {e}",
                severity=ErrorSeverity.CRITICAL,
                technical_details=str(e),
            )

        # Validation failed
        suggestions = [self.suggestion] if self.suggestion else []
        return ValidationError(
            self.error_message,
            severity=self.severity,
            suggestions=suggestions,
            technical_details=f"Failed rule: {self.name}",
        )


class ValidationMixin:
    """Mixin class providing common validation patterns

    This mixin can be added to any class to provide consistent
    validation capabilities across the application.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._validation_rules: Dict[str, List[ValidationRule]] = {}
        self._validation_errors: List[ValidationError] = []

    def add_validation_rule(self, field: str, rule: ValidationRule) -> None:
        """Add a validation rule for a field

        Args:
            field: Field name to validate
            rule: Validation rule to apply
        """
        if field not in self._validation_rules:
            self._validation_rules[field] = []
        self._validation_rules[field].append(rule)

    def add_simple_rule(
        self,
        field: str,
        validator: Callable[[Any], bool],
        error_message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a simple validation rule

        Args:
            field: Field name to validate
            validator: Function that returns True if valid
            error_message: Error message for failures
            severity: Error severity level
            suggestion: Suggestion for fixing
        """
        rule = ValidationRule(
            name=f"{field}_rule_{len(self._validation_rules.get(field, []))}",
            validator=validator,
            error_message=error_message,
            severity=severity,
            suggestion=suggestion,
        )
        self.add_validation_rule(field, rule)

    def validate_field(self, field: str, value: Any) -> List[ValidationError]:
        """Validate a single field

        Args:
            field: Field name
            value: Value to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        rules = self._validation_rules.get(field, [])

        for rule in rules:
            error = rule.validate(value)
            if error:
                errors.append(error)

        return errors

    def validate_all(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate all fields in provided data

        Args:
            data: Dictionary of field values to validate

        Returns:
            List of all validation errors
        """
        all_errors = []

        for field, value in data.items():
            field_errors = self.validate_field(field, value)
            all_errors.extend(field_errors)

        self._validation_errors = all_errors
        return all_errors

    def is_valid(self, data: Dict[str, Any]) -> bool:
        """Check if data is valid

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        errors = self.validate_all(data)
        return len(errors) == 0

    def get_validation_errors(self) -> List[ValidationError]:
        """Get last validation errors"""
        return self._validation_errors.copy()

    def clear_validation_errors(self) -> None:
        """Clear stored validation errors"""
        self._validation_errors.clear()

    def require_not_empty(self, field: str, message: Optional[str] = None) -> None:
        """Add rule requiring field is not empty

        Args:
            field: Field name
            message: Custom error message
        """
        msg = message or f"{field} cannot be empty"
        self.add_simple_rule(
            field,
            lambda x: x is not None and str(x).strip() != "",
            msg,
            suggestion=f"Provide a value for {field}",
        )

    def require_type(
        self, field: str, expected_type: type, message: Optional[str] = None
    ) -> None:
        """Add rule requiring specific type

        Args:
            field: Field name
            expected_type: Expected Python type
            message: Custom error message
        """
        msg = message or f"{field} must be of type {expected_type.__name__}"
        self.add_simple_rule(
            field,
            lambda x: isinstance(x, expected_type),
            msg,
            suggestion=f"Convert {field} to {expected_type.__name__}",
        )

    def require_in_range(
        self,
        field: str,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        message: Optional[str] = None,
    ) -> None:
        """Add rule requiring value in range

        Args:
            field: Field name
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            message: Custom error message
        """
        if min_val is not None and max_val is not None:
            range_desc = f"between {min_val} and {max_val}"
            validator = lambda x: min_val <= x <= max_val
        elif min_val is not None:
            range_desc = f"at least {min_val}"
            validator = lambda x: x >= min_val
        elif max_val is not None:
            range_desc = f"at most {max_val}"
            validator = lambda x: x <= max_val
        else:
            raise ValueError("At least one of min_val or max_val must be provided")

        msg = message or f"{field} must be {range_desc}"
        self.add_simple_rule(
            field, validator, msg, suggestion=f"Adjust {field} to be {range_desc}"
        )

    def require_matches_pattern(
        self, field: str, pattern: str, message: Optional[str] = None
    ) -> None:
        """Add rule requiring value matches regex pattern

        Args:
            field: Field name
            pattern: Regex pattern
            message: Custom error message
        """
        import re

        compiled_pattern = re.compile(pattern)

        msg = message or f"{field} must match pattern: {pattern}"
        self.add_simple_rule(
            field,
            lambda x: bool(compiled_pattern.match(str(x))),
            msg,
            suggestion=f"Format {field} according to pattern: {pattern}",
        )

    def require_one_of(
        self, field: str, valid_values: List[Any], message: Optional[str] = None
    ) -> None:
        """Add rule requiring value is one of specified options

        Args:
            field: Field name
            valid_values: List of valid values
            message: Custom error message
        """
        msg = message or f"{field} must be one of: {', '.join(map(str, valid_values))}"
        self.add_simple_rule(
            field,
            lambda x: x in valid_values,
            msg,
            suggestion=f"Use one of: {', '.join(map(str, valid_values))}",
        )
