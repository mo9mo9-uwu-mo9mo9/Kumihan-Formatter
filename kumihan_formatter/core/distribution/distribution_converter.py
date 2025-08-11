"""
配布管理 - 文書変換

Markdown→HTML/TXT変換の責任を担当
Issue #319対応 - distribution_manager.py から分離
"""

import re
from pathlib import Path
from typing import Any

from ..markdown_converter import convert_markdown_file


class DistributionConverter:
    """配布用文書変換クラス

    責任: Markdown→HTML/TXT変換・ファイル名変換
    """

    # ユーザーフレンドリーなファイル名マッピング
    FILENAME_MAPPINGS = {
        "readme.md": "はじめに",
        "install.md": "インストール方法",
        "usage.md": "使い方ガイド",
        "troubleshooting.md": "トラブルシューティング",
        "faq.md": "よくある質問",
        "quickstart.md": "クイックスタート",
        "contributing.md": "開発への参加方法",
        "changelog.md": "変更履歴",
        "license.md": "ライセンス",
    }

    def __init__(self, ui: Any | None = None) -> None:
        """
        Args:
            ui: UIインスタンス（進捗表示用）
        """
        self.ui = ui

    def convert_to_txt(self, file_path: Path, output_dir: Path) -> bool:
        """MarkdownファイルをプレーンテキストIDに変換

        Args:
            file_path: 変換元ファイル
            output_dir: 出力ディレクトリ

        Returns:
            bool: 変換成功かどうか
        """
        try:
            # Markdownを読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Markdown→テキスト変換
            text_content = self._markdown_to_plain_text(content)

            # 出力ファイル名を決定
            output_filename = self._get_user_friendly_filename(file_path, ".txt")
            output_file = output_dir / output_filename

            # テキストファイルとして保存
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text_content)

            if self.ui:
                self.ui.info(f"TXT変換: {file_path.name} → {output_filename}")

            return True

        except Exception as e:
            if self.ui:
                self.ui.warning(f"TXT変換失敗: {file_path.name} - {e}")
            return False

    def convert_to_html(self, file_path: Path, output_dir: Path) -> bool:
        """MarkdownファイルをHTMLに変換

        Args:
            file_path: 変換元ファイル
            output_dir: 出力ディレクトリ

        Returns:
            bool: 変換成功かどうか
        """
        try:
            # 出力ファイル名を決定
            output_filename = self._get_user_friendly_filename(file_path, ".html")
            output_file = output_dir / output_filename

            # タイトルを生成
            title = self._generate_title_from_filename(file_path)

            # Markdown→HTML変換
            success = convert_markdown_file(file_path, output_file, title)

            if success and self.ui:
                self.ui.info(f"HTML変換: {file_path.name} → {output_filename}")
            elif not success and self.ui:
                self.ui.warning(f"HTML変換失敗: {file_path.name}")

            return success

        except Exception as e:
            if self.ui:
                self.ui.warning(f"HTML変換失敗: {file_path.name} - {e}")
            return False

    def _markdown_to_plain_text(self, markdown_content: str) -> str:
        """Markdownをプレーンテキストに変換"""
        text = markdown_content

        # 見出しマーカーを除去
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # リンクからテキスト部分のみを抽出
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # 強調記法を除去
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # コードブロックのマーカーを除去
        text = re.sub(r"```.*?\n", "", text)
        text = re.sub(r"```", "", text)

        # インラインコードのマーカーを除去
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 水平線を除去
        text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)

        # 複数の空行を単一の空行に変換
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        return text.strip()

    def _get_user_friendly_filename(self, file_path: Path, new_extension: str) -> str:
        """ユーザーフレンドリーなファイル名を生成"""
        filename_lower = file_path.name.lower()

        # マッピングからユーザーフレンドリーな名前を取得
        for original, friendly in self.FILENAME_MAPPINGS.items():
            if filename_lower == original:
                return f"{friendly}{new_extension}"

        # マッピングにない場合は元のファイル名を使用
        return f"{file_path.stem}{new_extension}"

    def _generate_title_from_filename(self, file_path: Path) -> str:
        """ファイル名からタイトルを生成"""
        filename_lower = file_path.name.lower()

        # マッピングからタイトルを取得
        for original, friendly in self.FILENAME_MAPPINGS.items():
            if filename_lower == original:
                return friendly

        # マッピングにない場合は元のファイル名を使用
        return file_path.stem
