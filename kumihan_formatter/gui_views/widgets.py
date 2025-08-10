"""UI widgets for Kumihan-Formatter GUI

Single Responsibility Principle適用: UIウィジェット管理の分離
Issue #476対応 - gui_views.py分割（2/4）
"""

from tkinter import W, Widget, ttk
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..gui_models import AppState


class HeaderFrame:
    """ヘッダーフレームクラス

    タイトルとサブタイトルを表示するヘッダー部分
    """

    def __init__(self, parent: Widget) -> None:
        """ヘッダーフレームの初期化"""
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._setup_header()

    def _setup_header(self) -> None:
        """ヘッダーの構築"""
        # タイトル
        self.title_label = ttk.Label(
            self.frame, text="Kumihan-Formatter", font=("Arial", 16, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # サブタイトル
        self.subtitle_label = ttk.Label(
            self.frame,
            text="美しい組版を、誰でも簡単に。テキストファイルをワンクリックでHTMLに変換",
            font=("Arial", 10),
        )
        self.subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)


class FileSelectionFrame:
    """ファイル選択フレームクラス

    入力ファイルと出力ディレクトリの選択UI
    """

    def __init__(self, parent: Widget, app_state: "AppState") -> None:
        """ファイル選択フレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.LabelFrame(parent, text="ファイル選択", padding="10")
        self._setup_file_selection()

    def _setup_file_selection(self) -> None:
        """ファイル選択UIの構築"""
        self.frame.columnconfigure(1, weight=1)

        # 入力ファイル選択
        ttk.Label(self.frame, text="入力ファイル:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        self.input_entry = ttk.Entry(
            self.frame, textvariable=self.app_state.config.input_file_var, width=50
        )
        self.input_entry.grid(row=0, column=1, sticky="WE", padx=(0, 10))

        self.input_browse_btn = ttk.Button(self.frame, text="参照")
        self.input_browse_btn.grid(row=0, column=2)

        # 出力ディレクトリ選択
        ttk.Label(self.frame, text="出力フォルダ:").grid(
            row=1, column=0, sticky=W, padx=(0, 10), pady=(10, 0)
        )
        self.output_entry = ttk.Entry(
            self.frame, textvariable=self.app_state.config.output_dir_var, width=50
        )
        self.output_entry.grid(row=1, column=1, sticky="WE", padx=(0, 10), pady=(10, 0))

        self.output_browse_btn = ttk.Button(self.frame, text="参照")
        self.output_browse_btn.grid(row=1, column=2, pady=(10, 0))

    def set_input_browse_command(self, command: Callable[[], None]) -> None:
        """入力ファイル参照ボタンのコマンドを設定"""
        self.input_browse_btn.configure(command=command)

    def set_output_browse_command(self, command: Callable[[], None]) -> None:
        """出力ディレクトリ参照ボタンのコマンドを設定"""
        self.output_browse_btn.configure(command=command)

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)


class OptionsFrame:
    """オプション設定フレームクラス

    変換オプション（テンプレート、ソース表示等）の設定UI
    """

    def __init__(self, parent: Widget, app_state: "AppState") -> None:
        """オプションフレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.LabelFrame(parent, text="変換オプション", padding="10")
        self._setup_options()

    def _setup_options(self) -> None:
        """オプション設定UIの構築"""
        self.frame.columnconfigure(1, weight=1)

        # テンプレート選択
        ttk.Label(self.frame, text="テンプレート:").grid(row=0, column=0, sticky=W, padx=(0, 10))
        self.template_combo = ttk.Combobox(
            self.frame,
            textvariable=self.app_state.config.template_var,
            values=self.app_state.config.available_templates,
            state="readonly",
        )
        self.template_combo.grid(row=0, column=1, sticky="WE", padx=(0, 10))

        # ソース表示オプション
        self.source_check = ttk.Checkbutton(
            self.frame,
            text="ソース表示機能を含める",
            variable=self.app_state.config.include_source_var,
        )
        self.source_check.grid(row=1, column=0, columnspan=2, sticky=W, pady=(10, 0))

        # プレビュー無効化オプション
        self.preview_check = ttk.Checkbutton(
            self.frame,
            text="変換後のプレビューをスキップ",
            variable=self.app_state.config.no_preview_var,
        )
        self.preview_check.grid(row=2, column=0, columnspan=2, sticky=W, pady=(5, 0))

    def set_source_toggle_command(self, command: Callable[[], None]) -> None:
        """ソース表示チェックボックスのコマンドを設定"""
        self.source_check.configure(command=command)

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)
