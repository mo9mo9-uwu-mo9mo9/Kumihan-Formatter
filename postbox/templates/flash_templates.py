#!/usr/bin/env python3
"""
Flash 2.5 Optimization Templates
エラータイプ別修正テンプレート・ステップバイステップ指示
"""

from typing import Dict, List, Any
import re

class Flash25Templates:
    """Flash 2.5向け修正テンプレート・指示生成"""

    def __init__(self):
        self.error_templates = {
            "no-untyped-def": {
                "name": "戻り値型注釈不足",
                "difficulty": "easy",
                "typical_patterns": [
                    {
                        "pattern": r"def\s+(\w+)\s*\([^)]*\)\s*:",
                        "fix_template": "def {func_name}({params}) -> {return_type}:",
                        "return_types": {
                            "print|log|write": "None",
                            "get|fetch|load|read": "str | dict | list",
                            "count|len|size": "int",
                            "check|is_|has_": "bool",
                            "process|handle|execute": "None | bool",
                            "create|make|build": "object"
                        }
                    }
                ],
                "flash_instruction_template": """
🎯 戻り値型注釈追加
📝 手順:
1. 関数定義の行を見つける
2. ): の前に -> 型名 を追加
3. 型名は以下から選択:
   - None: 何も返さない
   - str: 文字列を返す
   - int: 数値を返す
   - bool: True/Falseを返す
   - list: リストを返す
   - dict: 辞書を返す

✅ 修正例:
def get_config():  → def get_config() -> dict:
def log_message():  → def log_message() -> None:
""",
                "validation_pattern": r"def\s+\w+\s*\([^)]*\)\s*->\s*\w+:"
            },

            "no-untyped-call": {
                "name": "型注釈なし関数呼び出し",
                "difficulty": "medium",
                "typical_patterns": [
                    {
                        "pattern": r"(\w+\s*=\s*)?(\w+)\s*\([^)]*\)",
                        "fix_template": "{original}  # type: ignore[no-untyped-call]",
                        "contexts": [
                            "外部ライブラリ関数",
                            "レガシーコード関数",
                            "型注釈なし内部関数"
                        ]
                    }
                ],
                "flash_instruction_template": """
🎯 型無視コメント追加
📝 手順:
1. エラーが出ている関数呼び出し行を見つける
2. 行末に type: ignore コメントを追加
3. コメント形式: # type: ignore[no-untyped-call]

✅ 修正例:
result = legacy_func()
→ result = legacy_func()  # type: ignore[no-untyped-call]

⚠️ 注意: スペースを正確に
""",
                "validation_pattern": r"#\s*type:\s*ignore\[no-untyped-call\]"
            },

            "type-arg": {
                "name": "ジェネリック型引数不足",
                "difficulty": "medium",
                "typical_patterns": [
                    {
                        "pattern": r":\s*(List|Dict|Set|Tuple)(\s*=|\s*\()",
                        "fix_template": ": {generic_type}[{type_args}]",
                        "type_mappings": {
                            "List": ["str", "int", "dict", "Any"],
                            "Dict": ["str, Any", "str, str", "str, int"],
                            "Set": ["str", "int"],
                            "Tuple": ["str, ...", "str, str", "int, str"]
                        }
                    }
                ],
                "flash_instruction_template": """
🎯 ジェネリック型引数追加
📝 手順:
1. List, Dict, Set, Tuple を見つける
2. 角括弧[]で型引数を追加
3. 型引数の選び方:
   - List[str]: 文字列のリスト
   - Dict[str, Any]: 文字列キー、任意の値
   - Set[int]: 整数のセット

✅ 修正例:
items: List = []  → items: List[str] = []
data: Dict = {}   → data: Dict[str, Any] = {}

💡 よく使う型:
- str, int, bool (基本型)
- Any (なんでも)
""",
                "validation_pattern": r"(List|Dict|Set|Tuple)\[[^]]+\]"
            },

            "call-arg": {
                "name": "関数引数型エラー",
                "difficulty": "hard",
                "typical_patterns": [
                    {
                        "pattern": r"(\w+)\s*\([^)]*\)",
                        "fix_approaches": [
                            "型キャスト追加",
                            "条件分岐追加",
                            "デフォルト値設定"
                        ]
                    }
                ],
                "flash_instruction_template": """
🎯 関数引数型修正
📝 手順:
1. エラーメッセージで期待される型を確認
2. 以下のいずれかで修正:
   a) 型キャスト: str(value), int(value)
   b) 条件チェック: if value is not None:
   c) デフォルト値: value or "default"

✅ 修正例:
func(user_id)  → func(str(user_id))
func(config)   → func(config or {})

⚠️ 注意: 元の動作を壊さないように
""",
                "validation_pattern": r"(str|int|bool|float)\s*\("
            },

            "attr-defined": {
                "name": "属性未定義エラー",
                "difficulty": "hard",
                "typical_patterns": [
                    {
                        "pattern": r"(\w+)\.(\w+)",
                        "fix_approaches": [
                            "hasattr チェック追加",
                            "getattr with default",
                            "type: ignore 追加"
                        ]
                    }
                ],
                "flash_instruction_template": """
🎯 属性アクセス修正
📝 手順:
1. 存在しない属性へのアクセスを特定
2. 以下のいずれかで修正:
   a) hasattr チェック: if hasattr(obj, 'attr'):
   b) getattr使用: getattr(obj, 'attr', default)
   c) type: ignore: obj.attr  # type: ignore

✅ 修正例:
obj.missing_attr
→ getattr(obj, 'missing_attr', None)

⚠️ 選択基準:
- 必須の属性 → hasattr
- オプション → getattr
- 確実に存在 → type: ignore
""",
                "validation_pattern": r"(hasattr|getattr|#\s*type:\s*ignore)"
            }
        }

    def get_template(self, error_type: str) -> Dict[str, Any]:
        """エラータイプ別テンプレート取得"""
        return self.error_templates.get(error_type, {})

    def generate_flash_instruction(self, error_type: str, function_name: str,
                                  error_lines: List[str], context: str = "") -> str:
        """Flash 2.5向け具体的修正指示生成"""

        template = self.get_template(error_type)
        if not template:
            return self._generic_instruction(error_type, function_name)

        base_instruction = template.get("flash_instruction_template", "")

        # コンテキスト情報追加
        specific_instruction = f"""
🎯 対象: {function_name}関数
🔧 エラー: {template.get('name', error_type)}
難易度: {template.get('difficulty', 'medium')}

{base_instruction}

📍 修正対象行:
{self._format_error_lines(error_lines)}

{context}
""".strip()

        return specific_instruction

    def generate_step_by_step_plan(self, tasks: List[Dict[str, Any]]) -> str:
        """複数タスクの段階的実行プラン生成"""

        plan = """
🚀 Flash 2.5 段階的修正プラン

📋 実行順序:
"""

        for i, task in enumerate(tasks, 1):
            error_type = task.get("error_type", "unknown")
            template = self.get_template(error_type)
            difficulty = template.get("difficulty", "medium")

            plan += f"""
ステップ {i}: {task.get('target_function', 'unknown')}関数
  - エラー: {template.get('name', error_type)}
  - 難易度: {difficulty}
  - 所要時間: {task.get('estimated_time', 10)}分
  - 修正内容: {template.get('flash_instruction_template', '').split('📝')[0].strip()}
"""

        plan += """

⚠️ Flash 2.5 最適化ルール:
1. 一度に1つの関数のみ修正
2. 修正前にコードをよく読む
3. 例に従って正確に修正
4. 修正後に動作確認
5. エラーが残る場合は type: ignore 使用

🎯 成功の鍵:
- 簡潔で具体的な修正
- 既存コードの最小変更
- 型注釈の正確性
"""

        return plan

    def create_validation_checklist(self, error_type: str) -> List[str]:
        """修正後検証チェックリスト生成"""

        template = self.get_template(error_type)
        validation_pattern = template.get("validation_pattern")

        checklist = [
            "✅ mypy エラーが解消されている",
            "✅ 既存の動作が変更されていない",
            "✅ コードが読みやすい状態を保持",
            "✅ 適切なインポート文が追加されている"
        ]

        if validation_pattern:
            checklist.append(f"✅ 修正パターンが正しい: {validation_pattern}")

        # エラータイプ別の特別チェック
        if error_type == "no-untyped-def":
            checklist.extend([
                "✅ 戻り値型が関数の実際の戻り値と一致",
                "✅ -> の前後にスペースがある"
            ])
        elif error_type == "no-untyped-call":
            checklist.extend([
                "✅ type: ignore コメントが正確",
                "✅ コメントの位置が行末"
            ])
        elif error_type == "type-arg":
            checklist.extend([
                "✅ ジェネリック型引数が適切",
                "✅ 角括弧の記法が正確"
            ])

        return checklist

    def _format_error_lines(self, error_lines: List[str]) -> str:
        """エラー行を見やすく整形"""
        if not error_lines:
            return "（エラー行情報なし）"

        formatted = ""
        for line in error_lines[:5]:  # 最大5行まで
            formatted += f"  {line}\n"

        if len(error_lines) > 5:
            formatted += f"  ... 他{len(error_lines) - 5}行\n"

        return formatted.rstrip()

    def _generic_instruction(self, error_type: str, function_name: str) -> str:
        """汎用修正指示"""
        return f"""
🎯 対象: {function_name}関数
🔧 エラー: {error_type}

📝 基本手順:
1. エラーメッセージを読む
2. 型注釈の追加/修正
3. 必要に応じて import 追加
4. mypy チェックで確認

⚠️ 分からない場合は type: ignore を使用
"""

def main():
    """テスト実行"""
    templates = Flash25Templates()

    # テンプレート表示
    for error_type in ["no-untyped-def", "no-untyped-call", "type-arg"]:
        template = templates.get_template(error_type)
        print(f"\n📋 {error_type}:")
        print(f"  名前: {template.get('name')}")
        print(f"  難易度: {template.get('difficulty')}")

        instruction = templates.generate_flash_instruction(
            error_type, "test_function", ["Line 10: missing return type"]
        )
        print(f"  指示例:\n{instruction[:200]}...")

if __name__ == "__main__":
    main()
