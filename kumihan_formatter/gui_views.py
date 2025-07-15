"""GUI Views for Kumihan-Formatter

View層: UIコンポーネント管理とレイアウト
MVCパターンでのView部分を担当し、ユーザーインターフェースの構築・更新を提供
"""

from tkinter import *
from tkinter import ttk
from typing import Any, Callable, Optional

from .gui_models import AppState


class MainWindow:
    """メインウィンドウクラス

    アプリケーションのメインウィンドウとグローバルレイアウトを管理
    """

    def __init__(self, app_state: AppState) -> None:
        """メインウィンドウの初期化"""
        self.app_state = app_state
        self.root = Tk()
        self._setup_window()
        self._setup_style()

    def _setup_window(self) -> None:
        """ウィンドウの基本設定"""
        self.root.title("Kumihan-Formatter v1.0 - 美しい組版を、誰でも簡単に")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

    def _setup_style(self) -> None:
        """スタイルの設定"""
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def center_window(self) -> None:
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        pos_x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def get_root(self) -> Tk:
        """Tkルートウィンドウを取得"""
        return self.root


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

    def __init__(self, parent: Widget, app_state: AppState) -> None:
        """ファイル選択フレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.LabelFrame(parent, text="ファイル選択", padding="10")
        self._setup_file_selection()

    def _setup_file_selection(self) -> None:
        """ファイル選択UIの構築"""
        self.frame.columnconfigure(1, weight=1)

        # 入力ファイル選択
        ttk.Label(self.frame, text="入力ファイル:").grid(
            row=0, column=0, sticky=W, padx=(0, 10)
        )
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

    def __init__(self, parent: Widget, app_state: AppState) -> None:
        """オプションフレームの初期化"""
        self.parent = parent
        self.app_state = app_state
        self.frame = ttk.LabelFrame(parent, text="変換オプション", padding="10")
        self._setup_options()

    def _setup_options(self) -> None:
        """オプション設定UIの構築"""
        self.frame.columnconfigure(1, weight=1)

        # テンプレート選択
        ttk.Label(self.frame, text="テンプレート:").grid(
            row=0, column=0, sticky=W, padx=(0, 10)
        )
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


class ActionButtonFrame:
    """アクションボタンフレームクラス

    変換実行、サンプル生成、ヘルプ等のアクションボタン
    """

    def __init__(self, parent: Widget, app_state: AppState) -> None:
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

    def __init__(self, parent: Widget, app_state: AppState) -> None:
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

    def __init__(self, parent: Widget, app_state: AppState) -> None:
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

        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, formatted_message + "\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)

    def clear_log(self) -> None:
        """ログをクリア"""
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)
        self.app_state.log_manager.clear_messages()

    def pack(self, **kwargs: Any) -> None:
        """フレームをパック"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """フレームをグリッド配置"""
        self.frame.grid(**kwargs)


class HelpDialog:
    """ヘルプダイアログクラス

    ヘルプ情報を表示するモーダルダイアログ
    """

    def __init__(self, parent: Tk) -> None:
        """ヘルプダイアログの初期化"""
        self.parent = parent
        self.window: Optional[Toplevel] = None

    def show(self) -> None:
        """ヘルプダイアログを表示"""
        if self.window:
            self.window.destroy()

        self.window = Toplevel(self.parent)
        self.window.title("ヘルプ")
        self.window.geometry("600x500")
        self.window.transient(self.parent)
        self.window.grab_set()

        self._center_window()
        self._setup_content()

    def _center_window(self) -> None:
        """ダイアログを画面中央に配置"""
        if not self.window:
            return

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")

    def _setup_content(self) -> None:
        """ヘルプコンテンツの設定"""
        if not self.window:
            return

        help_text = """Kumihan-Formatter GUI ヘルプ

【基本的な使い方】
1. 「参照」ボタンから変換したいテキストファイルを選択
2. 出力フォルダを指定（デフォルト: ./dist）
3. 必要に応じてオプションを設定
4. 「変換実行」ボタンをクリック

【オプション説明】
• テンプレート: 出力HTMLのテンプレートを選択
• ソース表示機能: 原文と変換結果を切り替え表示する機能
• プレビューをスキップ: 変換後にブラウザを自動で開かない

【サンプル生成】
「サンプル生成」ボタンで機能紹介用のサンプルファイルを生成できます。

【サポート】
詳細な使い方やトラブルシューティングは、
プロジェクトのドキュメントを参照してください。

GitHub: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
"""

        # コンテンツフレーム
        text_frame = Frame(self.window)
        text_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # ヘルプテキスト
        help_text_widget = Text(text_frame, wrap=WORD, padx=10, pady=10)
        help_scrollbar = ttk.Scrollbar(
            text_frame, orient=VERTICAL, command=help_text_widget.yview
        )
        help_text_widget.configure(yscrollcommand=help_scrollbar.set)

        help_text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        help_scrollbar.pack(side=RIGHT, fill=Y)

        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state=DISABLED)

        # 閉じるボタン
        ttk.Button(self.window, text="閉じる", command=self.window.destroy).pack(
            pady=10
        )


class MainView:
    """メインビュークラス

    すべてのUIコンポーネントを統合して管理する中央ビュー
    """

    def __init__(self, app_state: AppState) -> None:
        """メインビューの初期化"""
        self.app_state = app_state

        # メインウィンドウ作成
        self.main_window = MainWindow(app_state)
        self.root = self.main_window.get_root()

        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="WENS")

        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(6, weight=1)  # ログフレームを伸縮可能に

        # UI コンポーネント作成
        self._create_components()
        self._layout_components()

        # ウィンドウ中央配置
        self.main_window.center_window()

    def _create_components(self) -> None:
        """UIコンポーネントの作成"""
        self.header_frame = HeaderFrame(self.main_frame)
        self.file_selection_frame = FileSelectionFrame(self.main_frame, self.app_state)
        self.options_frame = OptionsFrame(self.main_frame, self.app_state)
        self.action_button_frame = ActionButtonFrame(self.main_frame, self.app_state)
        self.progress_frame = ProgressFrame(self.main_frame, self.app_state)
        self.log_frame = LogFrame(self.main_frame, self.app_state)
        self.help_dialog = HelpDialog(self.root)

    def _layout_components(self) -> None:
        """UIコンポーネントのレイアウト"""
        self.header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        self.file_selection_frame.grid(
            row=1, column=0, columnspan=3, sticky="WE", pady=(0, 10)
        )
        self.options_frame.grid(
            row=2, column=0, columnspan=3, sticky="WE", pady=(0, 10)
        )
        self.action_button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        self.progress_frame.grid(
            row=4, column=0, columnspan=3, sticky="WE", pady=(0, 10)
        )
        self.log_frame.grid(row=5, column=0, columnspan=3, sticky="WENS", pady=(0, 10))

    def set_ui_enabled(self, enabled: bool) -> None:
        """UI要素の有効/無効を一括設定"""
        state = NORMAL if enabled else DISABLED

        def update_widget_state(widget: Widget) -> None:
            try:
                if isinstance(
                    widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)
                ):
                    widget.configure(state=state)
            except:
                pass

            for child in widget.winfo_children():
                update_widget_state(child)

        # rootはTkクラスなので、直接のWidget子要素を更新
        for child in self.root.winfo_children():
            update_widget_state(child)

    def update_display(self) -> None:
        """画面表示を更新"""
        self.root.update_idletasks()

    def start_mainloop(self) -> None:
        """メインループを開始"""
        self.root.mainloop()
