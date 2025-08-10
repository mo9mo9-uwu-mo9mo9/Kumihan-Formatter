"""Dialog windows for Kumihan-Formatter GUI

Single Responsibility Principle適用: ダイアログウィンドウ管理の分離
Issue #476対応 - gui_views.py分割（4/4）
"""

from tkinter import BOTH, LEFT, RIGHT, VERTICAL, WORD, Frame, Text, Toplevel, Y, ttk
from tkinter.ttk import Widget
from typing import Optional


class HelpDialog:
    """ヘルプダイアログクラス

    使い方説明とヘルプ情報の表示
    """

    def __init__(self, parent: Widget) -> None:
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
        if hasattr(self.parent, "winfo_toplevel"):
            self.window.transient(self.parent.winfo_toplevel())
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
        help_scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=help_text_widget.yview)
        help_text_widget.configure(yscrollcommand=help_scrollbar.set)

        help_text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        help_scrollbar.pack(side=RIGHT, fill=Y)

        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state="disabled")

        # 閉じるボタン
        ttk.Button(self.window, text="閉じる", command=self.window.destroy).pack(pady=10)
