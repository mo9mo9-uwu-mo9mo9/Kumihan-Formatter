"""
入力検証システム - 基本型・データクラス定義

OWASP Top 10 対応入力検証システムの基本型とデータクラス群
input_validator.pyから分離（Issue: 巨大ファイル分割 - 1017行→250行程度）
"""

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Pattern, Union


class ValidationSeverity(Enum):
    """検証違反の重要度レベル"""
    
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """検証ルール定義"""
    
    name: str
    pattern: Union[str, Pattern[str]]
    message: str
    severity: ValidationSeverity
    enabled: bool = True
    custom_validator: Optional[Callable[[str], bool]] = None


@dataclass
class ValidationResult:
    """検証結果"""
    
    is_valid: bool
    violations: List[Dict[str, Any]]
    risk_score: float
    processing_time_ms: float
    input_hash: str
    validation_timestamp: datetime


@dataclass
class ValidationConfig:
    """検証設定"""
    
    max_input_length: int = 1000000
    enable_unicode_normalization: bool = True
    performance_tracking: bool = True
    audit_logging: bool = True
    risk_threshold: float = 0.7
    cache_size: int = 1000


class ValidationStats:
    """検証統計・メトリクス管理"""
    
    def __init__(self) -> None:
        self.total_validations = 0
        self.violations_by_type: Dict[str, int] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.risk_scores: List[float] = []
        self._lock = threading.Lock()
    
    def record_validation(self, result: ValidationResult) -> None:
        """検証結果の統計記録"""
        with self._lock:
            self.total_validations += 1
            self.risk_scores.append(result.risk_score)
            
            # 処理時間記録
            if "processing_time" not in self.performance_metrics:
                self.performance_metrics["processing_time"] = []
            self.performance_metrics["processing_time"].append(
                result.processing_time_ms
            )
            
            # 違反タイプ別統計
            for violation in result.violations:
                attack_type = violation.get("attack_type", "UNKNOWN")
                self.violations_by_type[attack_type] = (
                    self.violations_by_type.get(attack_type, 0) + 1
                )
    
    def get_report(self) -> Dict[str, Any]:
        """統計レポート生成"""
        with self._lock:
            avg_processing_time = sum(
                self.performance_metrics.get("processing_time", [0])
            ) / max(1, len(self.performance_metrics.get("processing_time", [1])))
            
            avg_risk_score = sum(self.risk_scores) / max(1, len(self.risk_scores))
            
            return {
                "total_validations": self.total_validations,
                "violations_by_type": self.violations_by_type.copy(),
                "performance": {
                    "avg_processing_time_ms": round(avg_processing_time, 4),
                    "total_processing_time_ms": sum(
                        self.performance_metrics.get("processing_time", [0])
                    ),
                },
                "risk_analysis": {
                    "avg_risk_score": round(avg_risk_score, 4),
                    "max_risk_score": (
                        max(self.risk_scores) if self.risk_scores else 0.0
                    ),
                    "high_risk_count": len([s for s in self.risk_scores if s >= 0.8]),
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
    
    def export_to_file(self, file_path: str) -> None:
        """tmp/validation_reports/ 配下にレポート出力"""
        report_dir = Path("tmp/validation_reports")
        report_dir.mkdir(exist_ok=True)
        
        full_path = report_dir / file_path
        report_data = self.get_report()
        
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)


__all__ = [
    "ValidationSeverity", 
    "ValidationRule", 
    "ValidationResult", 
    "ValidationConfig", 
    "ValidationStats"
]