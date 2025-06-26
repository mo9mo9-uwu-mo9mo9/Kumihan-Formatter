"""Validation and error handling for Kumihan-Formatter

This module provides comprehensive validation and error handling capabilities
for all components of the Kumihan-Formatter system.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .ast_nodes import Node, validate_ast
from .keyword_parser import KeywordParser, MarkerValidator
from .list_parser import ListParser, ListValidator
from .block_parser import BlockParser, BlockValidator
from .toc_generator import TOCValidator


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    level: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'structure', 'performance', 'style'
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    code: Optional[str] = None  # Error code for programmatic handling
    
    def is_error(self) -> bool:
        """Check if this is an error-level issue"""
        return self.level == 'error'
    
    def is_warning(self) -> bool:
        """Check if this is a warning-level issue"""
        return self.level == 'warning'
    
    def is_info(self) -> bool:
        """Check if this is an info-level issue"""
        return self.level == 'info'
    
    def format_message(self) -> str:
        """Format the issue message for display"""
        parts = []
        
        if self.line_number:
            parts.append(f"Line {self.line_number}")
            if self.column_number:
                parts.append(f":{self.column_number}")
        
        level_prefix = {
            'error': '❌ ERROR',
            'warning': '⚠️  WARNING', 
            'info': 'ℹ️  INFO'
        }.get(self.level, self.level.upper())
        
        parts.append(f"{level_prefix}: {self.message}")
        
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        
        return " ".join(parts)


class DocumentValidator:
    """Main validator for Kumihan documents"""
    
    def __init__(self, config=None):
        """Initialize validator with configuration"""
        self.config = config
        self.keyword_parser = KeywordParser(config)
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)
        
        # Initialize specialized validators
        self.marker_validator = MarkerValidator(self.keyword_parser)
        self.list_validator = ListValidator(self.list_parser)
        self.block_validator = BlockValidator(self.block_parser)
        self.toc_validator = TOCValidator()
        
        self.issues: List[ValidationIssue] = []
    
    def validate_text(self, text: str) -> List[ValidationIssue]:
        """
        Validate raw text input
        
        Args:
            text: Raw text to validate
        
        Returns:
            List[ValidationIssue]: List of validation issues
        """
        self.issues = []
        lines = text.split('\n')
        
        # Basic text validation
        self._validate_encoding(text)
        self._validate_line_structure(lines)
        self._validate_marker_syntax(lines)
        self._validate_list_syntax(lines)
        self._validate_document_structure(lines)
        
        return self.issues
    
    def validate_ast(self, ast: List[Node]) -> List[ValidationIssue]:
        """
        Validate parsed AST
        
        Args:
            ast: Parsed AST to validate
        
        Returns:
            List[ValidationIssue]: List of validation issues
        """
        self.issues = []
        
        # AST structure validation
        ast_issues = validate_ast(ast)
        for issue in ast_issues:
            self.issues.append(ValidationIssue(
                level='error',
                category='structure',
                message=issue
            ))
        
        # TOC validation
        toc_issues = self.toc_validator.validate_toc_structure(
            self._extract_toc_entries(ast)
        )
        for issue in toc_issues:
            self.issues.append(ValidationIssue(
                level='warning',
                category='structure',
                message=issue
            ))
        
        # Content validation
        self._validate_ast_content(ast)
        self._validate_ast_performance(ast)
        
        return self.issues
    
    def validate_file(self, file_path: Path) -> List[ValidationIssue]:
        """
        Validate a file
        
        Args:
            file_path: Path to file to validate
        
        Returns:
            List[ValidationIssue]: List of validation issues
        """
        self.issues = []
        
        try:
            # File existence and permissions
            if not file_path.exists():
                self.issues.append(ValidationIssue(
                    level='error',
                    category='file',
                    message=f"File not found: {file_path}",
                    code='FILE_NOT_FOUND'
                ))
                return self.issues
            
            if not file_path.is_file():
                self.issues.append(ValidationIssue(
                    level='error',
                    category='file',
                    message=f"Path is not a file: {file_path}",
                    code='NOT_A_FILE'
                ))
                return self.issues
            
            # Read and validate content
            try:
                text = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError as e:
                self.issues.append(ValidationIssue(
                    level='error',
                    category='encoding',
                    message=f"File encoding error: {e}",
                    suggestion="Ensure file is saved as UTF-8",
                    code='ENCODING_ERROR'
                ))
                return self.issues
            
            # Validate text content
            text_issues = self.validate_text(text)
            self.issues.extend(text_issues)
            
        except Exception as e:
            self.issues.append(ValidationIssue(
                level='error',
                category='file',
                message=f"Unexpected error reading file: {e}",
                code='FILE_READ_ERROR'
            ))
        
        return self.issues
    
    def _validate_encoding(self, text: str) -> None:
        """Validate text encoding and content"""
        # Check for common encoding issues
        if '\ufffd' in text:  # Replacement character
            self.issues.append(ValidationIssue(
                level='warning',
                category='encoding',
                message="Text contains replacement characters, possible encoding issue",
                suggestion="Check source file encoding"
            ))
        
        # Check for very long lines
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 1000:
                self.issues.append(ValidationIssue(
                    level='info',
                    category='style',
                    message="Very long line detected",
                    line_number=i + 1,
                    suggestion="Consider breaking long lines for readability"
                ))
    
    def _validate_line_structure(self, lines: List[str]) -> None:
        """Validate line-level structure"""
        for i, line in enumerate(lines):
            line_number = i + 1
            
            # Check for trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                self.issues.append(ValidationIssue(
                    level='info',
                    category='style',
                    message="Line has trailing whitespace",
                    line_number=line_number,
                    suggestion="Remove trailing whitespace"
                ))
            
            # Check for tabs vs spaces inconsistency
            if '\t' in line and '    ' in line:
                self.issues.append(ValidationIssue(
                    level='warning',
                    category='style',
                    message="Mixed tabs and spaces in line",
                    line_number=line_number,
                    suggestion="Use consistent indentation (spaces recommended)"
                ))
    
    def _validate_marker_syntax(self, lines: List[str]) -> None:
        """Validate marker syntax"""
        for i, line in enumerate(lines):
            line_number = i + 1
            line_stripped = line.strip()
            
            if line_stripped.startswith(';;;'):
                is_valid, errors = self.marker_validator.validate_marker_line(line_stripped)
                if not is_valid:
                    for error in errors:
                        self.issues.append(ValidationIssue(
                            level='error',
                            category='syntax',
                            message=error,
                            line_number=line_number,
                            code='INVALID_MARKER'
                        ))
    
    def _validate_list_syntax(self, lines: List[str]) -> None:
        """Validate list syntax"""
        list_issues = self.list_validator.validate_list_structure(lines)
        for issue in list_issues:
            self.issues.append(ValidationIssue(
                level='warning',
                category='syntax',
                message=issue,
                code='LIST_STRUCTURE'
            ))
    
    def _validate_document_structure(self, lines: List[str]) -> None:
        """Validate overall document structure"""
        structure_issues = self.block_validator.validate_document_structure(lines)
        for issue in structure_issues:
            self.issues.append(ValidationIssue(
                level='error',
                category='structure',
                message=issue,
                code='DOCUMENT_STRUCTURE'
            ))
    
    def _validate_ast_content(self, ast: List[Node]) -> None:
        """Validate AST content"""
        for node in ast:
            if isinstance(node, Node):
                # Check for empty content
                if not node.contains_text():
                    self.issues.append(ValidationIssue(
                        level='info',
                        category='content',
                        message=f"Empty {node.type} element",
                        suggestion="Consider removing empty elements"
                    ))
                
                # Validate specific node types
                if node.type == 'error':
                    self.issues.append(ValidationIssue(
                        level='error',
                        category='parsing',
                        message=f"Parse error: {node.content}",
                        line_number=node.get_attribute('line'),
                        code='PARSE_ERROR'
                    ))
    
    def _validate_ast_performance(self, ast: List[Node]) -> None:
        """Validate for performance issues"""
        # Check for excessive nesting
        max_depth = self._calculate_max_depth(ast)
        if max_depth > 10:
            self.issues.append(ValidationIssue(
                level='warning',
                category='performance',
                message=f"Deep nesting detected (depth: {max_depth})",
                suggestion="Consider simplifying document structure"
            ))
        
        # Check for too many nodes
        total_nodes = self._count_total_nodes(ast)
        if total_nodes > 1000:
            self.issues.append(ValidationIssue(
                level='info',
                category='performance',
                message=f"Large document ({total_nodes} nodes)",
                suggestion="Consider breaking into smaller documents"
            ))
    
    def _extract_toc_entries(self, ast: List[Node]) -> List:
        """Extract TOC entries from AST for validation"""
        # This would need to be implemented with actual TOC entry extraction
        return []
    
    def _calculate_max_depth(self, nodes: List[Node], current_depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        max_depth = current_depth
        for node in nodes:
            if isinstance(node, Node) and isinstance(node.content, list):
                child_depth = self._calculate_max_depth(node.content, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth
    
    def _count_total_nodes(self, nodes: List[Node]) -> int:
        """Count total number of nodes recursively"""
        count = 0
        for node in nodes:
            if isinstance(node, Node):
                count += 1
                if isinstance(node.content, list):
                    count += self._count_total_nodes(node.content)
        return count


class ValidationReporter:
    """Formats and reports validation results"""
    
    def __init__(self):
        pass
    
    def generate_report(self, issues: List[ValidationIssue], 
                       format_type: str = 'text') -> str:
        """
        Generate validation report
        
        Args:
            issues: List of validation issues
            format_type: Output format ('text', 'json', 'html')
        
        Returns:
            str: Formatted report
        """
        if format_type == 'json':
            return self._generate_json_report(issues)
        elif format_type == 'html':
            return self._generate_html_report(issues)
        else:
            return self._generate_text_report(issues)
    
    def _generate_text_report(self, issues: List[ValidationIssue]) -> str:
        """Generate text format report"""
        if not issues:
            return "✅ No validation issues found."
        
        lines = ["📋 Validation Report", "=" * 50]
        
        # Group by severity
        errors = [i for i in issues if i.is_error()]
        warnings = [i for i in issues if i.is_warning()]
        info = [i for i in issues if i.is_info()]
        
        lines.append(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        lines.append("")
        
        for level, items, icon in [
            ('ERRORS', errors, '❌'),
            ('WARNINGS', warnings, '⚠️ '),
            ('INFO', info, 'ℹ️ ')
        ]:
            if items:
                lines.append(f"{icon} {level} ({len(items)})")
                lines.append("-" * 30)
                for issue in items:
                    lines.append(f"  {issue.format_message()}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_json_report(self, issues: List[ValidationIssue]) -> str:
        """Generate JSON format report"""
        import json
        
        report_data = {
            'summary': {
                'total': len(issues),
                'errors': len([i for i in issues if i.is_error()]),
                'warnings': len([i for i in issues if i.is_warning()]),
                'info': len([i for i in issues if i.is_info()])
            },
            'issues': [
                {
                    'level': issue.level,
                    'category': issue.category,
                    'message': issue.message,
                    'line_number': issue.line_number,
                    'column_number': issue.column_number,
                    'suggestion': issue.suggestion,
                    'code': issue.code
                }
                for issue in issues
            ]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _generate_html_report(self, issues: List[ValidationIssue]) -> str:
        """Generate HTML format report"""
        if not issues:
            return "<div class='validation-success'>✅ No validation issues found.</div>"
        
        html_parts = [
            '<div class="validation-report">',
            '<h2>📋 Validation Report</h2>'
        ]
        
        # Summary
        errors = [i for i in issues if i.is_error()]
        warnings = [i for i in issues if i.is_warning()]
        info = [i for i in issues if i.is_info()]
        
        html_parts.append(
            f'<div class="summary">Summary: {len(errors)} errors, '
            f'{len(warnings)} warnings, {len(info)} info</div>'
        )
        
        # Issues by level
        for level, items, css_class in [
            ('Errors', errors, 'error'),
            ('Warnings', warnings, 'warning'),
            ('Info', info, 'info')
        ]:
            if items:
                html_parts.append(f'<div class="issue-group {css_class}">')
                html_parts.append(f'<h3>{level} ({len(items)})</h3>')
                html_parts.append('<ul>')
                for issue in items:
                    html_parts.append(f'<li>{issue.format_message()}</li>')
                html_parts.append('</ul>')
                html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)


class ErrorRecovery:
    """Handles error recovery and suggestion generation"""
    
    def __init__(self, validator: DocumentValidator):
        self.validator = validator
    
    def suggest_fixes(self, issues: List[ValidationIssue]) -> Dict[str, List[str]]:
        """
        Generate fix suggestions for validation issues
        
        Args:
            issues: List of validation issues
        
        Returns:
            Dict mapping issue codes to fix suggestions
        """
        suggestions = {}
        
        for issue in issues:
            if issue.code and issue.suggestion:
                if issue.code not in suggestions:
                    suggestions[issue.code] = []
                suggestions[issue.code].append(issue.suggestion)
        
        return suggestions
    
    def auto_fix_text(self, text: str, issues: List[ValidationIssue]) -> str:
        """
        Attempt to automatically fix simple issues
        
        Args:
            text: Original text
            issues: List of validation issues
        
        Returns:
            str: Text with automatic fixes applied
        """
        lines = text.split('\n')
        
        for issue in issues:
            if issue.line_number and issue.code in ['TRAILING_WHITESPACE']:
                # Fix trailing whitespace
                line_idx = issue.line_number - 1
                if line_idx < len(lines):
                    lines[line_idx] = lines[line_idx].rstrip()
        
        return '\n'.join(lines)