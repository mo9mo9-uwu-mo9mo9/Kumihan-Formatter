"""
脆弱性スキャナー - コードパターンスキャナー

コードパターン脆弱性検出機能
vulnerability_scanner.pyから分離（Issue: 巨大ファイル分割 - 960行→200行程度）
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List

from .vuln_types import RiskLevel, ScanResult, ScannerConfig, VulnerabilityType


class CodePatternScanner:
    """コードパターン脆弱性スキャナー"""

    # 危険な関数・パターン定義
    DANGEROUS_FUNCTIONS: Dict[str, Dict[str, Any]] = {
        "eval": {
            "risk_level": RiskLevel.CRITICAL,
            "description": "eval() function allows arbitrary code execution",
            "recommendation": "Use ast.literal_eval() or avoid dynamic evaluation",
        },
        "exec": {
            "risk_level": RiskLevel.CRITICAL,
            "description": "exec() function allows arbitrary code execution",
            "recommendation": "Avoid dynamic code execution",
        },
        "compile": {
            "risk_level": RiskLevel.HIGH,
            "description": "compile() can execute arbitrary code",
            "recommendation": "Validate input before compilation",
        },
        "__import__": {
            "risk_level": RiskLevel.HIGH,
            "description": "Dynamic imports can be security risks",
            "recommendation": "Use static imports when possible",
        },
    }

    # セキュリティパターン
    SECURITY_PATTERNS: List[Dict[str, Any]] = [
        {
            "pattern": r"subprocess\.call.*shell\s*=\s*True",
            "risk_level": RiskLevel.CRITICAL,
            "title": "Command injection vulnerability",
            "description": "subprocess with shell=True can lead to command injection",
            "recommendation": "Use subprocess without shell=True and validate inputs",
        },
        {
            "pattern": r"os\.system\s*\(",
            "risk_level": RiskLevel.CRITICAL,
            "title": "OS command execution",
            "description": "os.system() can execute arbitrary system commands",
            "recommendation": ("Use subprocess module with proper input validation"),
        },
        {
            "pattern": r"pickle\.loads?\s*\(",
            "risk_level": RiskLevel.HIGH,
            "title": "Unsafe deserialization",
            "description": (
                "pickle.load() can execute arbitrary code during deserialization"
            ),
            "recommendation": "Use safer serialization formats like JSON",
        },
        {
            "pattern": r"yaml\.load\s*\([^,)]*\)",
            "risk_level": RiskLevel.HIGH,
            "title": "Unsafe YAML loading",
            "description": "yaml.load() without Loader parameter is unsafe",
            "recommendation": "Use yaml.safe_load() or yaml.load() with SafeLoader",
        },
        {
            "pattern": r"(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
            "risk_level": RiskLevel.MEDIUM,
            "title": "Hardcoded credentials",
            "description": "Hardcoded credentials found in source code",
            "recommendation": "Use environment variables or secure configuration",
        },
        {
            "pattern": r"\.format\([^)]*\{.*\}[^)]*\)",
            "risk_level": RiskLevel.LOW,
            "title": "Potential format string vulnerability",
            "description": "Dynamic string formatting can be vulnerable",
            "recommendation": "Use parameterized queries or validate format strings",
        },
    ]

    def __init__(self, config: ScannerConfig, logger: Any):
        self.config = config
        self.logger = logger

    def scan_file(self, file_path: Path) -> List[ScanResult]:
        """単一ファイルのスキャン"""
        results: List[ScanResult] = []

        try:
            if file_path.stat().st_size > self.config.max_file_size:
                return results

            content = file_path.read_text(encoding="utf-8")

            # AST解析による関数呼び出しチェック
            ast_results = self._scan_ast(file_path, content)
            results.extend(ast_results)

            # 正規表現パターンチェック
            pattern_results = self._scan_patterns(file_path, content)
            results.extend(pattern_results)

        except Exception as e:
            self.logger.error(f"File scan error for {file_path}: {e}")

        return results

    def _scan_ast(self, file_path: Path, content: str) -> List[ScanResult]:
        """AST解析によるスキャン"""
        results: List[ScanResult] = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func)
                    if func_name in self.DANGEROUS_FUNCTIONS:
                        func_data = self.DANGEROUS_FUNCTIONS[func_name]

                        results.append(
                            ScanResult(
                                vulnerability_type=VulnerabilityType.CODE_PATTERN,
                                risk_level=func_data["risk_level"],
                                title=f"Dangerous function: {func_name}()",
                                description=func_data["description"],
                                location=f"{file_path}:{node.lineno}",
                                recommendation=func_data["recommendation"],
                                details={"function": func_name, "line": node.lineno},
                            )
                        )

        except SyntaxError:
            # 構文エラーファイルはスキップ
            pass
        except Exception as e:
            self.logger.error(f"AST scan error: {e}")

        return results

    def _scan_patterns(self, file_path: Path, content: str) -> List[ScanResult]:
        """正規表現パターンスキャン"""
        results: List[ScanResult] = []
        lines = content.split("\n")

        for pattern_data in self.SECURITY_PATTERNS:
            pattern = pattern_data["pattern"]

            for line_no, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    results.append(
                        ScanResult(
                            vulnerability_type=VulnerabilityType.CODE_PATTERN,
                            risk_level=pattern_data["risk_level"],
                            title=pattern_data["title"],
                            description=pattern_data["description"],
                            location=f"{file_path}:{line_no}",
                            recommendation=pattern_data["recommendation"],
                            details={"pattern": pattern, "line_content": line.strip()},
                        )
                    )

        return results

    def _get_function_name(self, node: ast.AST) -> str:
        """関数名取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""


__all__ = ["CodePatternScanner"]