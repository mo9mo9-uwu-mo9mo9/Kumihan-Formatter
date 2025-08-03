#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Kumihan-Formatter 変換ツール (Mac用GUI版)

ダブルクリックで簡単起動！Kumihan記法をHTMLに変換する対話型ツール

✨ 特徴:
- 📝 リアルタイム記法テスト
- 📁 ドラッグ&ドロップファイル変換
- 🎨 直感的なユーザーインターフェース
- 🚀 高速変換エンジン

🔧 使い方:
- "Kumihan-Formatter.app" をダブルクリックして起動
- または Terminal から: python3 "Kumihan変換ツール.py"
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


def main_menu():
    """メインメニュー表示と選択"""
    print("🚀 Kumihan-Formatter 変換ツール")
    print("=" * 70)
    print("📝 Kumihan記法をHTMLに変換する高性能ツール")
    print("=" * 70)
    print("📋 利用可能なモード:")
    print("  1️⃣  対話型変換 (リアルタイム記法テスト)")
    print("  2️⃣  ファイル変換 (ドラッグ&ドロップによる一括変換)")
    print("-" * 70)
    print("💡 ヒント: Kumihan-Formatter.app をダブルクリックで簡単起動！")
    
    while True:
        try:
            choice = input("\nモードを選択してください (1/2) または 'quit' で終了: ").strip()
            
            if choice.lower() in ['quit', 'exit']:
                print("👋 終了します")
                return None
            elif choice == '1':
                return 'interactive'
            elif choice == '2':
                return 'file_conversion'
            else:
                print("❌ 無効な選択です。1または2を入力してください。")
        except KeyboardInterrupt:
            print("\n👋 Ctrl+C で終了します")
            return None
        except EOFError:
            print("\n👋 EOF で終了します")
            return None


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
    
    print("\n📝 対話型変換モード")
    print("=" * 60)
    print("📝 Kumihan記法を入力してHTML変換をテストできます")
    print("💡 コマンド:")
    print("   - 'exit' または 'quit': 終了")
    print("   - 'back': メインメニューに戻る")
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

def file_conversion_mode():
    """ファイル変換モード（D&D対応）"""
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
        input("\nEnterキーを押してメインメニューに戻る...")
        return
    
    logger = get_logger(__name__)
    
    print("\n📁 ファイル変換モード")
    print("=" * 60)
    print("📁 Kumihanファイルを一括変換できます")
    print("💡 使用方法:")
    print("   1. 変換したいファイルパスを入力")
    print("   2. 複数ファイルはカンマ区切りで指定")
    print("   3. ディレクトリを指定すると配下の.kumihanファイルを一括変換")
    print("💡 コマンド:")
    print("   - 'back': メインメニューに戻る")
    print("   - 'quit': 終了")
    print("-" * 60)
    
    parser = Parser()
    renderer = Renderer()
    
    while True:
        try:
            # ファイルパス入力
            user_input = input("\n📁 変換するファイル/ディレクトリパス> ").strip()
            
            if not user_input:
                continue
            
            # 特殊コマンド処理
            if user_input.lower() == 'back':
                print("🔙 メインメニューに戻ります")
                break
                
            elif user_input.lower() in ['quit', 'exit']:
                print("👋 終了します")
                sys.exit(0)
            
            # ファイル処理
            process_files(user_input, parser, renderer, logger)
                
        except KeyboardInterrupt:
            print("\n\n👋 Ctrl+C でメインメニューに戻ります")
            break
        except EOFError:
            print("\n👋 EOF でメインメニューに戻ります")
            break
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            logger.error(f"Unexpected error in file conversion mode: {e}")


def process_files(input_paths: str, parser, renderer, logger):
    """ファイル処理メイン関数（セキュリティ・パフォーマンス強化版）"""
    import glob
    import time
    
    # セキュリティ設定
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB制限
    MAX_FILES_COUNT = 1000  # 最大処理ファイル数
    
    # カンマ区切りでパス分割
    paths = [path.strip().strip('"\'') for path in input_paths.split(',')]
    
    all_files = []
    
    # 各パスを処理
    for path_str in paths:
        path = Path(path_str).expanduser().resolve()
        
        if path.is_file():
            # 単一ファイル
            if is_kumihan_file(path):
                if is_file_safe(path, MAX_FILE_SIZE):
                    all_files.append(path)
                else:
                    print(f"⚠️  スキップ: {path.name} (ファイルサイズが大きすぎます: {path.stat().st_size / 1024 / 1024:.1f}MB)")
            else:
                print(f"⚠️  スキップ: {path.name} (Kumihanファイルではありません)")
                
        elif path.is_dir():
            # ディレクトリ：.kumihanファイルを検索
            kumihan_files = find_kumihan_files(path)
            # ファイルサイズチェック
            safe_files = [f for f in kumihan_files if is_file_safe(f, MAX_FILE_SIZE)]
            
            if safe_files:
                all_files.extend(safe_files)
                skipped_count = len(kumihan_files) - len(safe_files)
                print(f"📂 {path.name}: {len(safe_files)}個のKumihanファイルを発見")
                if skipped_count > 0:
                    print(f"    ⚠️  {skipped_count}個のファイルをサイズ制限によりスキップ")
            else:
                print(f"📂 {path.name}: 処理可能なKumihanファイルが見つかりませんでした")
                
        else:
            # ワイルドカード対応
            try:
                matched_files = glob.glob(str(path))
                for matched_path in matched_files:
                    file_path = Path(matched_path)
                    if file_path.is_file() and is_kumihan_file(file_path) and is_file_safe(file_path, MAX_FILE_SIZE):
                        all_files.append(file_path)
                        
                if not matched_files:
                    print(f"❌ パスが見つかりません: {path_str}")
            except Exception as e:
                print(f"❌ パス処理エラー: {path_str} - {e}")
    
    # ファイル数制限チェック
    if len(all_files) > MAX_FILES_COUNT:
        print(f"⚠️  ファイル数が制限を超えています。最初の{MAX_FILES_COUNT}個のみ処理します。")
        all_files = all_files[:MAX_FILES_COUNT]
    
    if not all_files:
        print("❌ 変換可能なKumihanファイルが見つかりませんでした")
        return
    
    # 変換実行
    print(f"\n🚀 {len(all_files)}個のファイルを変換開始...")
    start_time = time.time()
    
    success_count = 0
    error_count = 0
    total_input_size = 0
    total_output_size = 0
    
    for i, file_path in enumerate(all_files, 1):
        try:
            # プログレス表示の改善
            print(f"\n[{i:3d}/{len(all_files)}] {file_path.name} ", end="", flush=True)
            
            # ファイル読み込み
            file_stat = file_path.stat()
            total_input_size += file_stat.st_size
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("📖 ", end="", flush=True)  # 読み込み完了
            
            # パース＆レンダリング
            result = parser.parse(content)
            print("🔄 ", end="", flush=True)  # パース完了
            
            html_content = renderer.render(result)
            print("🎨 ", end="", flush=True)  # レンダリング完了
            
            # 出力ファイル名決定
            output_path = file_path.with_suffix('.html')
            
            # HTML出力
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            output_stat = output_path.stat()
            total_output_size += output_stat.st_size
            
            print(f"✅ 成功: {output_path.name} ({output_stat.st_size / 1024:.1f}KB)")
            success_count += 1
            
        except UnicodeDecodeError as e:
            print(f"❌ 文字エンコーディングエラー: {e}")
            error_count += 1
            logger.error(f"Encoding error for {file_path}: {e}")
        except MemoryError as e:
            print(f"❌ メモリ不足: ファイルが大きすぎます")
            error_count += 1
            logger.error(f"Memory error for {file_path}: {e}")
        except Exception as e:
            print(f"❌ 失敗: {e}")
            error_count += 1
            logger.error(f"File conversion error for {file_path}: {e}")
    
    # 結果サマリー（詳細版）
    elapsed_time = time.time() - start_time
    
    print(f"\n📊 変換完了:")
    print(f"   ✅ 成功: {success_count}ファイル")
    if error_count > 0:
        print(f"   ❌ 失敗: {error_count}ファイル")
    
    print(f"   📁 出力ディレクトリ: {all_files[0].parent if all_files else '(なし)'}")
    print(f"   ⏱️  処理時間: {elapsed_time:.2f}秒")
    print(f"   📊 入力サイズ: {total_input_size / 1024:.1f}KB")
    print(f"   📊 出力サイズ: {total_output_size / 1024:.1f}KB")
    
    if success_count > 0:
        avg_time = elapsed_time / success_count
        print(f"   📈 平均処理時間: {avg_time:.2f}秒/ファイル")

def is_kumihan_file(file_path: Path) -> bool:
    """Kumihanファイルかどうかを判定"""
    valid_extensions = {'.kumihan', '.txt', '.md'}
    return file_path.suffix.lower() in valid_extensions

def is_file_safe(file_path: Path, max_size: int) -> bool:
    """ファイルが安全に処理可能かをチェック
    
    Args:
        file_path: チェック対象のファイルパス
        max_size: 最大ファイルサイズ（バイト）
    
    Returns:
        bool: 安全に処理可能な場合True
    """
    try:
        # ファイルサイズチェック
        file_stat = file_path.stat()
        if file_stat.st_size > max_size:
            return False
        
        # 読み取り権限チェック
        if not file_path.is_file() or not os.access(file_path, os.R_OK):
            return False
            
        # 空ファイルチェック
        if file_stat.st_size == 0:
            return False
            
        return True
        
    except (OSError, PermissionError):
        return False


def find_kumihan_files(directory: Path) -> list[Path]:
    """ディレクトリ内のKumihanファイルを検索"""
    kumihan_files = []
    
    # 再帰的に検索
    for ext in ['.kumihan', '.txt', '.md']:
        pattern = f"**/*{ext}"
        kumihan_files.extend(directory.glob(pattern))
    
    # ファイル名でソート
    return sorted(kumihan_files)


def main():
    """メインエントリーポイント"""
    setup_encoding()
    
    while True:
        mode = main_menu()
        
        if mode is None:  # ユーザーが終了を選択
            break
        elif mode == 'interactive':
            interactive_repl()
        elif mode == 'file_conversion':
            file_conversion_mode()
            
    print("👋 Kumihan-Formatter を終了します")


if __name__ == "__main__":
    main()