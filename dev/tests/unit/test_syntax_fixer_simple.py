#!/usr/bin/env python3
"""
Syntax Fixer 簡単テストスイート
"""

import tempfile
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dev.tools.syntax_fixer import SyntaxFixer


def test_combine_markers():
    """マーカー統合ロジックテスト"""
    print("🧪 マーカー統合テスト実行中...")
    
    fixer = SyntaxFixer()
    
    # 基本的な統合
    markers = [";;;太字;;;", ";;;イタリック;;;"]
    result = fixer._combine_markers(markers)
    expected = ";;;太字+イタリック;;;"
    print(f"デバッグ: markers={markers}, result={result}")
    assert result == expected, f"期待値: {expected}, 実際: {result}"
    print("✅ 基本統合: OK")
    
    # color属性付き統合
    markers = [";;;ハイライト color=#ff0000;;;", ";;;太字;;;"]
    result = fixer._combine_markers(markers)
    expected = ";;;ハイライト+太字 color=#ff0000;;;"
    print(f"デバッグ: markers={markers}, result={result}")
    assert result == expected, f"期待値: {expected}, 実際: {result}"
    print("✅ color属性統合: OK")


def test_malformed_blocks():
    """見出しブロック修正テスト"""
    print("🧪 見出しブロック修正テスト実行中...")
    
    content = """;;;見出し1
テストタイトル

;;;見出し2
サブタイトル"""
    
    fixer = SyntaxFixer()
    fixed_content, changes = fixer._fix_malformed_blocks(content)
    
    expected = """;;;見出し1
テストタイトル
;;;

;;;見出し2
サブタイトル
;;;"""
    
    assert fixed_content == expected, f"期待値と実際の内容が異なります"
    assert len(changes) == 2, f"変更数期待値: 2, 実際: {len(changes)}"
    print("✅ 見出しブロック修正: OK")


def test_file_processing():
    """ファイル処理統合テスト"""
    print("🧪 ファイル処理統合テスト実行中...")
    
    test_content = """;;;見出し1
テスト

;;;見出し2
終了"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        fixer = SyntaxFixer()
        result = fixer.fix_file(temp_path, preview_only=True)
        
        print(f"デバッグ: errors_fixed={result.errors_fixed}")
        print(f"デバッグ: changes_made={result.changes_made}")
        print(f"デバッグ: original!=fixed: {result.original_content != result.fixed_content}")
        
        # 修正が検出されることを確認
        assert result.errors_fixed > 0, f"修正箇所が検出されませんでした: {result.changes_made}"
        assert result.original_content != result.fixed_content, f"修正内容が変更されていません\n元:\n{result.original_content}\n修正:\n{result.fixed_content}"
        print("✅ ファイル処理: OK")
        
    finally:
        temp_path.unlink()  # 一時ファイルを削除


def run_all_tests():
    """全テストを実行"""
    print("🚀 Syntax Fixer テスト開始\n")
    
    try:
        test_combine_markers()
        test_malformed_blocks() 
        test_file_processing()
        
        print("\n🎉 全テスト合格!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        return False
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)