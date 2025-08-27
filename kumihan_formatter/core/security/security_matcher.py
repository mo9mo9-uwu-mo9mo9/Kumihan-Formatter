"""
入力検証システム - セキュリティパターンマッチャー

OWASP Top 10 攻撃パターンの高速マッチングエンジン
input_validator.pyから分離（Issue: 巨大ファイル分割 - 1017行→250行程度）
"""

import re
import threading
from functools import lru_cache
from typing import Any, Dict, List, Pattern

from .validation_types import ValidationSeverity


class SecurityPatternMatcher:
    """高速セキュリティパターンマッチングエンジン"""
    
    def __init__(self) -> None:
        self._compiled_patterns: Dict[str, Pattern[str]] = {}
        self._lock = threading.Lock()
        self._initialize_owasp_patterns()
    
    def _initialize_owasp_patterns(self) -> None:
        """OWASP Top 10パターンの初期化"""
        # A03: SQL Injection
        self.SQL_INJECTION_PATTERNS = [
            r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+"
            r"from|drop\s+table)",
            r"(?i)(\bor\b\s+\d+\s*=\s*\d+|\band\b\s+\d+\s*=\s*\d+)",
            r"(?i)(exec\s*\(|execute\s*\(|sp_executesql)",
            r"[\'\"];\s*(update|delete|insert|create|alter|drop)",
            r"(\%27|\%22|\'|\")(\%6F|\%4F|o|O)(\%72|\%52|r|R)",
            r"(?i)(information_schema|sys\.tables|pg_tables)",
            r"(?i)(waitfor\s+delay|benchmark\s*\(|sleep\s*\()",
        ]
        
        # A03: XSS (Cross-Site Scripting)
        self.XSS_PATTERNS = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"expression\s*\(",
            r"vbscript:",
            r"data:text/html",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<applet[^>]*>.*?</applet>",
        ]
        
        # A03: Command Injection
        self.COMMAND_INJECTION_PATTERNS = [
            r"[;&|`$(){}]",
            r"(\|\s*\w+|&&\s*\w+|;\s*\w+)",
            r"(nc\s|netcat\s|wget\s|curl\s)",
            r"(/bin/|/usr/bin/|cmd\.exe|powershell)",
            r"(\$\(.*?\)|\`.*?\`)",
            r"(>\s*/dev/null|2>&1|/dev/null)",
        ]
        
        # A01: Path Traversal
        self.PATH_TRAVERSAL_PATTERNS = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e\\",
            r"\.\.%2f",
            r"\.\.%5c",
        ]
        
        # A03: LDAP Injection
        self.LDAP_INJECTION_PATTERNS = [
            r"\(\s*\|\s*\(",
            r"\(\s*&\s*\(",
            r"\*\)",
            r"(\)\s*\(\s*\||\)\s*\(\s*&)",
        ]
        
        # A03: XML Injection
        self.XML_INJECTION_PATTERNS = [
            r"<!ENTITY",
            r"<!DOCTYPE",
            r"<\?xml",
            r"SYSTEM\s+[\"'][^\"']*[\"']",
            r"<!\[CDATA\[",
        ]
        
        # A10: SSRF (Server-Side Request Forgery)
        self.SSRF_PATTERNS = [
            r"(localhost|127\.0\.0\.1|0\.0\.0\.0)",
            r"(10\.|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[01]\.|192\.168\.)",
            r"(file://|ftp://|gopher://|dict://)",
            r"(@|%40)(localhost|127\.0\.0\.1)",
        ]
    
    @lru_cache(maxsize=1000)
    def compile_pattern(self, pattern: str) -> Pattern[str]:
        """パターンをコンパイルしてキャッシュ"""
        try:
            return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        except re.error:
            # フォールバック: エスケープして基本パターンとして処理
            return re.compile(re.escape(pattern), re.IGNORECASE)
    
    def match_owasp_patterns(self, input_str: str) -> List[Dict[str, Any]]:
        """OWASP Top 10パターンマッチング"""
        violations = []
        
        # 各攻撃パターンをチェック
        pattern_groups = [
            ("SQL_INJECTION", self.SQL_INJECTION_PATTERNS, ValidationSeverity.CRITICAL),
            ("XSS", self.XSS_PATTERNS, ValidationSeverity.HIGH),
            (
                "COMMAND_INJECTION",
                self.COMMAND_INJECTION_PATTERNS,
                ValidationSeverity.CRITICAL,
            ),
            ("PATH_TRAVERSAL", self.PATH_TRAVERSAL_PATTERNS, ValidationSeverity.HIGH),
            ("LDAP_INJECTION", self.LDAP_INJECTION_PATTERNS, ValidationSeverity.HIGH),
            ("XML_INJECTION", self.XML_INJECTION_PATTERNS, ValidationSeverity.MEDIUM),
            ("SSRF", self.SSRF_PATTERNS, ValidationSeverity.HIGH),
        ]
        
        for attack_type, patterns, severity in pattern_groups:
            for pattern_str in patterns:
                compiled_pattern = self.compile_pattern(pattern_str)
                matches = compiled_pattern.finditer(input_str)
                
                for match in matches:
                    violations.append(
                        {
                            "attack_type": attack_type,
                            "pattern": pattern_str,
                            "matched_text": match.group(0),
                            "position": match.span(),
                            "severity": severity.value,
                            "confidence": self._calculate_confidence(
                                match.group(0), attack_type
                            ),
                        }
                    )
        
        return violations
    
    def _calculate_confidence(self, matched_text: str, attack_type: str) -> float:
        """マッチ結果の信頼度を計算"""
        # 基本信頼度
        base_confidence = 0.7
        
        # 攻撃タイプ別調整
        type_multipliers = {
            "SQL_INJECTION": 0.9,
            "XSS": 0.85,
            "COMMAND_INJECTION": 0.95,
            "PATH_TRAVERSAL": 0.8,
            "LDAP_INJECTION": 0.75,
            "XML_INJECTION": 0.7,
            "SSRF": 0.8,
        }
        
        # マッチテキストの長さによる調整
        length_multiplier = min(1.0, len(matched_text) / 20.0)
        
        confidence = (
            base_confidence * type_multipliers.get(attack_type, 0.7) * length_multiplier
        )
        return min(0.99, max(0.1, confidence))


__all__ = ["SecurityPatternMatcher"]