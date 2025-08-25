"""File Selection Component with Drag & Drop

ドラッグ&ドロップ対応ファイル選択コンポーネント
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import List, Callable, Optional

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from ...core.utilities.logger import get_logger
from ..styles.theme import KumihanTheme


class FileDropFrame(ctk.CTkFrame):
    """ドラッグ&ドロップ対応ファイル選択フレーム"""

    def __init__(
        self, parent, on_files_selected: Callable[[List[Path]], None], **kwargs
    ):
        # テーマスタイルを適用
        style_kwargs = KumihanTheme.get_frame_style()
        style_kwargs.update(kwargs)
        super().__init__(parent, **style_kwargs)

        self.logger = get_logger(__name__)
        self.on_files_selected = on_files_selected
        self.selected_files: List[Path] = []

        # UI構築
        self._build_ui()
        self._setup_drag_and_drop()

    def _build_ui(self) -> None:
        """UI構築"""
        # ドロップエリアラベル
        self.drop_label = ctk.CTkLabel(
            self,
            text="📎 ファイルをここにドラッグ&ドロップ\n\n対応形式: .txt, .md, .kumi\nまたはクリックしてファイル選択",
            **KumihanTheme.get_label_style("secondary"),
            justify="center",
        )
        self.drop_label.pack(expand=True, pady=40)

        # クリックでファイル選択
        self.drop_label.bind("<Button-1>", self._on_click_select)
        self.bind("<Button-1>", self._on_click_select)

        # ホバー効果
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.drop_label.bind("<Enter>", self._on_enter)
        self.drop_label.bind("<Leave>", self._on_leave)

    def _setup_drag_and_drop(self) -> None:
        """ドラッグ&ドロップ設定"""
        try:
            # tkinterdnd2を使用してドラッグ&ドロップ有効化
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)

            self.logger.info("ドラッグ&ドロップ機能を有効化")
        except Exception as e:
            self.logger.warning(f"ドラッグ&ドロップ設定エラー: {e}")

    def _on_click_select(self, event=None) -> None:
        """クリックによるファイル選択"""
        filetypes = [
            ("Kumihan Files", "*.kumi"),
            ("Text Files", "*.txt"),
            ("Markdown Files", "*.md"),
            ("All Files", "*.*"),
        ]

        files = filedialog.askopenfilenames(
            title="変換するファイルを選択", filetypes=filetypes
        )

        if files:
            file_paths = [Path(f) for f in files]
            self._process_files(file_paths)

    def _on_drop(self, event) -> None:
        """ドラッグ&ドロップイベント処理"""
        try:
            # ファイルパスを取得（複数ファイル対応）
            files = self.tk.splitlist(event.data)
            file_paths = []

            for file_str in files:
                file_path = Path(file_str)
                if file_path.exists() and file_path.is_file():
                    # 対応ファイル形式をチェック
                    if file_path.suffix.lower() in [".txt", ".md", ".kumi"]:
                        file_paths.append(file_path)

            if file_paths:
                self._process_files(file_paths)
            else:
                self.logger.warning("対応していないファイル形式です")

        except Exception as e:
            self.logger.error(f"ドロップ処理エラー: {e}")

    def _on_drag_enter(self, event) -> None:
        """ドラッグエンター時の視覚フィードバック"""
        self.configure(border_color=KumihanTheme.PRIMARY_COLOR, border_width=2)
        self.drop_label.configure(
            text="📎 ここにドロップしてください", text_color=KumihanTheme.PRIMARY_COLOR
        )

    def _on_drag_leave(self, event) -> None:
        """ドラッグリーブ時の視覚フィードバック復元"""
        self.configure(border_color=KumihanTheme.BORDER_COLOR, border_width=1)
        self.drop_label.configure(
            text="📎 ファイルをここにドラッグ&ドロップ\n\n対応形式: .txt, .md, .kumi\nまたはクリックしてファイル選択",
            text_color=KumihanTheme.TEXT_SECONDARY,
        )

    def _on_enter(self, event) -> None:
        """マウスホバー時の視覚フィードバック"""
        self.configure(border_color=KumihanTheme.PRIMARY_COLOR)

    def _on_leave(self, event) -> None:
        """マウスリーブ時の視覚フィードバック復元"""
        self.configure(border_color=KumihanTheme.BORDER_COLOR)

    def _process_files(self, file_paths: List[Path]) -> None:
        """ファイル処理"""
        self.selected_files = file_paths
        self.on_files_selected(file_paths)

        # 視覚フィードバック
        file_count = len(file_paths)
        if file_count == 1:
            self.drop_label.configure(
                text=f"✅ ファイル選択完了\n\n📄 {file_paths[0].name}",
                text_color=KumihanTheme.SUCCESS_COLOR,
            )
        else:
            self.drop_label.configure(
                text=f"✅ ファイル選択完了\n\n📁 {file_count}ファイル選択済み",
                text_color=KumihanTheme.SUCCESS_COLOR,
            )

        self.logger.info(f"ファイル選択: {file_count}件")

    def clear_selection(self) -> None:
        """選択をクリア"""
        self.selected_files.clear()
        self.drop_label.configure(
            text="📎 ファイルをここにドラッグ&ドロップ\n\n対応形式: .txt, .md, .kumi\nまたはクリックしてファイル選択",
            text_color=KumihanTheme.TEXT_SECONDARY,
        )
        self.configure(border_color=KumihanTheme.BORDER_COLOR)


class FileListDisplay(ctk.CTkScrollableFrame):
    """選択されたファイルリスト表示"""

    def __init__(self, parent, **kwargs):
        style_kwargs = KumihanTheme.get_frame_style()
        style_kwargs.update(kwargs)
        super().__init__(parent, **style_kwargs)

        self.files: List[Path] = []

    def update_file_list(self, files: List[Path]) -> None:
        """ファイルリスト更新"""
        self.files = files

        # 既存のウィジェットを削除
        for widget in self.winfo_children():
            widget.destroy()

        if not files:
            empty_label = ctk.CTkLabel(
                self,
                text="選択されたファイルはありません",
                **KumihanTheme.get_label_style("secondary"),
            )
            empty_label.pack(pady=20)
            return

        # ファイルリスト表示
        for i, file_path in enumerate(files):
            self._create_file_item(file_path, i)

    def _create_file_item(self, file_path: Path, index: int) -> None:
        """個別ファイルアイテム作成"""
        item_frame = ctk.CTkFrame(self, fg_color="transparent")
        item_frame.pack(fill="x", pady=4, padx=10)

        # ファイルアイコンと名前
        file_icon = "📄" if file_path.suffix.lower() == ".kumi" else "📝"
        file_label = ctk.CTkLabel(
            item_frame,
            text=f"{file_icon} {file_path.name}",
            **KumihanTheme.get_label_style("primary"),
        )
        file_label.pack(side="left", anchor="w")

        # ファイルパス
        path_label = ctk.CTkLabel(
            item_frame,
            text=str(file_path.parent),
            **KumihanTheme.get_label_style("secondary"),
        )
        path_label.pack(side="left", padx=(10, 0), anchor="w")

        # ファイルサイズ
        try:
            file_size = file_path.stat().st_size
            size_text = self._format_file_size(file_size)
            size_label = ctk.CTkLabel(
                item_frame, text=size_text, **KumihanTheme.get_label_style("secondary")
            )
            size_label.pack(side="right", anchor="e")
        except Exception:
            pass  # ファイルサイズ取得失敗時は無視

    def _format_file_size(self, size_bytes: int) -> str:
        """ファイルサイズをフォーマット"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
