#!/usr/bin/env python3
"""
Kumihan記法検証システム - Claude Code専用
記法記述ミスを防ぎ、正しいパターンをガイドする機能
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class NotationError:
    """記法エラー情報"""
    pattern: str
    position: int
    error_type: str
    suggestion: str


class NotationValidator:
    """Kumihan記法バリデーター"""
    
    def __init__(self):
        # 正しい記法パターン（改良版 - 複合記法・色属性対応）
        self.correct_patterns = {
            'inline': r'#([^#]+(?:\+[^#]+)*)(?:\s+color=[^#\s]+)?#\s+([^#]+)##',
            'block': r'#([^#]+(?:\+[^#]+)*)(?:\s+color=[^#\s]+)?#\n([^#]*)\n##',
            'inline_color': r'#(ハイライト)\s+color=([^#\s]+)#\s+([^#]+)##',
            'block_color': r'#(ハイライト)\s+color=([^#\s]+)#\n([^#]*)\n##'
        }
        
        # よくある間違いパターン（拡張版）
        self.error_patterns = {
            'duplicate_keyword': r'#([^#\s]+)#\s+([^#]+)#\1#',  # #太字# 内容#太字#
            'missing_closing': r'#([^#\s]+)#\s+([^#]+)$',       # #太字# 内容（##なし）
            'wrong_closing': r'#([^#\s]+)#\s+([^#]+)#([^#\s]*[^#])#',  # #太字# 内容#間違い#
            'invalid_color': r'#ハイライト\s+color=([^#\s]+)#',  # 無効色チェック用
            'malformed_compound': r'#([^#]+\+[^#]*\s|[^#]*\s\+[^#]+)#',  # 複合記法エラー
            'nested_markers': r'#[^#]*#[^#]*#[^#]*##',  # ネストエラー
        }
        
        # 有効キーワード
        self.valid_keywords = {
            "太字", "イタリック", "下線", "取り消し線", "コード", "引用", "枠線", 
            "ハイライト", "見出し1", "見出し2", "見出し3", "見出し4", "見出し5",
            "折りたたみ", "ネタバレ", "中央寄せ", "注意", "情報", "コードブロック"
        }
        
        # 色名
        self.valid_colors = {
            "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
            "black", "white", "gray", "cyan", "magenta", "lime", "navy", "olive",
            "maroon", "teal", "silver", "gold", "indigo", "violet", "coral", "salmon",
            "khaki", "crimson", "azure", "beige", "turquoise", "lavender"
        }

    def validate_text(self, text: str) -> Tuple[bool, List[NotationError]]:
        """テキスト全体の記法検証（最適化版）"""
        errors = []
        
        # 一回のスキャンで全エラーパターンをチェック
        for error_type, pattern in self.error_patterns.items():
            for match in re.finditer(pattern, text):
                error_info = self._create_error_info(error_type, match)
                if error_info:
                    errors.append(error_info)
        
        # キーワード妥当性チェック（統合）
        self._validate_keywords(text, errors)
        
        return len(errors) == 0, errors
    
    def _create_error_info(self, error_type: str, match: re.Match) -> NotationError:
        """エラー情報生成（共通化）"""
        if error_type == 'duplicate_keyword':
            keyword = match.group(1)
            content = match.group(2)
            return NotationError(
                pattern=match.group(0),
                position=match.start(),
                error_type="重複キーワード",
                suggestion=f"#{keyword}# {content}##"
            )
        elif error_type == 'missing_closing':
            keyword = match.group(1)
            content = match.group(2)
            return NotationError(
                pattern=match.group(0),
                position=match.start(),
                error_type="閉じタグ不足",
                suggestion=f"#{keyword}# {content}##"
            )
        elif error_type == 'invalid_color':
            color = match.group(1)
            return NotationError(
                pattern=match.group(0),
                position=match.start(),
                error_type="無効色名",
                suggestion=f"有効色: red, blue, #ff0000 など"
            )
        elif error_type == 'malformed_compound':
            return NotationError(
                pattern=match.group(0),
                position=match.start(),
                error_type="複合記法エラー",
                suggestion="正しい複合: #太字+イタリック# 内容##"
            )
        elif error_type == 'nested_markers':
            return NotationError(
                pattern=match.group(0),
                position=match.start(),
                error_type="ネスト構造エラー",
                suggestion="記法のネストは避けてください"
            )
        return None
    
    def _validate_keywords(self, text: str, errors: List[NotationError]):
        """キーワード妥当性チェック（分離）"""
        inline_pattern = r'#([^#\s]+)#'
        for match in re.finditer(inline_pattern, text):
            keyword = match.group(1)
            # 複合キーワードを分解
            keywords = keyword.split('+')
            base_keywords = [k.split()[0] for k in keywords]  # color属性除去
            
            for base_keyword in base_keywords:
                if base_keyword not in self.valid_keywords:
                    errors.append(NotationError(
                        pattern=match.group(0),
                        position=match.start(),
                        error_type="無効キーワード",
                        suggestion=f"有効キーワード: {', '.join(list(self.valid_keywords)[:5])}..."
                    ))

    def suggest_notation(self, keyword: str, content: str, use_color: bool = False, 
                        color: str = None, block_mode: bool = False) -> str:
        """正しい記法を提案"""
        if keyword not in self.valid_keywords:
            return f"❌ 無効キーワード: {keyword}"
        
        if use_color and keyword == "ハイライト":
            if color and (color in self.valid_colors or re.match(r'^#[0-9a-fA-F]{6}$', color)):
                if block_mode:
                    return f"#{keyword} color={color}#\n{content}\n##"
                else:
                    return f"#{keyword} color={color}# {content}##"
            else:
                return f"❌ 無効色: {color}. 有効色: red, blue, #ff0000 など"
        else:
            if block_mode:
                return f"#{keyword}#\n{content}\n##"
            else:
                return f"#{keyword}# {content}##"

    def get_templates(self) -> Dict[str, str]:
        """記法テンプレート集"""
        return {
            "基本インライン": "#{keyword}# {content}##",
            "基本ブロック": "#{keyword}#\n{content}\n##",
            "色付きハイライト": "#ハイライト color={color}# {content}##",
            "複合記法": "#{keyword1}+{keyword2}# {content}##",
            "見出し例": "#見出し1# タイトル##",
            "コード例": "#コード# console.log('Hello')##",
            "注意事項例": "#注意# 重要な情報です##"
        }

    def fix_common_errors(self, text: str) -> str:
        """よくあるエラーの自動修正"""
        # 重複キーワードエラーを修正
        for pattern_match in re.finditer(self.error_patterns['duplicate_keyword'], text):
            keyword = pattern_match.group(1)
            content = pattern_match.group(2)
            correct = f"#{keyword}# {content}##"
            text = text.replace(pattern_match.group(0), correct)
        
        return text


def validate_notation_interactive():
    """対話式記法検証"""
    validator = NotationValidator()
    
    print("🔍 Kumihan記法バリデーター")
    print("=" * 50)
    print("記法を入力してください（'exit'で終了）:")
    
    while True:
        user_input = input("\n📝 記法: ").strip()
        
        if user_input.lower() == 'exit':
            break
        
        if not user_input:
            continue
            
        # 検証実行
        is_valid, errors = validator.validate_text(user_input)
        
        if is_valid:
            print("✅ 正しい記法です！")
        else:
            print("❌ 記法エラーが見つかりました:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error.error_type}: {error.pattern}")
                print(f"     提案: {error.suggestion}")
            
            # 自動修正提案
            fixed = validator.fix_common_errors(user_input)
            if fixed != user_input:
                print(f"\n🔧 自動修正案: {fixed}")
    
    print("\n👋 検証終了")


def main():
    """メイン実行"""
    print("🚀 Kumihan記法検証システム")
    
    # テンプレート表示
    validator = NotationValidator()
    templates = validator.get_templates()
    
    print("\n📋 記法テンプレート:")
    for name, template in templates.items():
        print(f"  {name}: {template}")
    
    # 対話モード開始
    validate_notation_interactive()


if __name__ == "__main__":
    main()