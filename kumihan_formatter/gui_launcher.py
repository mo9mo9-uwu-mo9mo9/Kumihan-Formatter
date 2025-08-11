"""GUI Launcher for Kumihan-Formatter

エントリーポイント: MVCパターンで再構築されたGUIアプリケーションのランチャー
最小限のコードでGUIコントローラーを起動し、エラーハンドリングを提供
"""

import sys
from pathlib import Path
from typing import Any

# パスの設定
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


# デバッグロガーのインポート（代替実装）
def info(*args: Any, **kwargs: Any) -> None:
    pass


def error(*args: Any, **kwargs: Any) -> None:
    pass


def log_startup_info() -> None:
    pass


# スタートアップ情報のログ
log_startup_info()
info("GUI Launcher module loading...")

# GUIコントローラーのインポート
try:
    info("Importing GUI controller...")
    from .gui_controllers.gui_controller import create_gui_application

    info("GUI controller imported successfully")
except ImportError as gui_error:
    error(f"Failed to import GUI controller: {gui_error}")
    # 詳細なエラー情報を表示
    import traceback

    error(f"Import traceback: {traceback.format_exc()}")

    # フォールバック: エラーダイアログを表示して終了
    try:
        import tkinter.messagebox as mb

        mb.showerror(
            "インポートエラー",
            f"GUIコンポーネントの読み込みに失敗しました:\n\n{gui_error}\n\n"
            f"必要なモジュールがインストールされているか確認してください。",
        )
    except Exception:
        print(
            f"GUIコンポーネントの読み込みに失敗しました: {gui_error}", file=sys.stderr
        )

    sys.exit(1)


def main() -> None:
    """メイン関数: GUIアプリケーションのエントリーポイント"""
    try:
        info("Creating GUI application...")
        app = create_gui_application()

        info("Starting GUI application...")
        app.run()

        info("GUI application finished")

    except Exception as e:
        error(f"GUI application error: {e}")

        # エラーダイアログの表示
        try:
            import tkinter.messagebox as mb

            mb.showerror(
                "起動エラー",
                f"GUIの起動中にエラーが発生しました:\n\n{str(e)}\n\n"
                f"コマンドライン版の使用をお試しください。",
            )
        except Exception:
            # Tkinterも利用できない場合はコンソールに出力
            print(f"GUIの起動中にエラーが発生しました: {str(e)}", file=sys.stderr)
            print("コマンドライン版の使用をお試しください。", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
