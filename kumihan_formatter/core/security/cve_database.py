"""
脆弱性スキャナー - CVEデータベース管理

CVE（Common Vulnerabilities and Exposures）データベース管理機能
vulnerability_scanner.pyから分離（Issue: 巨大ファイル分割 - 960行→200行程度）
"""

from typing import Any, Dict, List

from .vuln_types import CVERecord, ScannerConfig


class CVEDatabase:
    """CVEデータベース管理（簡略版）"""

    def __init__(self, config: ScannerConfig, logger: Any):
        self.config = config
        self.logger = logger
        self._cve_data: Dict[str, List[CVERecord]] = {}
        self._load_builtin_cve_data()

    def _load_builtin_cve_data(self) -> None:
        """組み込みCVEデータロード"""
        # 組み込みCVEデータ（実際の実装では外部データベース使用）
        self._cve_data = {
            "django": [
                CVERecord(
                    cve_id="CVE-2022-34265",
                    description="Django SQL injection vulnerability",
                    severity="HIGH",
                    score=8.8,
                    affected_versions=["<3.2.14", "<4.0.6"],
                    fixed_in="3.2.14, 4.0.6",
                    published_date="2022-07-04",
                )
            ],
            "pillow": [
                CVERecord(
                    cve_id="CVE-2022-22817",
                    description="Pillow buffer overflow vulnerability",
                    severity="HIGH",
                    score=9.8,
                    affected_versions=["<9.0.1"],
                    fixed_in="9.0.1",
                    published_date="2022-01-10",
                )
            ],
        }

    def lookup_cve(self, package_name: str, version: str) -> List[CVERecord]:
        """CVE検索"""
        results = []
        package_name = package_name.lower()

        if package_name in self._cve_data:
            for cve in self._cve_data[package_name]:
                # バージョンマッチング（簡略化）
                if self._version_affected(version, cve.affected_versions):
                    results.append(cve)

        return results

    def _version_affected(self, version: str, affected_versions: List[str]) -> bool:
        """バージョン影響チェック"""
        for affected in affected_versions:
            try:
                if affected.startswith("<"):
                    if version < affected[1:]:
                        return True
                elif affected.startswith("<="):
                    if version <= affected[2:]:
                        return True
                elif version == affected:
                    return True
            except Exception:
                continue
        return False


__all__ = ["CVEDatabase"]