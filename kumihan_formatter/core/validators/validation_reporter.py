"""Validation report generation

This module formats and reports validation results in various formats.
"""

import json
from typing import List

from .validation_issue import ValidationIssue


class ValidationReporter:
    """Formats and reports validation results"""

    def __init__(self) -> None:
        pass

    def generate_report(
        self, issues: list[ValidationIssue], format_type: str = "text"
    ) -> str:
        """
        Generate validation report

        Args:
            issues: List of validation issues
            format_type: Output format ('text', 'json', 'html')

        Returns:
            str: Formatted report
        """
        if format_type == "json":
            return self._generate_json_report(issues)
        elif format_type == "html":
            return self._generate_html_report(issues)
        else:
            return self._generate_text_report(issues)

    def _generate_text_report(self, issues: list[ValidationIssue]) -> str:
        """Generate text format report"""
        if not issues:
            return "✅ No validation issues found."

        lines = ["📋 Validation Report", "=" * 50]

        # Group by severity
        errors = [i for i in issues if i.is_error()]
        warnings = [i for i in issues if i.is_warning()]
        info = [i for i in issues if i.is_info()]

        lines.append(
            f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info"
        )
        lines.append("")

        for level, items, icon in [
            ("ERRORS", errors, "❌"),
            ("WARNINGS", warnings, "⚠️ "),
            ("INFO", info, "ℹ️ "),
        ]:
            if items:
                lines.append(f"{icon} {level} ({len(items)})")
                lines.append("-" * 30)
                for issue in items:
                    lines.append(f"  {issue.format_message()}")
                lines.append("")

        return "\n".join(lines)

    def _generate_json_report(self, issues: list[ValidationIssue]) -> str:
        """Generate JSON format report"""
        report_data = {
            "summary": {
                "total": len(issues),
                "errors": len([i for i in issues if i.is_error()]),
                "warnings": len([i for i in issues if i.is_warning()]),
                "info": len([i for i in issues if i.is_info()]),
            },
            "issues": [
                {
                    "level": issue.level,
                    "category": issue.category,
                    "message": issue.message,
                    "line_number": issue.line_number,
                    "column_number": issue.column_number,
                    "suggestion": issue.suggestion,
                    "code": issue.code,
                }
                for issue in issues
            ],
        }

        return json.dumps(report_data, ensure_ascii=False, indent=2)

    def _generate_html_report(self, issues: list[ValidationIssue]) -> str:
        """Generate HTML format report"""
        if not issues:
            return (
                "<div class='validation-success'>✅ No validation issues found.</div>"
            )

        html_parts = [
            '<div class="validation-report">',
            "<h2>📋 Validation Report</h2>",
        ]

        # Summary
        errors = [i for i in issues if i.is_error()]
        warnings = [i for i in issues if i.is_warning()]
        info = [i for i in issues if i.is_info()]

        html_parts.append(
            f'<div class="summary">Summary: {len(errors)} errors, '
            f"{len(warnings)} warnings, {len(info)} info</div>"
        )

        # Issues by category
        for level, items, class_name in [
            ("Errors", errors, "errors"),
            ("Warnings", warnings, "warnings"),
            ("Info", info, "info"),
        ]:
            if items:
                html_parts.append(f'<div class="{class_name}">')
                html_parts.append(f"<h3>{level} ({len(items)})</h3>")
                html_parts.append("<ul>")
                for issue in items:
                    html_parts.append("<li>")
                    if issue.line_number:
                        html_parts.append(
                            f'<span class="line-number">Line {issue.line_number}</span> '
                        )
                    html_parts.append(f'<span class="message">{issue.message}</span>')
                    if issue.suggestion:
                        html_parts.append(
                            f' <span class="suggestion">({issue.suggestion})</span>'
                        )
                    html_parts.append("</li>")
                html_parts.append("</ul>")
                html_parts.append("</div>")

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def print_summary(self, issues: list[ValidationIssue]) -> None:
        """Print a summary of validation issues to console"""
        errors = sum(1 for i in issues if i.is_error())
        warnings = sum(1 for i in issues if i.is_warning())
        info = sum(1 for i in issues if i.is_info())

        if not issues:
            print("✅ No validation issues found.")
        else:
            print(
                f"Validation complete: {errors} errors, {warnings} warnings, {info} info"
            )

            if errors > 0:
                print("❌ Errors must be fixed before proceeding.")
            elif warnings > 0:
                print("⚠️  Consider addressing warnings for better quality.")
            else:
                print("ℹ️  Review informational messages.")
