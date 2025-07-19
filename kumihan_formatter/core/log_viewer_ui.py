"""GUI Log Viewer UI Components for Kumihan-Formatter
GUIアプリケーション用のログビューアーUIコンポーネント
"""

from typing import TYPE_CHECKING, Optional

# tkinterは必要時にのみインポート（CI環境での問題回避）
if TYPE_CHECKING:
    import tkinter as tk
    from tkinter import scrolledtext, ttk
else:
    try:
        import tkinter as tk
        from tkinter import scrolledtext, ttk
    except ImportError:
        # CI環境やheadless環境ではtkinterが利用できない場合がある
        tk = None  # type: ignore
        scrolledtext = None  # type: ignore
        ttk = None  # type: ignore


class LogViewerUI:
    """ログビューアーのUIコンポーネント管理"""

    def __init__(self, window: "tk.Widget") -> None:
        self.window = window
        self.log_text: Optional["scrolledtext.ScrolledText"] = None
        self.auto_scroll_var: Optional["tk.BooleanVar"] = None
        self.level_var: Optional["tk.StringVar"] = None
        self.status_var: Optional["tk.StringVar"] = None

    def setup_ui(
        self,
        clear_callback: callable,
        toggle_auto_scroll_callback: callable,
        open_log_file_callback: callable,
        filter_logs_callback: callable,
    ) -> None:
        """UIコンポーネントのセットアップ"""
        self._setup_toolbar(
            clear_callback,
            toggle_auto_scroll_callback,
            open_log_file_callback,
            filter_logs_callback,
        )
        self._setup_log_text_area()
        self._setup_status_bar()

    def _setup_toolbar(
        self,
        clear_callback: callable,
        toggle_auto_scroll_callback: callable,
        open_log_file_callback: callable,
        filter_logs_callback: callable,
    ) -> None:
        """ツールバーのセットアップ"""
        # ツールバー
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # クリアボタン
        ttk.Button(toolbar, text="ログクリア", command=clear_callback).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        # 自動スクロールチェックボックス
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar,
            text="自動スクロール",
            variable=self.auto_scroll_var,
            command=toggle_auto_scroll_callback,
        ).pack(side=tk.LEFT, padx=(0, 5))

        # ログファイルを開くボタン
        ttk.Button(
            toolbar, text="ログファイルを開く", command=open_log_file_callback
        ).pack(side=tk.LEFT, padx=(0, 5))

        # ログレベルフィルター
        ttk.Label(toolbar, text="レベル:").pack(side=tk.LEFT, padx=(10, 5))
        self.level_var = tk.StringVar(value="ALL")
        level_combo = ttk.Combobox(
            toolbar,
            textvariable=self.level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=10,
        )
        level_combo.pack(side=tk.LEFT)
        level_combo.bind("<<ComboboxSelected>>", filter_logs_callback)

    def _setup_log_text_area(self) -> None:
        """ログテキストエリアのセットアップ"""
        # ログテキストエリア
        text_frame = ttk.Frame(self.window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(
            text_frame, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # ログレベルごとの色設定
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure(
            "ERROR", foreground="red", font=("Consolas", 10, "bold")
        )

    def _setup_status_bar(self) -> None:
        """ステータスバーのセットアップ"""
        # ステータスバー
        self.status_var = tk.StringVar(value="ログビューアー起動中...")
        status_bar = ttk.Label(
            self.window,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def get_auto_scroll_state(self) -> bool:
        """自動スクロール状態を取得"""
        return self.auto_scroll_var.get() if self.auto_scroll_var else True

    def get_level_filter(self) -> str:
        """レベルフィルターを取得"""
        return self.level_var.get() if self.level_var else "ALL"

    def set_status(self, message: str) -> None:
        """ステータスメッセージを設定"""
        if self.status_var:
            self.status_var.set(message)

    def clear_log_text(self) -> None:
        """ログテキストをクリア"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

    def add_log_entry(self, log_line: str, tag: str) -> None:
        """ログエントリを追加"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_line + "\n", tag)
            self.log_text.config(state=tk.DISABLED)

    def scroll_to_end(self) -> None:
        """テキストエリアを最下部にスクロール"""
        if self.log_text:
            self.log_text.see(tk.END)
