#!/usr/bin/env python3
"""
強化版Flash 2.5テンプレート - 品質向上対応
構文エラー防止・指示精度向上
"""

from typing import Dict, Any, List


class EnhancedFlash25Templates:
    """品質向上版Flash 2.5テンプレート"""
    
    def __init__(self):
        self.enhanced_templates = {
            "no-untyped-def": {
                "name": "型注釈未定義エラー修正",
                "difficulty": "medium",
                "flash_instruction_template": self._get_no_untyped_def_template(),
                "prohibited_patterns": [
                    "def function(param -> None: Type):",
                    "def function(param -> Type: None):",
                    "param -> None:",
                    ") -> None: Type",
                ],
                "correct_examples": [
                    "def function(param: Any) -> None:",
                    "def __init__(self, param: Any) -> None:",
                    "def method(self, param: Any) -> Any:",
                ],
                "quality_checks": [
                    "構文検証必須",
                    "mypy --strict 通過確認",
                    "import文確認"
                ]
            }
        }
    
    def _get_no_untyped_def_template(self) -> str:
        """no-untyped-def用の詳細テンプレート"""
        return """
🚀 Flash 2.5 品質保証付き指示: no-untyped-def エラー修正

⚠️ 【重要】構文エラー防止ルール:
❌ 絶対禁止パターン:
   def function(param -> None: Type):    # これは構文エラー！
   def function(param -> Type: None):    # これも構文エラー！
   def __init__(self, param -> None: Any): # 完全に間違い！

✅ 正しい修正パターン:
   def function(param: Any) -> None:     # 正しい！
   def __init__(self, param: Any) -> None: # 正しい！
   def method(self, param: Any) -> Any:   # 正しい！

📋 修正手順:
1. 関数定義を特定
2. 欠けている引数の型注釈を追加: `param: Any`
3. 欠けている返り値型注釈を追加: `-> None` または `-> Any`
4. import文の確認: `from typing import Any` を追加

🎯 具体的修正例:

修正前:
```python
def __init__(self, validator):
    pass

def process_data(self, data, options):
    return result
```

修正後:
```python
from typing import Any

def __init__(self, validator: Any) -> None:
    pass

def process_data(self, data: Any, options: Any) -> Any:
    return result
```

⚡ Flash 2.5 実行ルール:
1. 関数を1つずつ順番に修正
2. 各修正後、構文チェックを実行
3. エラーが出た場合は即座に修正
4. 分からない場合は必ず `Any` 型を使用

🔍 品質チェック項目:
□ Python構文が正常
□ 型注釈の位置が正しい (引数: `param: Type`, 返り値: `-> Type`)
□ 必要なimport文が追加されている
□ mypy --strict でエラーが出ない

❗ 注意事項:
- `->` は必ず `)` の後に配置
- 引数の型注釈は `:` を使用
- 返り値の型注釈は `->` を使用
- わからない型は必ず `Any` を使用
"""

    def get_enhanced_template(self, error_type: str) -> Dict[str, Any]:
        """強化版テンプレート取得"""
        return self.enhanced_templates.get(error_type, self._get_default_template())
    
    def _get_default_template(self) -> Dict[str, Any]:
        """デフォルトテンプレート"""
        return {
            "name": "一般的なエラー修正",
            "difficulty": "medium", 
            "flash_instruction_template": "適切な修正を実行してください。",
            "prohibited_patterns": [],
            "correct_examples": [],
            "quality_checks": ["基本的な構文チェック"]
        }
    
    def generate_quality_assured_instruction(self, error_type: str, 
                                           tasks: List[Dict], 
                                           file_path: str) -> str:
        """品質保証付き指示生成"""
        
        template = self.get_enhanced_template(error_type)
        base_instruction = template["flash_instruction_template"]
        
        # 品質保証要素を追加
        quality_instruction = f"""
{base_instruction}

📦 今回の修正対象:
ファイル: {file_path}
修正箇所: {len(tasks)}件

📋 修正対象関数リスト:
"""
        
        for i, task in enumerate(tasks, 1):
            func_name = task.get('target_function', 'unknown')
            error_count = task.get('error_count', 0)
            quality_instruction += f"{i}. {func_name} ({error_count}エラー)\n"
        
        quality_instruction += f"""

🔒 品質保証プロセス:
1. 各関数修正後に構文チェック実行
2. エラーが出た場合は以下パターンをチェック:
   ❌ `param -> None:` → ✅ `param: Any`
   ❌ `def func(param -> None: Type):` → ✅ `def func(param: Type) -> None:`
3. 修正完了後、全体構文チェック実行
4. 問題がある場合は段階的に修正

⚠️ 禁止パターン再確認:
"""
        
        for pattern in template["prohibited_patterns"]:
            quality_instruction += f"❌ {pattern}\n"
            
        quality_instruction += f"""

✅ 正解パターン:
"""
        
        for example in template["correct_examples"]:
            quality_instruction += f"✅ {example}\n"
        
        quality_instruction += """

🎯 成功基準:
- 全ての関数に適切な型注釈が追加される
- Python構文エラーが0件
- 必要なimport文が追加される
- mypy strict mode でエラーが出ない

📝 実行方法:
1. 上記リストの関数を1つずつ修正
2. 各修正後に構文確認
3. 全修正完了後に品質チェック実行
4. エラーがあれば即座に修正
"""
        
        return quality_instruction
    
    def get_error_prevention_guide(self, error_type: str) -> str:
        """エラー防止ガイド取得"""
        
        guides = {
            "no-untyped-def": """
🛡️ no-untyped-def エラー防止ガイド

❌ よくある間違い:
1. def function(param -> None: Type):  # -> を間違った場所に
2. def function(param: -> Type):       # : の後に -> を配置
3. def function(param -> Type:):       # 型注釈の順序が逆

✅ 正しいパターン:
1. def function(param: Type) -> ReturnType:
2. def function(param: Any) -> None:
3. def __init__(self, param: Any) -> None:

🔧 修正テクニック:
- 引数: 名前の後に `: 型名`
- 返り値: 引数リストの `)` の後に `-> 型名:`
- 不明な型は `Any` を使用
- 必要に応じて `from typing import Any` を追加

📝 チェックリスト:
□ 全ての関数に返り値型注釈がある
□ 全ての引数に型注釈がある  
□ 構文エラーがない
□ import文が正しい
"""
        }
        
        return guides.get(error_type, "一般的なエラー防止ガイドがありません")


def main():
    """テスト実行"""
    templates = EnhancedFlash25Templates()
    
    # テストタスク
    test_tasks = [
        {"target_function": "__init__", "error_count": 1},
        {"target_function": "process_data", "error_count": 2},
        {"target_function": "validate", "error_count": 1},
    ]
    
    # 品質保証付き指示生成テスト
    instruction = templates.generate_quality_assured_instruction(
        "no-untyped-def", test_tasks, "test_file.py"
    )
    
    print("=== 生成された品質保証付き指示 ===")
    print(instruction)
    
    print("\n=== エラー防止ガイド ===")
    guide = templates.get_error_prevention_guide("no-untyped-def")
    print(guide)


if __name__ == "__main__":
    main()