"""Document Classification System
文書分類システム - Issue #118対応
エンドユーザー向けと開発者向け文書を適切に分類・処理する
"""

import re
from enum import Enum
from pathlib import Path
from typing import Dict


class DocumentType(Enum):
    """文書タイプの分類"""

    USER_ESSENTIAL = "user_essential"  # 最重要ユーザー文書（.txt化）
    USER_GUIDE = "user_guide"  # ユーザーガイド（HTML化）
    DEVELOPER = "developer"  # 開発者向け文書（Markdownのまま）
    TECHNICAL = "technical"  # 技術文書（開発者ディレクトリ）
    EXCLUDE = "exclude"  # 配布から除外
    EXAMPLE = "example"  # サンプルファイル


class DocumentClassifier:
    """文書分類器
    ファイルパスとメタデータに基づいて文書を適切に分類する
    """

    def __init__(self) -> None:
        """分類器を初期化"""
        self.classification_rules = self._build_classification_rules()

    def _build_classification_rules(self) -> Dict[DocumentType, dict[str, list[str]]]:
        """分類ルールを構築"""
        return {
            DocumentType.USER_ESSENTIAL: {
                "filenames": [
                    "README.md",
                    "readme.md",
                    "LISENCE",
                    "LICENSE",
                    "LICENSE.txt",
                    "はじめに.md",
                    "はじめに.txt",
                    "クイックスタート.md",
                    "クイックスタート.txt",
                    "quickstart.md",
                    "quickstart.txt",
                ],
                "patterns": [
                    r"^readme",
                    r"^license",
                    r"quickstart",
                    r"クイック.*スタート",
                    r"はじめに",
                    r"getting.*started",
                ],
            },
            DocumentType.USER_GUIDE: {
                "filenames": [
                    "INSTALL.md",
                    "install.md",
                    "USAGE.md",
                    "usage.md",
                    "tutorial.md",
                    "TUTORIAL.md",
                    "TROUBLESHOOTING.md",
                    "troubleshooting.md",
                    "FAQ.md",
                    "faq.md",
                    "インストール.md",
                    "チュートリアル.md",
                    "トラブルシューティング.md",
                    "よくある質問.md",
                ],
                "paths": ["docs/user", "docs/ユーザー", "user_docs", "ユーザーガイド"],
                "patterns": [
                    r"install",
                    r"usage",
                    r"tutorial",
                    r"troubleshoot",
                    r"faq",
                    r"インストール",
                    r"使い方",
                    r"チュートリアル",
                    r"トラブル.*シューティング",
                    r"よくある質問",
                ],
            },
            DocumentType.DEVELOPER: {
                "filenames": [
                    "CONTRIBUTING.md",
                    "contributing.md",
                    "DEVELOPERS.md",
                    "developers.md",
                    "API.md",
                    "api.md",
                    "ARCHITECTURE.md",
                    "architecture.md",
                ],
                "paths": [
                    "dev",
                    "developer",
                    "development",
                    "docs/dev",
                    "docs/developer",
                    "docs/development",
                ],
                "patterns": [
                    r"contribut",
                    r"developer",
                    r"development",
                    r"api",
                    r"architecture",
                ],
            },
            DocumentType.TECHNICAL: {
                "filenames": [
                    "CLAUDE.md",
                    "SPEC.md",
                    "spec.md",
                    "STYLE_GUIDE.md",
                    "style_guide.md",
                    "DESIGN.md",
                    "design.md",
                    "REFACTORING_SUMMARY.md",
                    "BRANCH_CLEANUP.md",
                    "SYNTAX_CHECKER_README.md",
                ],
                "patterns": [
                    r"claude\.md$",
                    r"spec\.md$",
                    r"style.*guide",
                    r"design",
                    r"refactor",
                    r"branch.*cleanup",
                    r"syntax.*checker",
                ],
            },
            DocumentType.EXAMPLE: {
                "paths": ["examples", "samples", "サンプル"],
                "patterns": [r"example", r"sample", r"サンプル", r"テンプレート"],
            },
            DocumentType.EXCLUDE: {
                "filenames": [
                    "CHANGELOG.md",
                    "HISTORY.md",
                    "TODO.md",
                    ".gitignore",
                    ".gitattributes",
                ],
                "paths": [
                    ".git",
                    ".github",
                    ".vscode",
                    ".idea",
                    "__pycache__",
                    ".pytest_cache",
                    "node_modules",
                ],
                "patterns": [
                    r"changelog",
                    r"history",
                    r"todo",
                    r"\.git",
                    r"__pycache__",
                    r"\.pytest_cache",
                ],
            },
        }

    def classify_file(self, file_path: Path, base_path: Path) -> DocumentType:
        """ファイルを分類
        Args:
            file_path: 分類するファイルのパス
            base_path: ベースディレクトリパス
        Returns:
            DocumentType: 分類結果
        """
        relative_path = file_path.relative_to(base_path)
        filename = file_path.name.lower()
        path_str = str(relative_path).lower()
        # ファイル名による直接マッチング（最高優先度）
        for doc_type, rules in self.classification_rules.items():
            if "filenames" in rules:
                for target_filename in rules["filenames"]:
                    if filename == target_filename.lower():
                        return doc_type
        # パス prefix による分類
        for doc_type, rules in self.classification_rules.items():
            if "paths" in rules:
                for path_prefix in rules["paths"]:
                    if path_str.startswith(path_prefix.lower()):
                        return doc_type
        # パターンマッチング
        for doc_type, rules in self.classification_rules.items():
            if "patterns" in rules:
                for pattern in rules["patterns"]:
                    if re.search(pattern, path_str, re.IGNORECASE):
                        return doc_type
        # デフォルト: 拡張子による分類
        if file_path.suffix.lower() == ".md":
            # Markdownファイルはデフォルトでユーザーガイドとして扱う
            return DocumentType.USER_GUIDE
        elif file_path.suffix.lower() in [".txt", ".html"]:
            return DocumentType.USER_ESSENTIAL
        else:
            return DocumentType.EXCLUDE

    def classify_directory(self, directory: Path) -> dict[DocumentType, list[Path]]:
        """ディレクトリ内のファイルを一括分類
        Args:
            directory: 分類するディレクトリ
        Returns:
            Dict: 分類結果（タイプ別ファイルリスト）
        """
        result = {doc_type: [] for doc_type in DocumentType}  # type: ignore
        # 除外パターンをロード
        exclude_patterns = self._load_exclude_patterns(directory)
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # 除外パターンチェック
                if self._should_exclude_by_patterns(
                    file_path, directory, exclude_patterns
                ):
                    continue
                doc_type = self.classify_file(file_path, directory)
                result[doc_type].append(file_path)
        return result

    def _load_exclude_patterns(self, directory: Path) -> list[str]:
        """除外パターンを.distignoreから読み込み"""
        distignore_file = directory / ".distignore"
        patterns = []
        if distignore_file.exists():
            try:
                with open(distignore_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception:
                pass  # エラーは無視
        return patterns

    def _should_exclude_by_patterns(
        self, file_path: Path, base_path: Path, patterns: list[str]
    ) -> bool:
        """除外パターンによるチェック"""
        from ..core.file_ops import FileOperations

        return FileOperations.should_exclude(file_path, patterns, base_path)

    def get_conversion_strategy(self, doc_type: DocumentType) -> tuple[str, str]:
        """文書タイプに対する変換戦略を取得
        Args:
            doc_type: 文書タイプ
        Returns:
            tuple[str, str]: (変換方法, 出力先ディレクトリ)
        """
        strategies = {
            DocumentType.USER_ESSENTIAL: ("markdown_to_txt", "docs/essential"),
            DocumentType.USER_GUIDE: ("markdown_to_html", "docs/user"),
            DocumentType.DEVELOPER: ("copy_as_is", "docs/developer"),
            DocumentType.TECHNICAL: ("copy_as_is", "docs/technical"),
            DocumentType.EXAMPLE: ("copy_as_is", "examples"),
            DocumentType.EXCLUDE: ("exclude", ""),
        }
        return strategies.get(doc_type, ("exclude", ""))

    def generate_document_summary(
        self, classified_files: dict[DocumentType, list[Path]]
    ) -> str:
        """分類結果のサマリーを生成"""
        summary_lines = ["📚 文書分類結果", "=" * 40, ""]
        type_names = {
            DocumentType.USER_ESSENTIAL: "🎯 重要文書（.txt変換）",
            DocumentType.USER_GUIDE: "📖 ユーザーガイド（HTML変換）",
            DocumentType.DEVELOPER: "🔧 開発者文書",
            DocumentType.TECHNICAL: "⚙️ 技術文書",
            DocumentType.EXAMPLE: "📝 サンプル・例",
            DocumentType.EXCLUDE: "🚫 除外対象",
        }
        for doc_type, files in classified_files.items():
            if files:
                summary_lines.append(
                    f"{type_names.get(doc_type, str(doc_type))} ({len(files)}件)"
                )
                for file_path in sorted(files)[:5]:  # 最初の5件のみ表示
                    summary_lines.append(f"  - {file_path}")
                if len(files) > 5:
                    summary_lines.append(f"  ... 他{len(files) - 5}件")
                summary_lines.append("")
        return "\n".join(summary_lines)


def classify_document(file_path: Path, base_path: Path) -> DocumentType:
    """ファイルを分類（外部API）
    Args:
        file_path: 分類するファイル
        base_path: ベースディレクトリ
    Returns:
        DocumentType: 分類結果
    """
    classifier = DocumentClassifier()
    return classifier.classify_file(file_path, base_path)


def classify_project_documents(project_dir: Path) -> dict[DocumentType, list[Path]]:
    """プロジェクト文書を一括分類（外部API）
    Args:
        project_dir: プロジェクトディレクトリ
    Returns:
        Dict: 分類結果
    """
    classifier = DocumentClassifier()
    return classifier.classify_directory(project_dir)
