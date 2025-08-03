#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kumihan-Formatter 対話型変換ツール (Mac用ダブルクリック実行)

ダブルクリックで実行可能な対話型のKumihan記法変換ツール
変換テストに最適化されています。
"""

import os
import sys
from pathlib import Path


def setup_encoding():
    """エンコーディング設定 (macOS用)"""
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def interactive_repl():
    """対話型変換REPL"""
    # プロジェクトルートをPythonパスに追加
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # エンコーディング設定
    setup_encoding()
    
    try:
        from kumihan_formatter.parser import Parser
        from kumihan_formatter.renderer import Renderer
        from kumihan_formatter.core.utilities.logger import get_logger
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("💡 プロジェクトディレクトリで実行していることを確認してください")
        input("\nEnterキーを押して終了...")
        return
    
    logger = get_logger(__name__)
    
    print("🚀 Kumihan-Formatter 対話型変換ツール")
    print("=" * 60)
    print("📝 Kumihan記法を入力してHTML変換をテストできます")
    print("💡 コマンド:")
    print("   - 'exit' または 'quit': 終了")
    print("   - 'help': ヘルプ表示")
    print("   - 'clear': 画面クリア")
    print("   - 'history': 変換履歴表示")
    print("   - 'examples': 記法例表示")
    print("-" * 60)
    
    parser = Parser()
    renderer = Renderer()
    
    history = []
    
    while True:
        try:
            # プロンプト表示
            user_input = input("\n📝 Kumihan記法> ").strip()
            
            if not user_input:
                continue
            
            # 特殊コマンド処理
            if user_input.lower() in ['exit', 'quit']:
                print("👋 終了します")
                break
                
            elif user_input.lower() == 'help':
                print("\n📖 ヘルプ:")
                print("  🔹 Kumihan記法を入力するとHTML変換されます")
                print("  🔹 基本構文: # 装飾名 #内容##")
                print("  🔹 例: # 太字 #重要なテキスト##")
                print("  🔹 'examples' で詳細な記法例を確認")
                continue
                
            elif user_input.lower() == 'clear':
                os.system('clear' if os.name == 'posix' else 'cls')
                print("🚀 Kumihan-Formatter 対話型変換ツール")
                print("=" * 60)
                continue
                
            elif user_input.lower() == 'history':
                if not history:
                    print("📚 変換履歴は空です")
                else:
                    print("\n📚 変換履歴 (最新10件):")
                    for i, (input_text, output_html) in enumerate(history[-10:], 1):
                        print(f"  {i:2d}. 入力: {input_text[:40]}{'...' if len(input_text) > 40 else ''}")
                        print(f"      出力: {output_html[:80]}{'...' if len(output_html) > 80 else ''}")
                        print()
                continue
                
            elif user_input.lower() == 'examples':
                print("\n📖 Kumihan記法例:")
                examples = [
                    ("# 太字 #重要##", "太字（strong）"),
                    ("# イタリック #強調##", "イタリック（em）"),
                    ("# 見出し1 #メインタイトル##", "見出し1（h1）"),
                    ("# 見出し2 #サブタイトル##", "見出し2（h2）"),
                    ("# ハイライト #注目##", "ハイライト（mark）"),
                    ("# 太字 #重要## な # イタリック #内容##", "複合記法"),
                ]
                for example, desc in examples:
                    print(f"  🔹 {example}")
                    print(f"    → {desc}")
                    print()
                continue
            
            # Kumihan記法の変換実行
            try:
                # パース処理
                result = parser.parse(user_input)
                
                # HTML生成
                html_content = renderer.render(result)
                
                # 結果表示
                print(f"\n✅ 変換成功:")
                print(f"📄 HTML: {html_content}")
                
                # プレーンテキスト表示（デバッグ用）
                import re
                plain_text = re.sub(r'<[^>]+>', '', html_content)
                if plain_text != html_content:
                    print(f"📋 Text: {plain_text}")
                
                # 履歴に追加
                history.append((user_input, html_content))
                
            except Exception as parse_error:
                print(f"\n❌ 変換エラー: {parse_error}")
                print("💡 記法を確認してください。'examples' で例を参照")
                logger.error(f"Parse error: {parse_error}")
                
        except KeyboardInterrupt:
            print("\n\n👋 Ctrl+C で終了します")
            break
        except EOFError:
            print("\n👋 EOF で終了します")
            break
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            logger.error(f"Unexpected error: {e}")
    
    print("\n🎉 対話セッション終了")
    input("Enterキーを押してウィンドウを閉じます...")


if __name__ == "__main__":
    interactive_repl()