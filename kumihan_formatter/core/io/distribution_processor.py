"""
配布管理 - ファイル処理

ファイルコピー・分類処理・統計レポートの責任を担当
Issue #319対応 - distribution_manager.py から分離
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ...doc_classifier import DocumentType


class DistributionProcessor:
    """配布用ファイル処理クラス

    責任: ファイルコピー・分類処理・統計生成
    """

    def __init__(self, ui: Any | None = None) -> None:
        """
        Args:
            ui: UIインスタンス（進捗表示用）
        """
        self.ui = ui

    def copy_program_files(
        self,
        classified_files: dict[DocumentType, list[Path]],
        source_dir: Path,
        output_dir: Path,
    ) -> dict[str, int]:
        """メインプログラムファイルの処理

        Args:
            classified_files: 分類されたファイル辞書
            source_dir: ソースディレクトリ
            output_dir: 出力ディレクトリ

        Returns:
            dict[str, int]: 処理統計
        """
        stats = {"copied_as_is": 0}

        # サンプルファイル
        for file_path in classified_files[DocumentType.EXAMPLE]:
            if self._copy_file_as_is(file_path, source_dir, output_dir):
                stats["copied_as_is"] += 1

        # メインプログラム（kumihan_formatter/ 以下）
        stats["copied_as_is"] += self._copy_main_program(source_dir, output_dir)

        # セットアップファイル
        stats["copied_as_is"] += self._copy_setup_files(source_dir, output_dir)

        return stats

    def _copy_main_program(self, source_dir: Path, output_dir: Path) -> int:
        """メインプログラムをコピー"""
        kumihan_formatter_dir = source_dir / "kumihan_formatter"
        copied_count = 0

        if kumihan_formatter_dir.exists():
            target_dir = output_dir / "kumihan_formatter"

            # 既存ディレクトリを削除
            if target_dir.exists():
                shutil.rmtree(target_dir)

            # プログラムディレクトリをコピー
            shutil.copytree(kumihan_formatter_dir, target_dir)

            # Python ファイル数をカウント
            py_files = list(target_dir.rglob("*.py"))
            copied_count = len(py_files)

            if self.ui:
                self.ui.info(
                    f"メインプログラムをコピー: {copied_count}個のPythonファイル"
                )

        return copied_count

    def _copy_setup_files(self, source_dir: Path, output_dir: Path) -> int:
        """セットアップファイルをコピー"""
        setup_files = ["setup_windows.bat", "setup_macos.command", "pyproject.toml"]
        copied_count = 0

        for filename in setup_files:
            setup_file = source_dir / filename
            if setup_file.exists():
                try:
                    shutil.copy2(setup_file, output_dir / filename)
                    copied_count += 1

                    if self.ui:
                        self.ui.dim(f"セットアップファイルをコピー: {filename}")

                except Exception as e:
                    if self.ui:
                        self.ui.warning(
                            f"セットアップファイルコピー失敗: {filename} - {e}"
                        )

        return copied_count

    def _copy_file_as_is(
        self, file_path: Path, source_dir: Path, output_dir: Path
    ) -> bool:
        """ファイルをそのままコピー

        Args:
            file_path: コピー元ファイル
            source_dir: ソースディレクトリ
            output_dir: 出力ディレクトリ

        Returns:
            bool: コピー成功かどうか
        """
        try:
            relative_path = file_path.relative_to(source_dir)
            target_file = output_dir / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_file)
            return True

        except Exception as e:
            if self.ui:
                self.ui.warning(f"ファイルコピー失敗: {file_path.name} - {e}")
            return False

    def create_distribution_info(self, output_dir: Path, stats: dict[str, int]) -> None:
        """配布情報ファイルを作成

        Args:
            output_dir: 出力ディレクトリ
            stats: 処理統計
        """
        info_content = self._generate_distribution_info(stats)
        info_file = output_dir / "distribution_info.txt"

        try:
            with open(info_file, "w", encoding="utf-8") as f:
                f.write(info_content)

            if self.ui:
                self.ui.info("配布情報ファイルを作成: distribution_info.txt")

        except Exception as e:
            if self.ui:
                self.ui.warning(f"配布情報ファイル作成失敗: {e}")

    def _generate_distribution_info(self, stats: dict[str, int]) -> str:
        """配布情報テキストを生成"""
        generation_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        return f"""Kumihan-Formatter 配布パッケージ情報

作成日時: {generation_time}

ファイル処理統計:
- HTML変換: {stats.get('converted_to_html', 0)}ファイル
- TXT変換: {stats.get('converted_to_txt', 0)}ファイル
- コピーファイル: {stats.get('copied_as_is', 0)}ファイル
- 総ファイル数: {stats.get('total_files', 0)}ファイル

このパッケージには、Kumihan-Formatterの実行に必要なすべてのファイルが含まれています。
詳細な使用方法については、付属のドキュメントをご参照ください。
"""

    def report_statistics(self, stats: dict[str, int]) -> None:
        """統計情報を表示

        Args:
            stats: 処理統計
        """
        if not self.ui:
            return

        self.ui.info("=== 配布構造作成完了 ===")
        self.ui.success(f"総ファイル数: {stats.get('total_files', 0)}")

        if stats.get("converted_to_html", 0) > 0:
            self.ui.info(f"HTML変換: {stats['converted_to_html']}ファイル")

        if stats.get("converted_to_txt", 0) > 0:
            self.ui.info(f"TXT変換: {stats['converted_to_txt']}ファイル")

        if stats.get("copied_as_is", 0) > 0:
            self.ui.info(f"ファイルコピー: {stats['copied_as_is']}ファイル")

        if stats.get("excluded", 0) > 0:
            self.ui.dim(f"除外: {stats['excluded']}ファイル")
