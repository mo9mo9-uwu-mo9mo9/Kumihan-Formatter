"""Document Classification System
文書分類システム - Issue #118対応
エンドユーザー向けと開発者向け文書を適切に分類・処理する
"""

from pathlib import Path

from .classification_rules import build_classification_rules, get_conversion_strategies
from .document_types import DocumentType, get_type_display_names

__all__ = ["DocumentClassifier", "DocumentType"]


class DocumentClassifier:
    """文書分類器
    ファイルパスとメタデータに基づいて文書を適切に分類する
    """

    def __init__(self) -> None:
        """分類器を初期化"""
        self.classification_rules = build_classification_rules()

    def classify_file(self, file_path: Path, base_path: Path) -> DocumentType:
        """ファイルを分類
        Args:
            file_path: 分類するファイルのパス
            base_path: ベースディレクトリパス
        Returns:
            DocumentType: 分類結果
        """
        # パスベース分類ルール実装
        import os

        ext = os.path.splitext(file_path.name)[1].lower()
        # 拡張子による分類
        if ext in [".md", ".markdown"]:
            return (
                DocumentType.MARKDOWN
                if hasattr(DocumentType, "MARKDOWN")
                else DocumentType.GENERAL
            )
        elif ext in [".txt"]:
            return (
                DocumentType.TEXT
                if hasattr(DocumentType, "TEXT")
                else DocumentType.GENERAL
            )

        filename = file_path.name.lower()
        # ファイル名による直接マッチング（最高優先度）
        for doc_type, rules in self.classification_rules.items():
            if "filenames" in rules:
                for target_filename in rules["filenames"]:
                    if filename == target_filename.lower():
                        return doc_type

        # デフォルト分類
        return DocumentType.GENERAL

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
        # 統合モジュール経由で実行
        from .file_path_utilities import FilePathUtilities

        return FilePathUtilities.should_exclude(file_path, patterns, base_path)

    def get_conversion_strategy(self, doc_type: DocumentType) -> tuple[str, str]:
        """文書タイプに対する変換戦略を取得
        Args:
            doc_type: 文書タイプ
        Returns:
            tuple[str, str]: (変換方法, 出力先ディレクトリ)
        """
        strategies = get_conversion_strategies()
        return strategies.get(doc_type, ("exclude", ""))

    def generate_document_summary(
        self, classified_files: dict[DocumentType, list[Path]]
    ) -> str:
        """分類結果のサマリーを生成"""
        summary_lines = ["📚 文書分類結果", "=" * 40, ""]
        type_names = get_type_display_names()
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
