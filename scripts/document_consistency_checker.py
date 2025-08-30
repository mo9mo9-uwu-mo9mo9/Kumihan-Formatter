#!/usr/bin/env python3
"""
Kumihan-Formatter Document Consistency Checker
Issue #1240: Development Process Normalization

ドキュメント間の整合性をチェックし、不一致を検出・報告するシステム
"""

import os
import sys
import re
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

# プロジェクトルートの取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from kumihan_formatter.core.utilities.logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class InconsistencyType(Enum):
    """不整合のタイプ"""

    VERSION_MISMATCH = "version_mismatch"
    BROKEN_LINK = "broken_link"
    OUTDATED_CONTENT = "outdated_content"
    MISSING_DOCUMENTATION = "missing_documentation"
    STRUCTURAL_INCONSISTENCY = "structural_inconsistency"
    CODE_DOC_MISMATCH = "code_doc_mismatch"


class SeverityLevel(Enum):
    """重要度レベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DocumentInconsistency:
    """ドキュメント不整合項目"""

    id: str
    title: str
    description: str
    inconsistency_type: InconsistencyType
    severity: SeverityLevel
    source_file: str
    target_file: Optional[str]
    line_number: Optional[int]
    detected_date: datetime.datetime
    suggested_fix: Optional[str] = None


class DocumentConsistencyChecker:
    """ドキュメント整合性チェッカー"""

    def __init__(self):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.doc_files = self._get_documentation_files()
        self.code_files = self._get_code_files()
        self.inconsistencies: List[DocumentInconsistency] = []

    def _get_documentation_files(self) -> List[Path]:
        """ドキュメントファイルの取得"""
        doc_patterns = ["*.md", "*.rst", "*.txt", "*.yml", "*.yaml"]
        doc_files = []

        # ルートディレクトリのドキュメント
        for pattern in doc_patterns:
            doc_files.extend(self.project_root.glob(pattern))

        # .githubディレクトリ
        github_dir = self.project_root / ".github"
        if github_dir.exists():
            for pattern in doc_patterns:
                doc_files.extend(github_dir.rglob(pattern))

        # docsディレクトリがあれば
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            for pattern in doc_patterns:
                doc_files.extend(docs_dir.rglob(pattern))

        return sorted(doc_files)

    def _get_code_files(self) -> List[Path]:
        """コードファイルの取得"""
        code_files = []

        # Pythonファイル
        kumihan_dir = self.project_root / "kumihan_formatter"
        if kumihan_dir.exists():
            code_files.extend(kumihan_dir.rglob("*.py"))

        # 設定ファイル
        config_files = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Makefile",
            "requirements.txt",
            "package.json",
        ]
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                code_files.append(config_path)

        return sorted(code_files)

    def check_version_consistency(self) -> List[DocumentInconsistency]:
        """バージョン整合性チェック"""
        inconsistencies = []
        version_sources = {}

        # pyproject.tomlからバージョン取得
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding="utf-8")
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                version_sources["pyproject.toml"] = version_match.group(1)

        # __init__.pyからバージョン取得
        init_path = self.project_root / "kumihan_formatter" / "__init__.py"
        if init_path.exists():
            content = init_path.read_text(encoding="utf-8")
            version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                version_sources["__init__.py"] = version_match.group(1)

        # README.mdからバージョン取得
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            version_matches = re.findall(r"v?(\d+\.\d+\.\d+)", content)
            if version_matches:
                version_sources["README.md"] = version_matches[0]

        # バージョンの一致確認
        if len(set(version_sources.values())) > 1:
            inconsistency = DocumentInconsistency(
                id=f"version_mismatch_{datetime.datetime.now().strftime('%Y%m%d')}",
                title="バージョン情報の不一致",
                description=f"複数のファイルで異なるバージョンが記載されています: {version_sources}",
                inconsistency_type=InconsistencyType.VERSION_MISMATCH,
                severity=SeverityLevel.HIGH,
                source_file="multiple",
                target_file=None,
                line_number=None,
                detected_date=datetime.datetime.now(),
                suggested_fix="全ファイルのバージョンを統一してください",
            )
            inconsistencies.append(inconsistency)

        return inconsistencies

    def check_broken_links(self) -> List[DocumentInconsistency]:
        """リンク切れチェック"""
        inconsistencies = []

        for doc_file in self.doc_files:
            if doc_file.suffix.lower() != ".md":
                continue

            try:
                content = doc_file.read_text(encoding="utf-8")
                lines = content.split("\n")

                # Markdownリンクを検出
                link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

                for line_num, line in enumerate(lines, 1):
                    for match in re.finditer(link_pattern, line):
                        link_text, link_url = match.groups()

                        # 相対パスリンクのチェック
                        if not link_url.startswith(("http://", "https://", "#")):
                            link_path = doc_file.parent / link_url
                            if not link_path.exists():
                                inconsistency = DocumentInconsistency(
                                    id=f"broken_link_{doc_file.stem}_{line_num}",
                                    title=f"リンク切れ: {link_text}",
                                    description=f"{doc_file.name}の{line_num}行目でリンク切れを検出: {link_url}",
                                    inconsistency_type=InconsistencyType.BROKEN_LINK,
                                    severity=SeverityLevel.MEDIUM,
                                    source_file=str(
                                        doc_file.relative_to(self.project_root)
                                    ),
                                    target_file=link_url,
                                    line_number=line_num,
                                    detected_date=datetime.datetime.now(),
                                    suggested_fix=f"リンク先ファイルの作成または正しいパスへの修正: {link_url}",
                                )
                                inconsistencies.append(inconsistency)

            except Exception as e:
                logger.warning(f"ファイル読み込みエラー {doc_file}: {e}")

        return inconsistencies

    def check_code_documentation_sync(self) -> List[DocumentInconsistency]:
        """コードとドキュメントの同期チェック"""
        inconsistencies = []

        # CLAUDEで設定されたAPIとドキュメントの同期確認
        api_py_path = self.project_root / "API.md"
        if api_py_path.exists():
            api_content = api_py_path.read_text(encoding="utf-8")

            # 実装されているクラス・関数の一覧取得
            implemented_classes = set()
            implemented_functions = set()

            for py_file in self.code_files:
                if py_file.suffix == ".py":
                    try:
                        content = py_file.read_text(encoding="utf-8")

                        # クラス定義を検出
                        class_matches = re.findall(
                            r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", content, re.MULTILINE
                        )
                        implemented_classes.update(class_matches)

                        # 関数定義を検出（private除く）
                        func_matches = re.findall(
                            r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", content, re.MULTILINE
                        )
                        implemented_functions.update(
                            f for f in func_matches if not f.startswith("_")
                        )

                    except Exception as e:
                        logger.warning(f"ファイル解析エラー {py_file}: {e}")

            # API.mdに記載されているが実装されていない項目
            documented_classes = set(
                re.findall(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", api_content)
            )
            documented_functions = set(
                re.findall(r"def\s+([A-Za-z_][A-Za-z0-9_]*)", api_content)
            )

            missing_classes = documented_classes - implemented_classes
            missing_functions = documented_functions - implemented_functions

            if missing_classes or missing_functions:
                missing_items = list(missing_classes) + list(missing_functions)
                inconsistency = DocumentInconsistency(
                    id=f"code_doc_mismatch_{datetime.datetime.now().strftime('%Y%m%d')}",
                    title="APIドキュメントと実装の不一致",
                    description=f"ドキュメントに記載されているが実装されていない項目: {', '.join(missing_items[:10])}",
                    inconsistency_type=InconsistencyType.CODE_DOC_MISMATCH,
                    severity=SeverityLevel.HIGH,
                    source_file="API.md",
                    target_file="kumihan_formatter/",
                    line_number=None,
                    detected_date=datetime.datetime.now(),
                    suggested_fix="未実装項目の実装またはドキュメントからの削除",
                )
                inconsistencies.append(inconsistency)

        return inconsistencies

    def check_structural_consistency(self) -> List[DocumentInconsistency]:
        """構造的整合性チェック"""
        inconsistencies = []

        # 必須ドキュメントの存在確認
        required_docs = {
            "README.md": "プロジェクトの概要と使用方法",
            "CLAUDE.md": "Claude Code設定ファイル",
            "CONTRIBUTING.md": "コントリビューションガイド",
            "ARCHITECTURE.md": "アーキテクチャドキュメント",
        }

        for doc_name, description in required_docs.items():
            doc_path = self.project_root / doc_name
            if not doc_path.exists():
                inconsistency = DocumentInconsistency(
                    id=f"missing_doc_{doc_name.lower().replace('.', '_')}",
                    title=f"必須ドキュメント不足: {doc_name}",
                    description=f"{description}が不足しています",
                    inconsistency_type=InconsistencyType.MISSING_DOCUMENTATION,
                    severity=SeverityLevel.MEDIUM,
                    source_file="project_root",
                    target_file=doc_name,
                    line_number=None,
                    detected_date=datetime.datetime.now(),
                    suggested_fix=f"{doc_name}ファイルの作成",
                )
                inconsistencies.append(inconsistency)

        # CLAUDE.mdの構造チェック
        claude_md = self.project_root / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8")
            required_sections = [
                "プロジェクト概要",
                "開発原則",
                "開発ワークフロー",
                "品質保証システム",
            ]

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            if missing_sections:
                inconsistency = DocumentInconsistency(
                    id=f"claude_md_structure_{datetime.datetime.now().strftime('%Y%m%d')}",
                    title="CLAUDE.md構造不整合",
                    description=f"必要なセクションが不足: {', '.join(missing_sections)}",
                    inconsistency_type=InconsistencyType.STRUCTURAL_INCONSISTENCY,
                    severity=SeverityLevel.MEDIUM,
                    source_file="CLAUDE.md",
                    target_file=None,
                    line_number=None,
                    detected_date=datetime.datetime.now(),
                    suggested_fix="不足セクションの追加",
                )
                inconsistencies.append(inconsistency)

        return inconsistencies

    def check_outdated_content(self) -> List[DocumentInconsistency]:
        """古い内容のチェック"""
        inconsistencies = []

        # 最終更新日が古いファイルの検出
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=90)

        for doc_file in self.doc_files:
            try:
                mtime = datetime.datetime.fromtimestamp(doc_file.stat().st_mtime)
                if mtime < cutoff_date:
                    inconsistency = DocumentInconsistency(
                        id=f"outdated_{doc_file.stem}",
                        title=f"古いドキュメント: {doc_file.name}",
                        description=f"{doc_file.name}が{(datetime.datetime.now() - mtime).days}日間更新されていません",
                        inconsistency_type=InconsistencyType.OUTDATED_CONTENT,
                        severity=SeverityLevel.LOW,
                        source_file=str(doc_file.relative_to(self.project_root)),
                        target_file=None,
                        line_number=None,
                        detected_date=datetime.datetime.now(),
                        suggested_fix="内容の確認と必要に応じた更新",
                    )
                    inconsistencies.append(inconsistency)

            except Exception as e:
                logger.warning(f"ファイル情報取得エラー {doc_file}: {e}")

        return inconsistencies

    def run_full_check(self) -> List[DocumentInconsistency]:
        """全整合性チェックの実行"""
        logger.info("ドキュメント整合性チェックを開始します...")

        self.inconsistencies = []

        # 各種チェックの実行
        self.inconsistencies.extend(self.check_version_consistency())
        self.inconsistencies.extend(self.check_broken_links())
        self.inconsistencies.extend(self.check_code_documentation_sync())
        self.inconsistencies.extend(self.check_structural_consistency())
        self.inconsistencies.extend(self.check_outdated_content())

        logger.info(f"整合性チェック完了: {len(self.inconsistencies)}件の不整合を検出")

        # 結果をファイルに保存
        self._save_results()

        return self.inconsistencies

    def _save_results(self):
        """チェック結果の保存"""
        report_data = []
        for inconsistency in self.inconsistencies:
            report_data.append(
                {
                    "id": inconsistency.id,
                    "title": inconsistency.title,
                    "description": inconsistency.description,
                    "inconsistency_type": inconsistency.inconsistency_type.value,
                    "severity": inconsistency.severity.value,
                    "source_file": inconsistency.source_file,
                    "target_file": inconsistency.target_file,
                    "line_number": inconsistency.line_number,
                    "detected_date": inconsistency.detected_date.isoformat(),
                    "suggested_fix": inconsistency.suggested_fix,
                }
            )

        # JSONファイルに保存
        tmp_dir = self.project_root / "tmp"
        tmp_dir.mkdir(exist_ok=True)

        json_report = (
            tmp_dir
            / f"document_consistency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(json_report, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # 人間が読みやすいレポートも生成
        md_report = (
            tmp_dir
            / f"document_consistency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        self._generate_markdown_report(md_report)

        logger.info(f"チェック結果を保存: {json_report}, {md_report}")

    def _generate_markdown_report(self, output_path: Path):
        """Markdownレポートの生成"""
        report_content = f"""# ドキュメント整合性チェックレポート

生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
対象ドキュメント: {len(self.doc_files)}ファイル
検出された問題: {len(self.inconsistencies)}件

## 📊 サマリー

"""

        # 重要度別集計
        severity_counts = {}
        for severity in SeverityLevel:
            count = len([i for i in self.inconsistencies if i.severity == severity])
            severity_counts[severity.value] = count

        report_content += "### 重要度別\n"
        for severity, count in severity_counts.items():
            emoji = {"critical": "🔴", "high": "🟡", "medium": "🟢", "low": "⚪"}
            report_content += (
                f"- {emoji.get(severity, '●')} {severity.upper()}: {count}件\n"
            )

        # タイプ別集計
        type_counts = {}
        for inc_type in InconsistencyType:
            count = len(
                [i for i in self.inconsistencies if i.inconsistency_type == inc_type]
            )
            type_counts[inc_type.value] = count

        report_content += "\n### タイプ別\n"
        for inc_type, count in type_counts.items():
            if count > 0:
                report_content += f"- {inc_type.replace('_', ' ').title()}: {count}件\n"

        # 詳細リスト
        if self.inconsistencies:
            report_content += "\n## 📝 詳細\n\n"

            for i, inconsistency in enumerate(self.inconsistencies, 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟡",
                    "medium": "🟢",
                    "low": "⚪",
                }
                report_content += f"### {i}. {inconsistency.title}\n\n"
                report_content += f"- **重要度**: {severity_emoji.get(inconsistency.severity.value, '●')} {inconsistency.severity.value.upper()}\n"
                report_content += f"- **タイプ**: {inconsistency.inconsistency_type.value.replace('_', ' ').title()}\n"
                report_content += f"- **ファイル**: {inconsistency.source_file}\n"
                if inconsistency.target_file:
                    report_content += f"- **対象**: {inconsistency.target_file}\n"
                if inconsistency.line_number:
                    report_content += f"- **行番号**: {inconsistency.line_number}\n"
                report_content += f"- **説明**: {inconsistency.description}\n"
                if inconsistency.suggested_fix:
                    report_content += f"- **推奨対応**: {inconsistency.suggested_fix}\n"
                report_content += "\n---\n\n"
        else:
            report_content += "\n## ✅ 問題なし\n\nドキュメントの整合性に問題は見つかりませんでした。\n"

        report_content += (
            f"\n---\n*Generated by Document Consistency Checker - Issue #1240*"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

    def get_summary(self) -> Dict[str, Any]:
        """サマリー情報の取得"""
        severity_counts = {}
        type_counts = {}

        for severity in SeverityLevel:
            severity_counts[severity.value] = len(
                [i for i in self.inconsistencies if i.severity == severity]
            )

        for inc_type in InconsistencyType:
            type_counts[inc_type.value] = len(
                [i for i in self.inconsistencies if i.inconsistency_type == inc_type]
            )

        return {
            "total_inconsistencies": len(self.inconsistencies),
            "total_documents": len(self.doc_files),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "check_date": datetime.datetime.now().isoformat(),
        }


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python document_consistency_checker.py [check|summary]")
        return

    command = sys.argv[1]
    checker = DocumentConsistencyChecker()

    if command == "check":
        inconsistencies = checker.run_full_check()
        print(
            f"✅ ドキュメント整合性チェック完了: {len(inconsistencies)}件の不整合を検出"
        )

        if inconsistencies:
            print("\n📋 検出された問題:")
            for i, inconsistency in enumerate(
                inconsistencies[:5], 1
            ):  # 最初の5件を表示
                print(f"  {i}. {inconsistency.title} ({inconsistency.severity.value})")
            if len(inconsistencies) > 5:
                print(f"  ... 他{len(inconsistencies) - 5}件")
            print("\n詳細レポートは tmp/ ディレクトリをご確認ください。")

    elif command == "summary":
        if not checker.inconsistencies:
            checker.run_full_check()

        summary = checker.get_summary()
        print("📊 ドキュメント整合性サマリー:")
        print(f"  - 対象ドキュメント: {summary['total_documents']}ファイル")
        print(f"  - 検出問題数: {summary['total_inconsistencies']}件")
        print(f"  - Critical: {summary['severity_breakdown']['critical']}件")
        print(f"  - High: {summary['severity_breakdown']['high']}件")
        print(f"  - Medium: {summary['severity_breakdown']['medium']}件")
        print(f"  - Low: {summary['severity_breakdown']['low']}件")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
