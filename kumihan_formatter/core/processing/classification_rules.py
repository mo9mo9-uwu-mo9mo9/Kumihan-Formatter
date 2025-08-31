from typing import Dict

"""Document Classification Rules
文書分類ルールの定義 - Issue #118対応
"""

from ..types.document_types import DocumentType


def build_classification_rules() -> Dict[DocumentType, dict[str, list[str]]]:
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


def get_conversion_strategies() -> Dict[DocumentType, tuple[str, str]]:
    """文書タイプに対する変換戦略のマッピングを取得"""
    return {
        DocumentType.USER_ESSENTIAL: ("markdown_to_txt", "docs/essential"),
        DocumentType.USER_GUIDE: ("markdown_to_html", "docs/user"),
        DocumentType.DEVELOPER: ("copy_as_is", "docs/developer"),
        DocumentType.TECHNICAL: ("copy_as_is", "docs/technical"),
        DocumentType.EXAMPLE: ("copy_as_is", "examples"),
        DocumentType.EXCLUDE: ("exclude", ""),
    }
