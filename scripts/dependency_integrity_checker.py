#!/usr/bin/env python3
"""
Dependency Integrity Checker - Issue #640 Phase 3
依存関係整合性自動検出システム

目的: プロジェクト依存関係の整合性と安全性確認
- 依存関係バージョン競合検出
- セキュリティ脆弱性チェック
- ライセンス互換性確認
- 不要依存関係検出
"""

import os
import sys
import json
import subprocess
# Optional dependency with proper error handling
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None
import packaging.version
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import tomllib
import tempfile
import hashlib

from scripts.tdd_system_base import TDDSystemBase, create_tdd_config, TDDSystemError
from scripts.secure_subprocess import secure_run
from scripts.security_utils import load_security_config, should_scan_file
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

class DependencyRisk(Enum):
    """依存関係リスクレベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"

@dataclass
class DependencyIssue:
    """依存関係問題"""
    package_name: str
    current_version: Optional[str]
    issue_type: str
    severity: DependencyRisk
    description: str
    recommendation: str
    vulnerability_id: Optional[str]
    affected_versions: Optional[str]
    fixed_version: Optional[str]
    license_issue: Optional[str]
    dependency_path: List[str]

@dataclass
class DependencyInfo:
    """依存関係情報"""
    name: str
    version: str
    license: Optional[str]
    description: Optional[str]
    dependencies: List[str]
    required_by: List[str]
    is_dev_dependency: bool
    is_direct_dependency: bool
    size: Optional[int]
    last_updated: Optional[datetime]

@dataclass
class DependencyTestResult:
    """依存関係テスト結果"""
    total_dependencies: int
    direct_dependencies: int
    transitive_dependencies: int
    security_issues: List[DependencyIssue]
    license_issues: List[DependencyIssue]
    version_conflicts: List[DependencyIssue]
    unused_dependencies: List[str]
    outdated_dependencies: List[DependencyIssue]
    dependency_tree: Dict[str, DependencyInfo]
    test_duration: float
    timestamp: datetime
    overall_risk: DependencyRisk
    recommendations: List[str]

class DependencyIntegrityChecker(TDDSystemBase):
    """依存関係整合性自動検出システム"""
    
    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)
        
        # 設定ファイルパス
        self.pyproject_toml = project_root / "pyproject.toml"
        self.requirements_txt = project_root / "requirements.txt"
        self.poetry_lock = project_root / "poetry.lock"
        
        # 設定を外部から読み込み
        security_config = load_security_config()
        
        # ライセンス互換性マトリックス
        self.license_compatibility = security_config.get('license_compatibility', {})
        
        # 問題あるライセンス
        self.problematic_licenses = security_config.get('problematic_licenses', [])
        
        # 既知の脆弱性パッケージ情報
        self.known_vulnerable = security_config.get('known_vulnerable_packages', {})
        
        # セキュリティデータベースURL
        self.security_db_url = "https://pyup.io/api/v1/safety/"
        
        self.dependency_tree = {}
        self.security_issues = []
        self.license_issues = []
        
        # requests依存関係チェック
        if not HAS_REQUESTS:
            logger.warning("requests not available - vulnerability checking disabled")
            logger.info("Install requests package for enhanced vulnerability checking: pip install requests")
        self.version_conflicts = []
        self.unused_deps = []
        self.outdated_deps = []
    
    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 依存関係整合性チェックシステム初期化中...")
        
        # プロジェクト設定ファイル確認
        config_files = [self.pyproject_toml, self.requirements_txt]
        found_configs = [f for f in config_files if f.exists()]
        
        if not found_configs:
            logger.error("プロジェクト設定ファイルが見つかりません (pyproject.toml, requirements.txt)")
            return False
        
        logger.info(f"設定ファイル検出: {[f.name for f in found_configs]}")
        
        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("✅ 依存関係整合性チェックシステム初期化完了")
        return True
    
    def execute_main_operation(self) -> DependencyTestResult:
        """依存関係整合性チェック実行"""
        logger.info("🚀 依存関係整合性チェック開始...")
        
        start_time = datetime.now()
        
        try:
            # 依存関係情報収集
            self._collect_dependency_info()
            
            # セキュリティ脆弱性チェック
            self._check_security_vulnerabilities()
            
            # ライセンス互換性チェック
            self._check_license_compatibility()
            
            # バージョン競合チェック
            self._check_version_conflicts()
            
            # 未使用依存関係チェック
            self._check_unused_dependencies()
            
            # 古い依存関係チェック
            self._check_outdated_dependencies()
            
            # 結果を分析
            result = self._analyze_results(start_time)
            
            # レポート生成
            self._generate_dependency_report(result)
            
            logger.info(f"✅ 依存関係整合性チェック完了: {len(self.security_issues + self.license_issues + self.version_conflicts)}件の問題発見")
            return result
            
        except Exception as e:
            logger.error(f"依存関係チェック実行エラー: {e}")
            raise TDDSystemError(f"チェック実行失敗: {e}")
    
    def _collect_dependency_info(self):
        """依存関係情報収集"""
        logger.info("📋 依存関係情報収集中...")
        
        # pyproject.tomlから依存関係読み込み
        if self.pyproject_toml.exists():
            self._parse_pyproject_toml()
        
        # requirements.txtから依存関係読み込み
        if self.requirements_txt.exists():
            self._parse_requirements_txt()
        
        # pip showで詳細情報取得
        self._get_installed_package_info()
        
        logger.info(f"依存関係情報収集完了: {len(self.dependency_tree)}パッケージ")
    
    def _parse_pyproject_toml(self):
        """pyproject.toml解析"""
        try:
            with open(self.pyproject_toml, 'rb') as f:
                data = tomllib.load(f)
            
            # 直接依存関係
            deps = data.get('project', {}).get('dependencies', [])
            for dep in deps:
                package_name, version_spec = self._parse_dependency_spec(dep)
                if package_name:
                    self.dependency_tree[package_name] = DependencyInfo(
                        name=package_name,
                        version=version_spec or 'unknown',
                        license=None,
                        description=None,
                        dependencies=[],
                        required_by=[],
                        is_dev_dependency=False,
                        is_direct_dependency=True,
                        size=None,
                        last_updated=None
                    )
            
            # 開発依存関係
            dev_deps = data.get('project', {}).get('optional-dependencies', {}).get('dev', [])
            for dep in dev_deps:
                package_name, version_spec = self._parse_dependency_spec(dep)
                if package_name:
                    self.dependency_tree[package_name] = DependencyInfo(
                        name=package_name,
                        version=version_spec or 'unknown',
                        license=None,
                        description=None,
                        dependencies=[],
                        required_by=[],
                        is_dev_dependency=True,
                        is_direct_dependency=True,
                        size=None,
                        last_updated=None
                    )
                    
        except Exception as e:
            logger.warning(f"pyproject.toml解析エラー: {e}")
    
    def _parse_requirements_txt(self):
        """requirements.txt解析"""
        try:
            with open(self.requirements_txt, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    package_name, version_spec = self._parse_dependency_spec(line)
                    if package_name and package_name not in self.dependency_tree:
                        self.dependency_tree[package_name] = DependencyInfo(
                            name=package_name,
                            version=version_spec or 'unknown',
                            license=None,
                            description=None,
                            dependencies=[],
                            required_by=[],
                            is_dev_dependency=False,
                            is_direct_dependency=True,
                            size=None,
                            last_updated=None
                        )
                        
        except Exception as e:
            logger.warning(f"requirements.txt解析エラー: {e}")
    
    def _parse_dependency_spec(self, dep_spec: str) -> Tuple[Optional[str], Optional[str]]:
        """依存関係仕様解析"""
        # 基本的な解析（簡易版）
        spec = dep_spec.strip()
        
        # コメント除去
        if '#' in spec:
            spec = spec.split('#')[0].strip()
        
        if not spec:
            return None, None
        
        # バージョン指定分離
        import re
        match = re.match(r'^([a-zA-Z0-9\-_.]+)\s*([><=!~]*\s*[0-9.]+.*)?$', spec)
        if match:
            package_name = match.group(1)
            version_spec = match.group(2).strip() if match.group(2) else None
            return package_name, version_spec
        
        return spec, None
    
    def _get_installed_package_info(self):
        """インストール済みパッケージ情報取得"""
        try:
            # pip listで全パッケージ取得
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--format=json'
            ], capture_output=True, text=True, check=True)
            
            installed_packages = json.loads(result.stdout)
            
            for pkg in installed_packages:
                pkg_name = pkg['name']
                pkg_version = pkg['version']
                
                # 詳細情報取得
                pkg_info = self._get_package_details(pkg_name)
                
                if pkg_name in self.dependency_tree:
                    # 既存エントリを更新
                    self.dependency_tree[pkg_name].version = pkg_version
                    self.dependency_tree[pkg_name].license = pkg_info.get('license')
                    self.dependency_tree[pkg_name].description = pkg_info.get('summary')
                else:
                    # 新規エントリ作成（推移的依存関係）
                    self.dependency_tree[pkg_name] = DependencyInfo(
                        name=pkg_name,
                        version=pkg_version,
                        license=pkg_info.get('license'),
                        description=pkg_info.get('summary'),
                        dependencies=[],
                        required_by=[],
                        is_dev_dependency=False,
                        is_direct_dependency=False,
                        size=None,
                        last_updated=None
                    )
                    
        except Exception as e:
            logger.warning(f"インストール済みパッケージ情報取得エラー: {e}")
    
    def _get_package_details(self, package_name: str) -> Dict:
        """パッケージ詳細情報取得"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'show', package_name
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
            
            details = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    details[key.strip().lower()] = value.strip()
            
            return details
            
        except Exception as e:
            logger.debug(f"パッケージ詳細取得エラー {package_name}: {e}")
            return {}
    
    def _check_security_vulnerabilities(self):
        """セキュリティ脆弱性チェック"""
        logger.info("🔒 セキュリティ脆弱性チェック中...")
        
        try:
            # safety check実行（pipパッケージ）
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'safety', '--quiet'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # safetyでチェック実行
                safety_result = subprocess.run([
                    sys.executable, '-m', 'safety', 'check', '--json'
                ], capture_output=True, text=True)
                
                if safety_result.returncode == 0 and safety_result.stdout:
                    try:
                        vulns = json.loads(safety_result.stdout)
                        for vuln in vulns:
                            issue = DependencyIssue(
                                package_name=vuln.get('package', 'unknown'),
                                current_version=vuln.get('installed_version'),
                                issue_type='security_vulnerability',
                                severity=self._assess_vulnerability_severity(vuln),
                                description=vuln.get('advisory', 'セキュリティ脆弱性'),
                                recommendation=f"バージョン {vuln.get('safe_versions', 'latest')} にアップデートしてください",
                                vulnerability_id=vuln.get('id'),
                                affected_versions=vuln.get('specs', []),
                                fixed_version=vuln.get('safe_versions'),
                                license_issue=None,
                                dependency_path=[]
                            )
                            self.security_issues.append(issue)
                    except json.JSONDecodeError:
                        logger.warning("safety check結果の解析に失敗")
                        
        except Exception as e:
            logger.warning(f"セキュリティ脆弱性チェックエラー: {e}")
            # フォールバック: 簡易チェック
            self._simple_security_check()
    
    def _simple_security_check(self):
        """簡易セキュリティチェック"""
        
        for pkg_name, pkg_info in self.dependency_tree.items():
            if pkg_name.lower() in self.known_vulnerable:
                vulns = self.known_vulnerable[pkg_name.lower()]
                for version_spec, cve_id in vulns.items():
                    if self._version_matches_spec(pkg_info.version, version_spec):
                        issue = DependencyIssue(
                            package_name=pkg_name,
                            current_version=pkg_info.version,
                            issue_type='security_vulnerability',
                            severity=DependencyRisk.HIGH,
                            description=f"既知の脆弱性: {cve_id}",
                            recommendation="最新バージョンにアップデートしてください",
                            vulnerability_id=cve_id,
                            affected_versions=version_spec,
                            fixed_version=None,
                            license_issue=None,
                            dependency_path=[]
                        )
                        self.security_issues.append(issue)
    
    def _assess_vulnerability_severity(self, vuln: Dict) -> DependencyRisk:
        """脆弱性重要度評価"""
        # CVSSスコアがあれば使用
        cvss_score = vuln.get('cvss_score')
        if cvss_score:
            if cvss_score >= 9.0:
                return DependencyRisk.CRITICAL
            elif cvss_score >= 7.0:
                return DependencyRisk.HIGH
            elif cvss_score >= 4.0:
                return DependencyRisk.MEDIUM
            else:
                return DependencyRisk.LOW
        
        # CVSSスコアがない場合はAdvisoryの内容で判断
        advisory = vuln.get('advisory', '').lower()
        if any(word in advisory for word in ['remote code execution', 'rce', 'critical']):
            return DependencyRisk.CRITICAL
        elif any(word in advisory for word in ['sql injection', 'xss', 'csrf']):
            return DependencyRisk.HIGH
        else:
            return DependencyRisk.MEDIUM
    
    def _check_license_compatibility(self):
        """ライセンス互換性チェック"""
        logger.info("📜 ライセンス互換性チェック中...")
        
        # プロジェクトライセンス取得
        project_license = self._get_project_license()
        
        if not project_license:
            logger.warning("プロジェクトライセンスが設定されていません")
            return
        
        compatible_licenses = self.license_compatibility.get(project_license, [])
        
        for pkg_name, pkg_info in self.dependency_tree.items():
            if pkg_info.license:
                pkg_license = self._normalize_license(pkg_info.license)
                
                # 問題あるライセンスチェック
                if pkg_license in self.problematic_licenses:
                    issue = DependencyIssue(
                        package_name=pkg_name,
                        current_version=pkg_info.version,
                        issue_type='problematic_license',
                        severity=DependencyRisk.HIGH,
                        description=f"問題のあるライセンス: {pkg_license}",
                        recommendation=f"ライセンス {pkg_license} のパッケージの使用を避けるか、代替パッケージを検討してください",
                        vulnerability_id=None,
                        affected_versions=None,
                        fixed_version=None,
                        license_issue=pkg_license,
                        dependency_path=[]
                    )
                    self.license_issues.append(issue)
                
                # 互換性チェック
                elif pkg_license not in compatible_licenses and pkg_license != project_license:
                    issue = DependencyIssue(
                        package_name=pkg_name,
                        current_version=pkg_info.version,
                        issue_type='license_incompatibility',
                        severity=DependencyRisk.MEDIUM,
                        description=f"ライセンス非互換: {pkg_license} vs プロジェクト {project_license}",
                        recommendation=f"ライセンス互換性を確認し、必要に応じて法務部門に相談してください",
                        vulnerability_id=None,
                        affected_versions=None,
                        fixed_version=None,
                        license_issue=pkg_license,
                        dependency_path=[]
                    )
                    self.license_issues.append(issue)
    
    def _get_project_license(self) -> Optional[str]:
        """プロジェクトライセンス取得"""
        try:
            if self.pyproject_toml.exists():
                with open(self.pyproject_toml, 'rb') as f:
                    data = tomllib.load(f)
                    license_info = data.get('project', {}).get('license')
                    if license_info:
                        if isinstance(license_info, dict):
                            return license_info.get('text')
                        else:
                            return str(license_info)
            
            # LICENSE ファイルから推測
            license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md']
            for license_file in license_files:
                license_path = self.project_root / license_file
                if license_path.exists():
                    with open(license_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        return self._detect_license_from_content(content)
            
        except Exception as e:
            logger.debug(f"プロジェクトライセンス取得エラー: {e}")
        
        return None
    
    def _normalize_license(self, license_str: str) -> str:
        """ライセンス文字列正規化"""
        license_mappings = {
            'mit': 'MIT',
            'apache': 'Apache-2.0',
            'apache software license': 'Apache-2.0',
            'bsd': 'BSD-3-Clause',
            'gpl': 'GPL-3.0',
            'lgpl': 'LGPL-3.0'
        }
        
        normalized = license_str.lower().strip()
        for pattern, standard in license_mappings.items():
            if pattern in normalized:
                return standard
        
        return license_str
    
    def _detect_license_from_content(self, content: str) -> Optional[str]:
        """ライセンス内容からライセンス種別検出"""
        content_lower = content.lower()
        
        if 'mit license' in content_lower:
            return 'MIT'
        elif 'apache license' in content_lower:
            return 'Apache-2.0'
        elif 'bsd license' in content_lower:
            return 'BSD-3-Clause'
        elif 'gnu general public license' in content_lower:
            return 'GPL-3.0'
        
        return None
    
    def _check_version_conflicts(self):
        """バージョン競合チェック"""
        logger.info("⚖️ バージョン競合チェック中...")
        
        # 重複パッケージ名チェック（大文字小文字、ハイフン/アンダースコア）
        normalized_names = {}
        
        for pkg_name in self.dependency_tree.keys():
            normalized = pkg_name.lower().replace('-', '_')
            if normalized in normalized_names:
                original_name = normalized_names[normalized]
                if original_name != pkg_name:
                    issue = DependencyIssue(
                        package_name=pkg_name,
                        current_version=self.dependency_tree[pkg_name].version,
                        issue_type='package_name_conflict',
                        severity=DependencyRisk.MEDIUM,
                        description=f"パッケージ名競合: {pkg_name} vs {original_name}",
                        recommendation="重複するパッケージのうち1つを削除してください",
                        vulnerability_id=None,
                        affected_versions=None,
                        fixed_version=None,
                        license_issue=None,
                        dependency_path=[]
                    )
                    self.version_conflicts.append(issue)
            else:
                normalized_names[normalized] = pkg_name
    
    def _check_unused_dependencies(self):
        """未使用依存関係チェック"""
        logger.info("🗑️ 未使用依存関係チェック中...")
        
        try:
            # 簡易版: import文を検索して使用されているパッケージを特定
            used_packages = self._find_imported_packages()
            
            direct_deps = [name for name, info in self.dependency_tree.items() 
                          if info.is_direct_dependency]
            
            for dep_name in direct_deps:
                # パッケージ名の正規化バリエーション
                variations = [
                    dep_name,
                    dep_name.replace('-', '_'),
                    dep_name.replace('_', '-'),
                    dep_name.lower(),
                    dep_name.lower().replace('-', '_')
                ]
                
                if not any(var in used_packages for var in variations):
                    self.unused_deps.append(dep_name)
                    
        except Exception as e:
            logger.warning(f"未使用依存関係チェックエラー: {e}")
    
    def _find_imported_packages(self) -> Set[str]:
        """インポートされているパッケージ検索"""
        imported = set()
        
        for py_file in self.project_root.glob("**/*.py"):
            if self._should_scan_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # import文を正規表現で検索
                    import re
                    
                    # from package import ...
                    from_imports = re.findall(r'from\s+([a-zA-Z0-9_.-]+)', content)
                    imported.update(pkg.split('.')[0] for pkg in from_imports)
                    
                    # import package
                    import_stmts = re.findall(r'import\s+([a-zA-Z0-9_.-]+)', content)
                    imported.update(pkg.split('.')[0] for pkg in import_stmts)
                    
                except Exception as e:
                    logger.debug(f"ファイル読み込みエラー {py_file}: {e}")
        
        return imported
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """ファイルをスキャンすべきかチェック"""
        file_str = str(file_path)
        
        exclude_patterns = [
            "tests/", "venv/", ".venv/", "__pycache__/",
            ".git/", "build/", "dist/", ".tox/", "node_modules/"
        ]
        
        for pattern in exclude_patterns:
            if pattern in file_str:
                return False
        
        return True
    
    def _check_outdated_dependencies(self):
        """古い依存関係チェック"""
        logger.info("⏰ 古い依存関係チェック中...")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                outdated_packages = json.loads(result.stdout)
                
                for pkg in outdated_packages:
                    pkg_name = pkg['name']
                    current_version = pkg['version']
                    latest_version = pkg['latest_version']
                    
                    if pkg_name in self.dependency_tree:
                        issue = DependencyIssue(
                            package_name=pkg_name,
                            current_version=current_version,
                            issue_type='outdated_dependency',
                            severity=self._assess_outdated_severity(current_version, latest_version),
                            description=f"古いバージョン: {current_version} → {latest_version}",
                            recommendation=f"バージョン {latest_version} にアップデートを検討してください",
                            vulnerability_id=None,
                            affected_versions=None,
                            fixed_version=latest_version,
                            license_issue=None,
                            dependency_path=[]
                        )
                        self.outdated_deps.append(issue)
                        
        except Exception as e:
            logger.warning(f"古い依存関係チェックエラー: {e}")
    
    def _assess_outdated_severity(self, current: str, latest: str) -> DependencyRisk:
        """古い依存関係の重要度評価"""
        try:
            current_ver = packaging.version.parse(current)
            latest_ver = packaging.version.parse(latest)
            
            # メジャーバージョンが異なる場合
            if current_ver.major < latest_ver.major:
                return DependencyRisk.HIGH
            
            # マイナーバージョンが大きく異なる場合
            if current_ver.minor < latest_ver.minor - 5:
                return DependencyRisk.MEDIUM
            
            # パッチバージョンが異なる場合
            if current_ver.micro < latest_ver.micro:
                return DependencyRisk.LOW
            
        except Exception:
            pass
        
        return DependencyRisk.LOW
    
    def _version_matches_spec(self, version: str, spec: str) -> bool:
        """バージョンが仕様にマッチするかチェック"""
        try:
            ver = packaging.version.parse(version)
            
            if spec.startswith('<'):
                spec_ver = packaging.version.parse(spec[1:])
                return ver < spec_ver
            elif spec.startswith('<='):
                spec_ver = packaging.version.parse(spec[2:])
                return ver <= spec_ver
            elif spec.startswith('>='):
                spec_ver = packaging.version.parse(spec[2:])
                return ver >= spec_ver
            elif spec.startswith('>'):
                spec_ver = packaging.version.parse(spec[1:])
                return ver > spec_ver
            elif spec.startswith('=='):
                spec_ver = packaging.version.parse(spec[2:])
                return ver == spec_ver
            
        except Exception:
            pass
        
        return False
    
    def _analyze_results(self, start_time: datetime) -> DependencyTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 統計計算
        total_deps = len(self.dependency_tree)
        direct_deps = sum(1 for info in self.dependency_tree.values() if info.is_direct_dependency)
        transitive_deps = total_deps - direct_deps
        
        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_dependency_risk()
        
        # 推奨事項生成
        recommendations = self._generate_dependency_recommendations()
        
        return DependencyTestResult(
            total_dependencies=total_deps,
            direct_dependencies=direct_deps,
            transitive_dependencies=transitive_deps,
            security_issues=self.security_issues,
            license_issues=self.license_issues,
            version_conflicts=self.version_conflicts,
            unused_dependencies=self.unused_deps,
            outdated_dependencies=self.outdated_deps,
            dependency_tree=self.dependency_tree,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations
        )
    
    def _calculate_overall_dependency_risk(self) -> DependencyRisk:
        """全体依存関係リスクレベル計算"""
        all_issues = self.security_issues + self.license_issues + self.version_conflicts + self.outdated_deps
        
        if not all_issues:
            return DependencyRisk.SAFE
        
        risk_counts = {}
        for issue in all_issues:
            risk_counts[issue.severity] = risk_counts.get(issue.severity, 0) + 1
        
        if risk_counts.get(DependencyRisk.CRITICAL, 0) > 0:
            return DependencyRisk.CRITICAL
        elif risk_counts.get(DependencyRisk.HIGH, 0) > 0:
            return DependencyRisk.HIGH
        elif risk_counts.get(DependencyRisk.MEDIUM, 0) > 0:
            return DependencyRisk.MEDIUM
        else:
            return DependencyRisk.LOW
    
    def _generate_dependency_recommendations(self) -> List[str]:
        """依存関係推奨事項生成"""
        recommendations = [
            "定期的な依存関係アップデートの実施",
            "セキュリティ脆弱性チェックの自動化",
            "ライセンス互換性確認の徹底",
            "未使用依存関係の定期的な削除",
            "依存関係のピン留めとロックファイルの管理",
            "SBOMの生成と管理",
            "依存関係の最小化（必要最小限のパッケージのみ使用）",
        ]
        
        if self.security_issues:
            recommendations.extend([
                "発見されたセキュリティ脆弱性を即座に修正する",
                "セキュリティアドバイザリの購読を検討する"
            ])
        
        if self.license_issues:
            recommendations.extend([
                "ライセンス問題のあるパッケージの代替手段を検討する",
                "法務部門とのライセンス確認プロセスを確立する"
            ])
        
        if self.unused_deps:
            recommendations.append(f"{len(self.unused_deps)}個の未使用依存関係を削除する")
        
        return recommendations
    
    def _generate_dependency_report(self, result: DependencyTestResult):
        """依存関係レポート生成"""
        report_file = self.project_root / "dependency_integrity_report.json"
        
        report_data = {
            "summary": {
                "total_dependencies": result.total_dependencies,
                "direct_dependencies": result.direct_dependencies,
                "transitive_dependencies": result.transitive_dependencies,
                "security_issues": len(result.security_issues),
                "license_issues": len(result.license_issues),
                "version_conflicts": len(result.version_conflicts),
                "unused_dependencies": len(result.unused_dependencies),
                "outdated_dependencies": len(result.outdated_dependencies),
                "overall_risk": result.overall_risk.value,
                "test_duration": result.test_duration,
                "timestamp": result.timestamp.isoformat()
            },
            "security_issues": [
                {
                    "package": issue.package_name,
                    "version": issue.current_version,
                    "type": issue.issue_type,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "vulnerability_id": issue.vulnerability_id,
                    "affected_versions": issue.affected_versions,
                    "fixed_version": issue.fixed_version
                }
                for issue in result.security_issues
            ],
            "license_issues": [
                {
                    "package": issue.package_name,
                    "version": issue.current_version,
                    "type": issue.issue_type,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "license": issue.license_issue
                }
                for issue in result.license_issues
            ],
            "version_conflicts": [
                {
                    "package": issue.package_name,
                    "version": issue.current_version,
                    "type": issue.issue_type,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "recommendation": issue.recommendation
                }
                for issue in result.version_conflicts
            ],
            "unused_dependencies": result.unused_dependencies,
            "outdated_dependencies": [
                {
                    "package": issue.package_name,
                    "current_version": issue.current_version,
                    "latest_version": issue.fixed_version,
                    "severity": issue.severity.value,
                    "recommendation": issue.recommendation
                }
                for issue in result.outdated_dependencies
            ],
            "dependency_tree": {
                name: {
                    "version": info.version,
                    "license": info.license,
                    "description": info.description,
                    "is_direct": info.is_direct_dependency,
                    "is_dev": info.is_dev_dependency
                }
                for name, info in result.dependency_tree.items()
            },
            "recommendations": result.recommendations,
            "risk_distribution": self._get_dependency_risk_distribution(
                result.security_issues + result.license_issues + 
                result.version_conflicts + result.outdated_dependencies
            )
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 依存関係整合性レポート生成: {report_file}")
    
    def _get_dependency_risk_distribution(self, issues: List[DependencyIssue]) -> Dict[str, int]:
        """依存関係リスク分布取得"""
        distribution = {}
        for issue in issues:
            risk = issue.severity.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent
    
    logger.info("🚀 依存関係整合性チェック開始")
    
    try:
        with DependencyIntegrityChecker(project_root) as checker:
            result = checker.run()
            
            # 結果サマリー表示
            logger.info("📊 依存関係整合性チェック結果サマリー:")
            logger.info(f"  総依存関係数: {result.total_dependencies}")
            logger.info(f"  直接依存関係: {result.direct_dependencies}")
            logger.info(f"  推移的依存関係: {result.transitive_dependencies}")
            logger.info(f"  セキュリティ問題: {len(result.security_issues)}件")
            logger.info(f"  ライセンス問題: {len(result.license_issues)}件")
            logger.info(f"  バージョン競合: {len(result.version_conflicts)}件")
            logger.info(f"  未使用依存関係: {len(result.unused_dependencies)}件")
            logger.info(f"  古い依存関係: {len(result.outdated_dependencies)}件")
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")
            
            # 重要な問題を表示
            critical_issues = [i for i in result.security_issues + result.license_issues 
                              if i.severity in [DependencyRisk.CRITICAL, DependencyRisk.HIGH]]
            
            if critical_issues:
                logger.warning(f"🚨 高リスク依存関係問題 {len(critical_issues)}件:")
                for issue in critical_issues[:5]:  # 上位5件表示
                    logger.warning(f"  - {issue.package_name} ({issue.severity.value}): {issue.description}")
            
            if result.unused_dependencies:
                logger.info(f"🗑️ 未使用依存関係: {', '.join(result.unused_dependencies[:5])}")
                if len(result.unused_dependencies) > 5:
                    logger.info(f"  ... 他{len(result.unused_dependencies) - 5}件")
            
            return 0 if result.overall_risk in [DependencyRisk.SAFE, DependencyRisk.LOW] else 1
            
    except Exception as e:
        logger.error(f"💥 依存関係整合性チェック実行エラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())