"""
脆弱性スキャナー - 基本型・データクラス定義

セキュリティ脆弱性検出システムの基本型とデータクラス群
vulnerability_scanner.pyから分離（Issue: 巨大ファイル分割 - 960行→200行程度）
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(Enum):
    """リスク評価レベル"""
    
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class VulnerabilityType(Enum):
    """脆弱性タイプ分類"""
    
    DEPENDENCY = "dependency"
    CODE_PATTERN = "code_pattern"
    RUNTIME_BEHAVIOR = "runtime_behavior"
    CVE_MATCH = "cve_match"
    CONFIGURATION = "configuration"


@dataclass
class CVERecord:
    """CVE脆弱性レコード"""
    
    cve_id: str
    description: str
    severity: str
    score: float
    affected_versions: List[str]
    fixed_in: Optional[str] = None
    published_date: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """スキャン結果データクラス"""
    
    vulnerability_type: VulnerabilityType
    risk_level: RiskLevel
    title: str
    description: str
    location: str
    recommendation: str
    details: Dict[str, Any] = field(default_factory=dict)
    cve_records: List[CVERecord] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class SecurityReport:
    """セキュリティレポート"""
    
    scan_id: str
    timestamp: str
    project_path: str
    scan_results: List[ScanResult]
    summary: Dict[str, Any]
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScannerConfig:
    """スキャナー設定"""
    
    enable_dependency_scan: bool = True
    enable_code_pattern_scan: bool = True
    enable_runtime_monitor: bool = True
    enable_cve_checks: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    scan_timeout: int = 300  # 5分
    parallel_workers: int = 4
    exclude_paths: List[str] = field(
        default_factory=lambda: [
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            "venv",
            ".venv",
        ]
    )
    exclude_extensions: List[str] = field(
        default_factory=lambda: [".pyc", ".pyo", ".so", ".dll", ".exe", ".bin"]
    )


__all__ = [
    "RiskLevel",
    "VulnerabilityType", 
    "CVERecord",
    "ScanResult",
    "SecurityReport",
    "ScannerConfig"
]