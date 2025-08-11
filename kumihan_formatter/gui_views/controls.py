"""Control widgets for Kumihan-Formatter GUI

Single Responsibility Principle適用: コントロールウィジェット管理の分離
Issue #476対応 - gui_views.py分割（3/4）
"""

from tkinter import DISABLED, LEFT, VERTICAL, WORD, Text, W, Widget, ttk
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ..gui_models import AppState


class ActionButtonFrame:
    """アクションボタンフレームクラス

    変換実行、サンプル生成、ヘルプ等のアクションボタン
    """

    def __init__(self, parent: Widget, app_state: "AppState") -> None:
        """アクションボタンフレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.Frame(parent)
        self._setup_buttons()

    def _setup_buttons(self) -> None:
        """ボタンUIの構築"""
        # 変換実行ボタン
        self.convert_btn = ttk.Button(
            self.frame,
            text="変換実行",
            style="Accent.TButton",
        )
        self.convert_btn.pack(side=LEFT, padx=(0, 10))

        # サンプル生成ボタン
        self.sample_btn = ttk.Button(self.frame, text="サンプル生成")
        self.sample_btn.pack(side=LEFT, padx=(0, 10))

        # ヘルプボタン
        self.help_btn = ttk.Button(self.frame, text="ヘルプ")
        self.help_btn.pack(side=LEFT, padx=(0, 10))

        # デバッグモード時のログボタン
        if self.app_state.debug_mode:
            self.log_btn = ttk.Button(self.frame, text="ログ")
            self.log_btn.pack(side=LEFT, padx=(0, 10))

        # 終了ボタン
        self.exit_btn = ttk.Button(self.frame, text="終了")
        self.exit_btn.pack(side=LEFT)

    def set_convert_command(self, command: Callable[[], None]) -> None:
        """変換実行ボタンのコマンドを設定"""
        self.convert_btn.configure(command=command)

    def set_sample_command(self, command: Callable[[], None]) -> None:
        """サンプル生成ボタンのコマンドを設定"""
        self.sample_btn.configure(command=command)

    def set_help_command(self, command: Callable[[], None]) -> None:
        """ヘルプボタンのコマンドを設定"""
        self.help_btn.configure(command=command)

    def set_log_command(self, command: Callable[[], None]) -> None:
        """ログボタンのコマンドを設定（デバッグモード時のみ）"""
        if hasattr(self, "log_btn"):
            self.log_btn.configure(command=command)

    def set_exit_command(self, command: Callable[[], None]) -> None:
        """終了ボタンのコマンドを設定"""
        self.exit_btn.configure(command=command)

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)


class ProgressFrame:
    """進捗表示フレームクラス

    進捗バーとステータス表示
    """

    def __init__(self, parent: Widget, app_state: "AppState") -> None:
        """進捗フレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.LabelFrame(parent, text="進行状況", padding="10")
        self._setup_progress()

    def _setup_progress(self) -> None:
        """進捗表示UIの構築"""
        self.frame.columnconfigure(0, weight=1)

        # 進捗バー
        self.progress_bar = ttk.Progressbar(
            self.frame,
            variable=self.app_state.conversion_state.progress_var,
            maximum=100,
        )
        self.progress_bar.grid(row=0, column=0, sticky="WE", pady=(0, 5))

        # ステータスラベル
        self.status_label = ttk.Label(
            self.frame, textvariable=self.app_state.conversion_state.status_var
        )
        self.status_label.grid(row=1, column=0, sticky=W)

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)


class LogFrame:
    """ログ表示フレームクラス

    実行ログの表示とスクロール
    """

    def __init__(self, parent: Widget, app_state: "AppState") -> None:
        """ログフレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.LabelFrame(parent, text="ログ", padding="10")
        self._setup_log()

    def _setup_log(self) -> None:
        """ログ表示UIの構築"""
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # ログテキストエリア
        self.log_text = Text(self.frame, height=8, wrap=WORD, state=DISABLED)

        # スクロールバー
        self.log_scrollbar = ttk.Scrollbar(
            self.frame, orient=VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        # 配置
        self.log_text.grid(row=0, column=0, sticky="WENS")
        self.log_scrollbar.grid(row=0, column=1, sticky="NS")

    def add_message(self, message: str, level: str = "info") -> None:
        """ログメッセージを追加"""
        formatted_message = self.app_state.log_manager.add_message(message, level)

        self.log_text.config(state="normal")
        self.log_text.insert("end", formatted_message + "\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see("end")

    def clear_log(self) -> None:
        """ログをクリア"""
        self.app_state.log_manager.clear_log()
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state=DISABLED)

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)
