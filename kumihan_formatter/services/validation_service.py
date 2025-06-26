"""Validation service implementation

This module provides centralized validation capabilities
with schema management and validation rule composition.
"""

import json
from typing import Any, Dict, List, Optional, Callable, Union
from pathlib import Path

from ..core.interfaces import ValidationService
from ..core.common import KumihanError, ErrorCategory, ValidationMixin, ValidationRule


class ValidationServiceImpl(ValidationService):
    """Centralized validation service implementation
    
    Provides schema-based validation with rule composition
    and custom validator registration.
    """
    
    def __init__(self):
        """Initialize validation service"""
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._validators: Dict[str, Callable] = {}
        self._rule_sets: Dict[str, List[ValidationRule]] = {}
        
        # Register built-in schemas and validators
        self._register_builtin_schemas()
        self._register_builtin_validators()
    
    def _register_builtin_schemas(self) -> None:
        """Register built-in validation schemas"""
        # Kumihan document schema
        kumihan_schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "author": {"type": "string"},
                        "version": {"type": "string"}
                    }
                }
            },
            "required": ["content"]
        }
        self.register_schema("kumihan_document", kumihan_schema)
        
        # Configuration schema
        config_schema = {
            "type": "object",
            "properties": {
                "debug": {"type": "boolean"},
                "cache": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "ttl": {"type": "integer", "minimum": 1}
                    }
                },
                "parser": {
                    "type": "object",
                    "properties": {
                        "strict_mode": {"type": "boolean"},
                        "max_file_size_mb": {"type": "integer", "minimum": 1, "maximum": 100}
                    }
                }
            }
        }
        self.register_schema("configuration", config_schema)
        
        # Plugin metadata schema
        plugin_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+"},
                "description": {"type": "string"},
                "author": {"type": "string"},
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "supported_formats": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["name", "version"]
        }
        self.register_schema("plugin_metadata", plugin_schema)
    
    def _register_builtin_validators(self) -> None:
        """Register built-in validator functions"""
        
        def validate_file_path(value: Any) -> bool:
            """Validate file path exists and is readable"""
            if not isinstance(value, (str, Path)):
                return False
            path = Path(value)
            return path.exists() and path.is_file()
        
        def validate_email(value: Any) -> bool:
            """Basic email validation"""
            if not isinstance(value, str):
                return False
            return "@" in value and "." in value.split("@")[-1]
        
        def validate_url(value: Any) -> bool:
            """Basic URL validation"""
            if not isinstance(value, str):
                return False
            return value.startswith(("http://", "https://"))
        
        def validate_semantic_version(value: Any) -> bool:
            """Validate semantic version format"""
            if not isinstance(value, str):
                return False
            import re
            pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$'
            return bool(re.match(pattern, value))
        
        self._validators.update({
            "file_path": validate_file_path,
            "email": validate_email,
            "url": validate_url,
            "semantic_version": validate_semantic_version
        })
    
    def validate(self, data: Any, schema: str) -> List[KumihanError]:
        """Validate data against schema
        
        Args:
            data: Data to validate
            schema: Schema identifier or definition
            
        Returns:
            List[KumihanError]: Validation errors (empty if valid)
        """
        if schema not in self._schemas:
            return [KumihanError(
                f"Unknown validation schema: {schema}",
                category=ErrorCategory.VALIDATION,
                user_message=f"不明な検証スキーマ: {schema}"
            )]
        
        schema_def = self._schemas[schema]
        return self._validate_against_schema(data, schema_def, schema)
    
    def _validate_against_schema(self, data: Any, schema_def: Dict[str, Any], schema_name: str) -> List[KumihanError]:
        """Validate data against schema definition
        
        Args:
            data: Data to validate
            schema_def: Schema definition
            schema_name: Schema name for error reporting
            
        Returns:
            List[KumihanError]: Validation errors
        """
        errors = []
        
        try:
            # Basic type validation
            expected_type = schema_def.get("type")
            if expected_type and not self._check_type(data, expected_type):
                errors.append(KumihanError(
                    f"Invalid type for schema '{schema_name}': expected {expected_type}",
                    category=ErrorCategory.VALIDATION,
                    user_message=f"型が不正です: {expected_type} が期待されています"
                ))
                return errors  # Don't continue if basic type is wrong
            
            # Object property validation
            if expected_type == "object" and isinstance(data, dict):
                errors.extend(self._validate_object_properties(data, schema_def, schema_name))
            
            # Array item validation
            elif expected_type == "array" and isinstance(data, list):
                errors.extend(self._validate_array_items(data, schema_def, schema_name))
            
            # String constraints
            elif expected_type == "string" and isinstance(data, str):
                errors.extend(self._validate_string_constraints(data, schema_def, schema_name))
            
            # Number constraints
            elif expected_type in ["integer", "number"] and isinstance(data, (int, float)):
                errors.extend(self._validate_number_constraints(data, schema_def, schema_name))
        
        except Exception as e:
            errors.append(KumihanError(
                f"Validation error for schema '{schema_name}': {e}",
                category=ErrorCategory.VALIDATION,
                cause=e
            ))
        
        return errors
    
    def _check_type(self, data: Any, expected_type: str) -> bool:
        """Check if data matches expected type"""
        if expected_type == "string":
            return isinstance(data, str)
        elif expected_type == "integer":
            return isinstance(data, int)
        elif expected_type == "number":
            return isinstance(data, (int, float))
        elif expected_type == "boolean":
            return isinstance(data, bool)
        elif expected_type == "array":
            return isinstance(data, list)
        elif expected_type == "object":
            return isinstance(data, dict)
        elif expected_type == "null":
            return data is None
        return True
    
    def _validate_object_properties(self, data: Dict[str, Any], schema_def: Dict[str, Any], schema_name: str) -> List[KumihanError]:
        """Validate object properties"""
        errors = []
        
        properties = schema_def.get("properties", {})
        required = schema_def.get("required", [])
        
        # Check required properties
        for req_prop in required:
            if req_prop not in data:
                errors.append(KumihanError(
                    f"Missing required property '{req_prop}' in schema '{schema_name}'",
                    category=ErrorCategory.VALIDATION,
                    user_message=f"必須プロパティ '{req_prop}' がありません"
                ))
        
        # Validate each property
        for prop_name, prop_value in data.items():
            if prop_name in properties:
                prop_schema = properties[prop_name]
                prop_errors = self._validate_against_schema(prop_value, prop_schema, f"{schema_name}.{prop_name}")
                errors.extend(prop_errors)
        
        return errors
    
    def _validate_array_items(self, data: List[Any], schema_def: Dict[str, Any], schema_name: str) -> List[KumihanError]:
        """Validate array items"""
        errors = []
        
        items_schema = schema_def.get("items")
        if items_schema:
            for i, item in enumerate(data):
                item_errors = self._validate_against_schema(item, items_schema, f"{schema_name}[{i}]")
                errors.extend(item_errors)
        
        # Array size constraints
        min_items = schema_def.get("minItems")
        max_items = schema_def.get("maxItems")
        
        if min_items is not None and len(data) < min_items:
            errors.append(KumihanError(
                f"Array too short in schema '{schema_name}': minimum {min_items} items",
                category=ErrorCategory.VALIDATION,
                user_message=f"配列が短すぎます: 最小 {min_items} 個必要"
            ))
        
        if max_items is not None and len(data) > max_items:
            errors.append(KumihanError(
                f"Array too long in schema '{schema_name}': maximum {max_items} items",
                category=ErrorCategory.VALIDATION,
                user_message=f"配列が長すぎます: 最大 {max_items} 個まで"
            ))
        
        return errors
    
    def _validate_string_constraints(self, data: str, schema_def: Dict[str, Any], schema_name: str) -> List[KumihanError]:
        """Validate string constraints"""
        errors = []
        
        min_length = schema_def.get("minLength")
        max_length = schema_def.get("maxLength")
        pattern = schema_def.get("pattern")
        
        if min_length is not None and len(data) < min_length:
            errors.append(KumihanError(
                f"String too short in schema '{schema_name}': minimum {min_length} characters",
                category=ErrorCategory.VALIDATION,
                user_message=f"文字列が短すぎます: 最小 {min_length} 文字必要"
            ))
        
        if max_length is not None and len(data) > max_length:
            errors.append(KumihanError(
                f"String too long in schema '{schema_name}': maximum {max_length} characters",
                category=ErrorCategory.VALIDATION,
                user_message=f"文字列が長すぎます: 最大 {max_length} 文字まで"
            ))
        
        if pattern:
            import re
            if not re.match(pattern, data):
                errors.append(KumihanError(
                    f"String does not match pattern in schema '{schema_name}': {pattern}",
                    category=ErrorCategory.VALIDATION,
                    user_message=f"文字列がパターンにマッチしません: {pattern}"
                ))
        
        return errors
    
    def _validate_number_constraints(self, data: Union[int, float], schema_def: Dict[str, Any], schema_name: str) -> List[KumihanError]:
        """Validate number constraints"""
        errors = []
        
        minimum = schema_def.get("minimum")
        maximum = schema_def.get("maximum")
        
        if minimum is not None and data < minimum:
            errors.append(KumihanError(
                f"Number too small in schema '{schema_name}': minimum {minimum}",
                category=ErrorCategory.VALIDATION,
                user_message=f"数値が小さすぎます: 最小 {minimum}"
            ))
        
        if maximum is not None and data > maximum:
            errors.append(KumihanError(
                f"Number too large in schema '{schema_name}': maximum {maximum}",
                category=ErrorCategory.VALIDATION,
                user_message=f"数値が大きすぎます: 最大 {maximum}"
            ))
        
        return errors
    
    def is_valid(self, data: Any, schema: str) -> bool:
        """Check if data is valid
        
        Args:
            data: Data to validate
            schema: Schema identifier
            
        Returns:
            bool: True if valid
        """
        errors = self.validate(data, schema)
        return len(errors) == 0
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a validation schema
        
        Args:
            name: Schema name
            schema: Schema definition
        """
        self._schemas[name] = schema
    
    def get_available_schemas(self) -> List[str]:
        """Get list of available schemas
        
        Returns:
            List[str]: Schema names
        """
        return list(self._schemas.keys())
    
    def register_validator(self, name: str, validator_func: Callable[[Any], bool]) -> None:
        """Register a custom validator function
        
        Args:
            name: Validator name
            validator_func: Function that returns True if value is valid
        """
        self._validators[name] = validator_func
    
    def get_available_validators(self) -> List[str]:
        """Get list of available custom validators
        
        Returns:
            List[str]: Validator names
        """
        return list(self._validators.keys())
    
    def create_rule_set(self, name: str, rules: List[ValidationRule]) -> None:
        """Create a named set of validation rules
        
        Args:
            name: Rule set name
            rules: List of validation rules
        """
        self._rule_sets[name] = rules
    
    def validate_with_rules(self, data: Dict[str, Any], rule_set_name: str) -> List[KumihanError]:
        """Validate data using a named rule set
        
        Args:
            data: Data to validate
            rule_set_name: Name of rule set to use
            
        Returns:
            List[KumihanError]: Validation errors
        """
        if rule_set_name not in self._rule_sets:
            return [KumihanError(
                f"Unknown rule set: {rule_set_name}",
                category=ErrorCategory.VALIDATION
            )]
        
        errors = []
        rules = self._rule_sets[rule_set_name]
        
        for rule in rules:
            for field_name, field_value in data.items():
                error = rule.validate(field_value)
                if error:
                    error.technical_details = f"Rule: {rule.name}, Field: {field_name}"
                    errors.append(error)
        
        return errors
    
    def load_schema_from_file(self, schema_name: str, file_path: Path) -> bool:
        """Load schema from JSON file
        
        Args:
            schema_name: Name to register schema under
            file_path: Path to JSON schema file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            self.register_schema(schema_name, schema)
            return True
        
        except Exception:
            return False