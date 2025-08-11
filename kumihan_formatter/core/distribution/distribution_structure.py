"""
配布管理 - 構造管理

配布用ディレクトリ構造の作成・管理の責任を担当
Issue #319対応 - distribution_manager.py から分離
"""

from pathlib import Path
from typing import Any


class DistributionStructure:
    """配布構造管理クラス

    責任: 配布用ディレクトリ構造の作成・管理
    """

    # 標準配布ディレクトリ構造
    STANDARD_DIRECTORIES = [
        "docs/essential",  # 最重要文書（.txt）
        "docs/user",  # ユーザーガイド（HTML）
        "docs/developer",  # 開発者文書（必要時）
        "docs/technical",  # 技術文書（必要時）
        "examples",  # サンプルファイル
        "kumihan_formatter",  # メインプログラム
    ]

    def __init__(self, ui: Any | None = None) -> None:
        """
        Args:
            ui: UIインスタンス（進捗表示用）
        """
        self.ui = ui

    def create_structure(
        self, output_dir: Path, custom_directories: list[str] | None = None
    ) -> None:
        """配布用ディレクトリ構造を作成

        Args:
            output_dir: 出力ディレクトリ
            custom_directories: カスタムディレクトリリスト（未指定時は標準構造）
        """
        directories = custom_directories or self.STANDARD_DIRECTORIES

        if self.ui:
            self.ui.info(f"配布構造を作成中: {len(directories)}個のディレクトリ")

        for dir_path in directories:
            target_path = output_dir / dir_path
            target_path.mkdir(parents=True, exist_ok=True)

            if self.ui:
                self.ui.dim(f"作成: {dir_path}")

    def validate_structure(self, output_dir: Path) -> bool:
        """配布構造が正しく作成されているかを検証

        Args:
            output_dir: 検証対象ディレクトリ

        Returns:
            bool: 構造が正常かどうか
        """
        for dir_path in self.STANDARD_DIRECTORIES:
            target_path = output_dir / dir_path
            if not target_path.exists() or not target_path.is_dir():
                if self.ui:
                    self.ui.error(f"必須ディレクトリが見つかりません: {dir_path}")
                return False

    def get_target_directory(self, output_dir: Path, doc_type: str) -> Path:
        """文書タイプに応じた出力ディレクトリを取得

        Args:
            output_dir: ベース出力ディレクトリ
            doc_type: 文書タイプ ('essential', 'user', 'developer', 'technical', 'example')

        Returns:
            Path: 対象ディレクトリパス
        """
        type_mapping = {
            "essential": "docs/essential",
            "user": "docs/user",
            "developer": "docs/developer",
            "technical": "docs/technical",
            "example": "examples",
            "program": "kumihan_formatter",
        }

        dir_path = type_mapping.get(doc_type, "docs/user")
        return output_dir / dir_path

    def clean_structure(self, output_dir: Path) -> None:
        """配布構造をクリーンアップ（空ディレクトリの削除等）

        Args:
            output_dir: クリーンアップ対象ディレクトリ
        """
        if self.ui:
            self.ui.info("配布構造をクリーンアップ中")

        # 空のディレクトリを削除
        for dir_path in reversed(self.STANDARD_DIRECTORIES):  # 深い階層から削除
            target_path = output_dir / dir_path
            if target_path.exists() and target_path.is_dir():
                try:
                    # ディレクトリが空の場合のみ削除
                    if not any(target_path.iterdir()):
                        target_path.rmdir()
                        if self.ui:
                            self.ui.dim(f"空ディレクトリを削除: {dir_path}")
                except OSError:
                    # 削除できない場合は無視
                    pass
