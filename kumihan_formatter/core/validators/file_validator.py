"""File validation for Kumihan documents

This module handles file-level validation including existence,
permissions, and encoding.
"""

from pathlib import Path

from .validation_issue import ValidationIssue


class FileValidator:
    """Validator for file-related issues"""

    def __init__(self) -> None:
        """Initialize file validator"""
        pass

    def validate_file_path(self, file_path: Path) -> list[ValidationIssue]:
        """Validate file path and permissions"""
        issues = []

        # Check file existence
        if not file_path.exists():
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"File not found: {file_path}",
                    code="FILE_NOT_FOUND",
                )
            )
            return issues

        # Check if it's a file
        if not file_path.is_file():
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"Path is not a file: {file_path}",
                    code="NOT_A_FILE",
                )
            )
            return issues

        # Check file extension
        if file_path.suffix.lower() != ".txt":
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="file",
                    message=f"File extension is not .txt: {file_path.suffix}",
                    suggestion="Kumihan-Formatter expects .txt files",
                    code="UNEXPECTED_EXTENSION",
                )
            )

        # Check permissions
        if not file_path.exists():
            return issues

        try:
            # Try to open for reading
            with open(file_path, "r", encoding="utf-8") as f:
                pass
        except PermissionError:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"Permission denied: {file_path}",
                    code="PERMISSION_DENIED",
                )
            )
        except UnicodeDecodeError:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"File is not valid UTF-8: {file_path}",
                    suggestion="Save the file with UTF-8 encoding",
                    code="INVALID_ENCODING",
                )
            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"Cannot read file: {str(e)}",
                    code="FILE_READ_ERROR",
                )
            )

        return issues

    def validate_output_path(self, output_path: Path) -> list[ValidationIssue]:
        """Validate output path"""
        issues = []

        # Check parent directory exists
        if not output_path.parent.exists():
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="file",
                    message=f"Output directory does not exist: {output_path.parent}",
                    suggestion="Directory will be created",
                    code="OUTPUT_DIR_MISSING",
                )
            )

        # Check if output file already exists
        if output_path.exists():
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="file",
                    message=f"Output file already exists: {output_path}",
                    suggestion="File will be overwritten",
                    code="OUTPUT_FILE_EXISTS",
                )
            )

        # Check write permissions
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Test write
            test_file = output_path.parent / ".test_write"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"Cannot write to directory: {output_path.parent}",
                    code="WRITE_PERMISSION_DENIED",
                )
            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"Output path error: {str(e)}",
                    code="OUTPUT_PATH_ERROR",
                )
            )

        return issues
