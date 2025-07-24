#!/usr/bin/env python3
"""
Kumihan Formatter プレイグラウンド起動スクリプト
Issue #580 - ドキュメント改善 Phase 2

使用方法:
    python start_playground.py
    または
    python docs/playground/start_playground.py
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def main():
    """プレイグラウンドを起動"""

    # スクリプトのディレクトリを取得
    script_dir = Path(__file__).parent
    server_path = script_dir / "server.py"

    print("🎮 Kumihan Formatter Playground を起動しています...")
    print(f"📁 作業ディレクトリ: {script_dir}")

    # 必要な依存関係をチェック・インストール
    try:
        import fastapi
        import uvicorn

        print("✅ FastAPI依存関係が確認されました")
    except ImportError:
        print("📦 FastAPI依存関係をインストールしています...")
        try:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "fastapi",
                    "uvicorn",
                    "jinja2",
                    "python-multipart",
                ]
            )
            print("✅ 依存関係のインストールが完了しました")
        except subprocess.CalledProcessError as e:
            print(f"❌ 依存関係のインストールに失敗しました: {e}")
            return 1

    # サーバーファイルの存在確認
    if not server_path.exists():
        print(f"❌ サーバーファイルが見つかりません: {server_path}")
        return 1

    print("🚀 Webサーバーを起動しています...")
    print("📊 起動後、以下の機能が利用できます:")
    print("   • リアルタイムKumihan記法プレビュー")
    print("   • Mermaid図表の自動生成")
    print("   • DX指標ダッシュボード")
    print("   • Google Analytics 4統合")
    print()

    try:
        # 作業ディレクトリをスクリプトディレクトリに変更
        os.chdir(script_dir)

        # ブラウザを少し遅れて開く
        def open_browser():
            time.sleep(2)
            url = "http://localhost:8080"
            print(f"🌐 ブラウザでプレイグラウンドを開いています: {url}")
            webbrowser.open(url)

        import threading

        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Uvicornサーバーを起動
        subprocess.run([sys.executable, "server.py"])

    except KeyboardInterrupt:
        print("\n🛑 プレイグラウンドを停止しています...")
        return 0
    except Exception as e:
        print(f"❌ プレイグラウンドの起動に失敗しました: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
