"""
脆弱性スキャナー - 依存関係スキャナー

依存関係脆弱性検査機能
vulnerability_scanner.pyから分離（Issue: 巨大ファイル分割 - 960行→200行程度）
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .vuln_types import RiskLevel, ScanResult, ScannerConfig, VulnerabilityType


class DependencyScanner:
    """依存関係脆弱性スキャナー"""
    
    def __init__(self, config: ScannerConfig, logger: Any):
        self.config = config
        self.logger = logger
    
    def scan_requirements_file(self, file_path: Path) -> List[ScanResult]:
        """requirements.txtファイルのスキャン"""
        results: List[ScanResult] = []
        
        try:
            if not file_path.exists():
                return results
            
            content = file_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            
            for line_no, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # パッケージ名とバージョン抽出
                package_info = self._parse_requirement_line(line)
                if package_info:
                    vulnerability = self._check_dependency_vulnerability(package_info)
                    if vulnerability:
                        vulnerability.location = f"{file_path}:{line_no}"
                        results.append(vulnerability)
        
        except Exception as e:
            self.logger.error(f"Requirements file scan error: {e}")
        
        return results
    
    def scan_pyproject_toml(self, file_path: Path) -> List[ScanResult]:
        """pyproject.tomlファイルのスキャン"""
        results: List[ScanResult] = []
        
        try:
            import tomllib
            
            if not file_path.exists():
                return results
            
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
            
            dependencies = []
            
            # [project.dependencies]
            if "project" in data and "dependencies" in data["project"]:
                dependencies.extend(data["project"]["dependencies"])
            
            # [build-system.requires]
            if "build-system" in data and "requires" in data["build-system"]:
                dependencies.extend(data["build-system"]["requires"])
            
            for dep in dependencies:
                package_info = self._parse_requirement_line(dep)
                if package_info:
                    vulnerability = self._check_dependency_vulnerability(package_info)
                    if vulnerability:
                        vulnerability.location = str(file_path)
                        results.append(vulnerability)
        
        except ImportError:
            self.logger.warning("tomllib not available, skipping pyproject.toml scan")
        except Exception as e:
            self.logger.error(f"pyproject.toml scan error: {e}")
        
        return results
    
    def _parse_requirement_line(self, line: str) -> Optional[Dict[str, str]]:
        """要求行のパース"""
        try:
            # 基本的な形式: package==1.2.3, package>=1.0.0
            match = re.match(r"^([a-zA-Z0-9_-]+)\s*([><=!]+)\s*([0-9.]+)", line)
            if match:
                return {
                    "name": match.group(1).lower(),
                    "operator": match.group(2),
                    "version": match.group(3),
                }
            
            # パッケージ名のみ
            match = re.match(r"^([a-zA-Z0-9_-]+)$", line)
            if match:
                return {"name": match.group(1).lower(), "operator": "", "version": ""}
        
        except Exception:
            pass
        
        return None
    
    def _check_dependency_vulnerability(
        self, package_info: Dict[str, str]
    ) -> Optional[ScanResult]:
        """依存関係脆弱性チェック"""
        package_name = package_info["name"]
        version = package_info.get("version", "")
        
        # 既知の脆弱性パッケージデータベース（簡略版）
        vulnerable_packages: Dict[str, Dict[str, Any]] = {
            "django": {
                "vulnerable_versions": ["<3.2.16", "<4.0.8", "<4.1.3"],
                "description": (
                    "Django has known security vulnerabilities in older versions"
                ),
                "risk_level": RiskLevel.HIGH,
            },
            "flask": {
                "vulnerable_versions": ["<2.2.0"],
                "description": (
                    "Flask has known security vulnerabilities in older versions"
                ),
                "risk_level": RiskLevel.MEDIUM,
            },
            "requests": {
                "vulnerable_versions": ["<2.31.0"],
                "description": (
                    "Requests library has SSL certificate verification issues"
                ),
                "risk_level": RiskLevel.MEDIUM,
            },
            "pillow": {
                "vulnerable_versions": ["<9.3.0"],
                "description": "Pillow has image processing vulnerabilities",
                "risk_level": RiskLevel.HIGH,
            },
            "pyyaml": {
                "vulnerable_versions": ["<6.0"],
                "description": "PyYAML has unsafe loading vulnerabilities",
                "risk_level": RiskLevel.CRITICAL,
            },
        }
        
        if package_name in vulnerable_packages:
            vuln_data = vulnerable_packages[package_name]
            
            # バージョンチェック（簡略化）
            is_vulnerable = False
            if version:
                # 簡単なバージョン比較
                for vuln_version in vuln_data["vulnerable_versions"]:
                    if self._version_matches(version, vuln_version):
                        is_vulnerable = True
                        break
            else:
                # バージョン不明の場合は脆弱性ありと仮定
                is_vulnerable = True
            
            if is_vulnerable:
                return ScanResult(
                    vulnerability_type=VulnerabilityType.DEPENDENCY,
                    risk_level=vuln_data["risk_level"],
                    title=f"Vulnerable dependency: {package_name}",
                    description=vuln_data["description"],
                    location="",  # 後で設定
                    recommendation=f"Update {package_name} to a secure version",
                    details={
                        "package": package_name,
                        "current_version": version,
                        "vulnerable_versions": vuln_data["vulnerable_versions"],
                    },
                )
        
        return None
    
    def _version_matches(self, version: str, pattern: str) -> bool:
        """バージョンパターンマッチング（簡略化）"""
        try:
            if pattern.startswith("<"):
                pattern_version = pattern[1:]
                return version < pattern_version
            elif pattern.startswith("<="):
                pattern_version = pattern[2:]
                return version <= pattern_version
            elif pattern.startswith(">"):
                pattern_version = pattern[1:]
                return version > pattern_version
            elif pattern.startswith(">="):
                pattern_version = pattern[2:]
                return version >= pattern_version
            else:
                return version == pattern
        except Exception:
            return True  # 不明な場合は脆弱性ありと仮定


__all__ = ["DependencyScanner"]