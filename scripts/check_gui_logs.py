#!/usr/bin/env python3
"""GUI Log Checker

GUIアプリケーションのログファイルを確認・分析するユーティリティ
"""

import sys
from pathlib import Path
from datetime import datetime


def check_gui_logs():
    """GUIログファイルを確認"""
    print("🔍 Kumihan-Formatter GUI ログチェック")
    print("=" * 50)
    
    log_dir = Path("tmp")
    
    # 主要ログファイル
    log_files = {
        "dev.log": "統一ログシステム（メイン）",
        "gui_debug.log": "GUI専用デバッグログ", 
        "gui_crashes.log": "GUIクラッシュログ",
        "performance.log": "パフォーマンスログ"
    }
    
    found_logs = False
    
    for log_file, description in log_files.items():
        log_path = log_dir / log_file
        
        if log_path.exists():
            found_logs = True
            file_size = log_path.stat().st_size
            modified_time = datetime.fromtimestamp(log_path.stat().st_mtime)
            
            print(f"📄 {log_file}")
            print(f"   {description}")
            print(f"   📊 サイズ: {file_size:,} bytes")
            print(f"   🕒 更新: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 最後の数行を表示（クラッシュログの場合）
            if "crash" in log_file and file_size > 0:
                print(f"   🔥 最新クラッシュ:")
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        recent_lines = lines[-10:] if len(lines) > 10 else lines
                        for line in recent_lines:
                            print(f"      {line.rstrip()}")
                except Exception as e:
                    print(f"      ❌ 読み込みエラー: {e}")
            
            print()
        else:
            print(f"📄 {log_file}: 見つかりません")
    
    if not found_logs:
        print("📝 ログファイルが見つかりません")
        print("   GUIアプリを一度起動してからもう一度確認してください")
    
    print("\n🔧 ログ有効化コマンド:")
    print("   make -f Makefile.gui gui-test        # 開発環境でテスト起動")
    print("   ./dist/Kumihan-Formatter.app/Contents/MacOS/Kumihan-Formatter  # 直接実行")


def tail_gui_logs():
    """GUIログをリアルタイム監視"""
    print("👀 GUI ログリアルタイム監視")
    print("   Ctrl+C で停止")
    print("-" * 40)
    
    log_files = ["tmp/dev.log", "tmp/gui_debug.log", "tmp/gui_crashes.log"]
    
    try:
        import subprocess
        
        # 存在するログファイルのみを監視
        existing_files = [f for f in log_files if Path(f).exists()]
        
        if not existing_files:
            print("❌ 監視するログファイルが見つかりません")
            return
        
        # tailコマンドで複数ファイル監視
        cmd = ["tail", "-f"] + existing_files
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 ログ監視を停止しました")
    except Exception as e:
        print(f"❌ ログ監視エラー: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tail":
        tail_gui_logs()
    else:
        check_gui_logs()