"""
入力検証システム - 高度入力バリデーター

OWASP Top 10完全対応 高性能入力検証システム
input_validator.pyから分離（Issue: 巨大ファイル分割 - 1017行→200行程度）
"""

import hashlib
import re
import threading
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union

from kumihan_formatter.core.logging.audit_logger import get_audit_logger
from kumihan_formatter.core.logging.structured_logger import get_structured_logger
from kumihan_formatter.core.utilities.logger import get_logger

from .security_matcher import SecurityPatternMatcher
from .validation_types import ValidationConfig, ValidationResult, ValidationRule, ValidationStats


class AdvancedInputValidator:
    """OWASP Top 10完全対応 高性能入力検証システム
    
    既存SecureInputValidatorとの完全な下位互換性を保持しつつ、
    エンタープライズセキュリティ機能を提供
    """
    
    # 既存のSecureInputValidatorパターン（互換性保持）
    SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]+$")
    DANGEROUS_PATTERNS = [
        r"\.\./",
        r"<script",
        r"javascript:",
        r"data:.*base64",
        r"[;&|`$(){}]",
    ]
    
    def __init__(self, config: Optional[ValidationConfig] = None) -> None:
        # ログシステム統合
        self.logger = get_logger(self.__class__.__name__)
        self.structured_logger = get_structured_logger("input_validation")
        self.audit_logger = get_audit_logger()
        
        # セキュリティパターンマッチャー
        self.pattern_matcher = SecurityPatternMatcher()
        
        # 統計・メトリクス
        self.validation_stats = ValidationStats()
        
        # 設定
        self.config = config or ValidationConfig()
        
        # カスタムルール管理
        self.custom_rules: List[ValidationRule] = []
        self._rules_lock = threading.Lock()
        
        self.logger.info("AdvancedInputValidator initialized with OWASP Top 10 support")
    
    def normalize_input(self, input_str: str) -> str:
        """Unicode正規化（NFKC）"""
        if self.config.enable_unicode_normalization:
            return unicodedata.normalize("NFKC", input_str)
        return input_str
    
    def _calculate_risk_score(self, violations: List[Dict[str, Any]]) -> float:
        """違反内容からリスクスコアを計算"""
        if not violations:
            return 0.0
        
        # 重要度別重み
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2,
            "info": 0.1,
        }
        
        total_score = 0.0
        for violation in violations:
            severity = violation.get("severity", "medium")
            confidence = violation.get("confidence", 0.7)
            weight = severity_weights.get(severity, 0.5)
            total_score += weight * confidence
        
        # 正規化（0.0-1.0）
        return min(1.0, total_score / max(1, len(violations)))
    
    def _create_input_hash(self, input_data: Any) -> str:
        """入力データのハッシュを生成"""
        data_str = str(input_data) if not isinstance(input_data, str) else input_data
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()[:16]
    
    def validate_input(
        self, data: Any, rules: List[ValidationRule]
    ) -> ValidationResult:
        """汎用入力検証"""
        start_time = time.perf_counter()
        
        # 入力の正規化
        if isinstance(data, str):
            normalized_input = self.normalize_input(data)
        else:
            normalized_input = str(data)
        
        # 基本的な長さチェック
        if len(normalized_input) > self.config.max_input_length:
            violation = {
                "attack_type": "INPUT_TOO_LONG",
                "severity": "high",
                "message": f"Input exceeds maximum length: "
                f"{len(normalized_input)} > {self.config.max_input_length}",
                "confidence": 1.0,
            }
            
            processing_time = (time.perf_counter() - start_time) * 1000
            result = ValidationResult(
                is_valid=False,
                violations=[violation],
                risk_score=1.0,
                processing_time_ms=processing_time,
                input_hash=self._create_input_hash(data),
                validation_timestamp=datetime.now(timezone.utc),
            )
            
            if self.config.performance_tracking:
                self.validation_stats.record_validation(result)
            
            return result
        
        # OWASP パターンマッチング
        owasp_violations = self.pattern_matcher.match_owasp_patterns(normalized_input)
        
        # カスタムルール適用
        custom_violations = []
        with self._rules_lock:
            for rule in rules + self.custom_rules:
                if not rule.enabled:
                    continue
                
                try:
                    if rule.custom_validator:
                        if not rule.custom_validator(normalized_input):
                            custom_violations.append(
                                {
                                    "attack_type": "CUSTOM_RULE",
                                    "rule_name": rule.name,
                                    "severity": rule.severity.value,
                                    "message": rule.message,
                                    "confidence": 0.9,
                                }
                            )
                    else:
                        pattern = (
                            rule.pattern
                            if isinstance(rule.pattern, Pattern)
                            else self.pattern_matcher.compile_pattern(str(rule.pattern))
                        )
                        if pattern.search(normalized_input):
                            custom_violations.append(
                                {
                                    "attack_type": "CUSTOM_RULE",
                                    "rule_name": rule.name,
                                    "severity": rule.severity.value,
                                    "message": rule.message,
                                    "confidence": 0.8,
                                }
                            )
                except Exception as e:
                    self.logger.warning(f"Error applying custom rule {rule.name}: {e}")
        
        # 結果の生成
        all_violations = owasp_violations + custom_violations
        risk_score = self._calculate_risk_score(all_violations)
        processing_time = (time.perf_counter() - start_time) * 1000
        
        result = ValidationResult(
            is_valid=len(all_violations) == 0,
            violations=all_violations,
            risk_score=risk_score,
            processing_time_ms=processing_time,
            input_hash=self._create_input_hash(data),
            validation_timestamp=datetime.now(timezone.utc),
        )
        
        # 統計記録
        if self.config.performance_tracking:
            self.validation_stats.record_validation(result)
        
        # 監査ログ記録（高リスク時）
        if self.config.audit_logging and risk_score >= self.config.risk_threshold:
            self.audit_logger.log_security_event(
                event_type="high_risk_input_detected",
                user_id="system",
                details={
                    "input_hash": result.input_hash,
                    "risk_score": risk_score,
                    "violations_count": len(all_violations),
                    "processing_time_ms": processing_time,
                },
            )
        
        # 構造化ログ
        if all_violations:
            self.structured_logger.warning(
                f"Input validation violations detected: {len(all_violations)} issues",
                extra={
                    "input_hash": result.input_hash,
                    "risk_score": risk_score,
                    "violations": [v.get("attack_type") for v in all_violations],
                },
            )
        
        return result
    
    def create_custom_rule(
        self,
        name: str,
        pattern: str,
        message: str,
        severity=None,  # ValidationSeverity.MEDIUM のデフォルト
    ):
        """カスタム検証ルール作成"""
        from .validation_types import ValidationSeverity
        if severity is None:
            severity = ValidationSeverity.MEDIUM
            
        rule = ValidationRule(
            name=name, pattern=pattern, message=message, severity=severity
        )
        
        with self._rules_lock:
            self.custom_rules.append(rule)
        
        self.logger.info(f"Custom validation rule created: {name}")
        
        return rule
    
    def bulk_validate(
        self, inputs: List[Any], rules: List[ValidationRule]
    ) -> List[ValidationResult]:
        """バッチ検証（高性能処理）"""
        results = []
        start_time = time.perf_counter()
        
        for input_data in inputs:
            result = self.validate_input(input_data, rules)
            results.append(result)
        
        total_time = (time.perf_counter() - start_time) * 1000
        self.structured_logger.info(
            f"Bulk validation completed: {len(inputs)} inputs in {total_time:.2f}ms",
            extra={
                "inputs_count": len(inputs),
                "total_time_ms": total_time,
                "avg_time_per_input": total_time / max(1, len(inputs)),
            },
        )
        
        return results
    
    def get_validation_report(self) -> Dict[str, Any]:
        """検証レポート取得"""
        return self.validation_stats.get_report()
    
    def export_validation_report(self, filename: Optional[str] = None) -> None:
        """検証レポートをファイルに出力"""
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}.json"
        
        self.validation_stats.export_to_file(filename)
        self.logger.info(f"Validation report exported: {filename}")
    
    # === 既存SecureInputValidator互換メソッド ===
    
    @classmethod
    def validate_file_path(cls, file_path: Union[str, Path]) -> bool:
        """既存メソッド: ファイルパスの安全性検証（互換性保持）"""
        try:
            path_str = str(file_path)
            
            # 基本的な危険パターンチェック（既存ロジック）
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, path_str, re.IGNORECASE):
                    return False
            
            # パストラバーサル攻撃の検出（既存ロジック）
            import os
            normalized = os.path.normpath(path_str)
            if ".." in normalized or normalized.startswith("/"):
                return False
            
            # 文字種制限チェック（既存ロジック）
            if not cls.SAFE_PATH_PATTERN.match(path_str):
                return False
            
            return True
            
        except (TypeError, ValueError):
            return False
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """既存メソッド: ファイル名のサニタイズ（互換性保持）"""
        # 既存ロジックの完全再現
        sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
        
        if sanitized.startswith("."):
            sanitized = "_" + sanitized[1:]
        
        if not sanitized:
            sanitized = "unnamed_file"
        
        return sanitized[:255]
    
    @classmethod
    def validate_text_content(cls, content: str, max_length: int = 1000000) -> bool:
        """既存メソッド: テキスト内容の検証（互換性保持）"""
        try:
            # 既存ロジック: 長さ制限
            if len(content) > max_length:
                return False
            
            # 既存ロジック: バイナリデータの混入チェック
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                return False
            
            # 既存ロジック: 危険なパターンの検出
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    return False
            
            return True
            
        except (TypeError, AttributeError):
            return False
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """既存メソッド: URL の安全性検証（互換性保持）"""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            
            # 既存ロジック: プロトコル制限
            if parsed.scheme not in ["http", "https", "ftp"]:
                return False
            
            # 既存ロジック: ローカルファイルシステムアクセス防止
            if parsed.scheme == "file":
                return False
            
            # 既存ロジック: プライベートIP範囲への接続防止
            if parsed.hostname:
                if parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    return False
            
            return True
            
        except (ValueError, TypeError):
            return False


__all__ = ["AdvancedInputValidator"]