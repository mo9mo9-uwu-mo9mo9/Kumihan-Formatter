#!/usr/bin/env python3
"""
構文検証器 - Gemini出力の構文エラー防止機構
Phase 1.1 品質向上対応
"""

import ast
import re
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class SyntaxValidator:
    """Gemini出力の構文検証・修正システム"""
    
    def __init__(self):
        self.common_syntax_errors = {
            # 型注釈の間違いパターン
            r'def\s+(\w+)\s*\([^)]*\s*->\s*None\s*:\s*([^)]+)\s*\)\s*->': 
                r'def \1(\2) -> None:',
            
            r'def\s+(\w+)\s*\([^)]*(\w+)\s*->\s*None\s*:\s*([^)]+)\s*\)\s*->':
                r'def \1(\2: \3) -> None:',
                
            # 引数型注釈の間違い
            r'(\w+)\s*->\s*None\s*:\s*([^,)]+)':
                r'\1: \2',
                
            # その他の典型的エラー
            r':\s*->\s*([^:]+):\s*':
                r': \1 -> ',
        }
        
    def validate_python_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Python構文の基本検証"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"構文エラー (行{e.lineno}): {e.msg}"
        except Exception as e:
            return False, f"解析エラー: {str(e)}"
    
    def validate_type_annotations(self, code: str) -> Tuple[bool, List[str]]:
        """型注釈の正当性検証"""
        errors = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 間違った型注釈パターンをチェック
            for pattern, correct in self.common_syntax_errors.items():
                if re.search(pattern, line):
                    errors.append(f"行{i}: 型注釈構文エラー - {line.strip()}")
                    
            # def文の基本チェック
            if 'def ' in line and '->' in line:
                # -> の位置チェック
                if re.search(r'def\s+\w+\s*\([^)]*->', line) and not re.search(r'def\s+\w+\s*\([^)]*\)\s*->', line):
                    errors.append(f"行{i}: -> の位置が不正 - {line.strip()}")
                    
        return len(errors) == 0, errors
    
    def auto_fix_syntax_errors(self, code: str) -> str:
        """構文エラーの自動修正"""
        fixed_code = code
        
        for pattern, replacement in self.common_syntax_errors.items():
            fixed_code = re.sub(pattern, replacement, fixed_code)
            
        # 追加の修正ルール
        fixed_code = self._fix_common_typing_errors(fixed_code)
        
        return fixed_code
    
    def _fix_common_typing_errors(self, code: str) -> str:
        """よくある型注釈エラーの修正"""
        
        # パターン1: def __init__(self, param -> None: Type = None) -> None:
        # 正解: def __init__(self, param: Type = None) -> None:
        pattern1 = r'def\s+(\w+)\s*\(\s*([^,)]*)\s*,\s*([^,)]*)\s*->\s*None\s*:\s*([^,)]*)\s*(.*?)\)\s*->'
        replacement1 = r'def \1(\2, \3: \4\5) ->'
        code = re.sub(pattern1, replacement1, code)
        
        # パターン2: 引数リスト内の -> None: を削除
        pattern2 = r'(\w+)\s*->\s*None\s*:\s*([^,)]+)'
        replacement2 = r'\1: \2'
        code = re.sub(pattern2, replacement2, code)
        
        return code
    
    def validate_mypy_compatibility(self, file_path: str) -> Tuple[bool, List[str]]:
        """mypy strict mode互換性チェック"""
        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            errors = []
            for line in result.stdout.split('\n'):
                if 'error:' in line:
                    errors.append(line.strip())
                    
            return len(errors) == 0, errors
            
        except subprocess.TimeoutExpired:
            return False, ["mypy検証タイムアウト"]
        except Exception as e:
            return False, [f"mypy検証エラー: {str(e)}"]
    
    def comprehensive_validation(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """包括的検証"""
        
        validation_result = {
            "syntax_valid": False,
            "type_annotations_valid": False,
            "mypy_compatible": False,
            "syntax_errors": [],
            "type_errors": [],
            "mypy_errors": [],
            "fixed_code": None,
            "validation_score": 0.0
        }
        
        # 1. 基本構文検証
        syntax_ok, syntax_error = self.validate_python_syntax(code)
        validation_result["syntax_valid"] = syntax_ok
        if syntax_error:
            validation_result["syntax_errors"].append(syntax_error)
        
        # 2. 型注釈検証
        type_ok, type_errors = self.validate_type_annotations(code)
        validation_result["type_annotations_valid"] = type_ok
        validation_result["type_errors"] = type_errors
        
        # 3. 自動修正試行
        if not syntax_ok or not type_ok:
            fixed_code = self.auto_fix_syntax_errors(code)
            validation_result["fixed_code"] = fixed_code
            
            # 修正後の再検証
            fixed_syntax_ok, _ = self.validate_python_syntax(fixed_code)
            fixed_type_ok, _ = self.validate_type_annotations(fixed_code)
            
            if fixed_syntax_ok and fixed_type_ok:
                validation_result["syntax_valid"] = True
                validation_result["type_annotations_valid"] = True
                code = fixed_code  # 修正されたコードを使用
        
        # 4. mypy検証（ファイルパスがある場合）
        if file_path:
            # 一時的にコードをファイルに書き出して検証
            temp_file = Path(file_path).with_suffix('.tmp.py')
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                mypy_ok, mypy_errors = self.validate_mypy_compatibility(str(temp_file))
                validation_result["mypy_compatible"] = mypy_ok
                validation_result["mypy_errors"] = mypy_errors
                
            finally:
                if temp_file.exists():
                    temp_file.unlink()
        
        # 5. 総合スコア計算
        score = 0.0
        if validation_result["syntax_valid"]:
            score += 0.4
        if validation_result["type_annotations_valid"]:
            score += 0.3
        if validation_result["mypy_compatible"]:
            score += 0.3
            
        validation_result["validation_score"] = score
        
        return validation_result


class TypeAnnotationTemplate:
    """型注釈テンプレート・パターン集"""
    
    def __init__(self):
        self.correct_patterns = {
            # 基本パターン
            "function_no_args": "def function() -> ReturnType:",
            "function_with_args": "def function(arg1: Type1, arg2: Type2) -> ReturnType:",
            "function_with_defaults": "def function(arg: Type = default_value) -> ReturnType:",
            "function_with_varargs": "def function(*args: Any, **kwargs: Any) -> ReturnType:",
            
            # よく使われる型
            "any_type": "from typing import Any\ndef function(param: Any) -> Any:",
            "optional_type": "from typing import Optional\ndef function(param: Optional[Type]) -> None:",
            "callable_type": "from typing import Callable\ndef function(callback: Callable[..., Any]) -> None:",
            "context_manager": "def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:",
        }
        
        self.prohibited_patterns = [
            # 絶対に使ってはいけないパターン
            "def function(param -> None: Type):",
            "def function(param -> Type: None):",
            "def function(param: -> Type):",
            "def function(param, -> Type):",
        ]
        
    def get_correction_example(self, error_type: str) -> str:
        """エラータイプに応じた修正例を提供"""
        
        examples = {
            "no-untyped-def": """
✅ 正しい例:
def function(param: Any) -> Any:
    pass

def __init__(self, param: Type) -> None:
    pass

❌ 間違い例:
def function(param -> None: Type):  # 絶対禁止
def function(param):  # 型注釈なし
""",
            
            "method_typing": """
✅ 正しい例:
def method(self, param: Any) -> Any:
    pass

class MyClass:
    def __init__(self, param: Any) -> None:
        pass
""",
        }
        
        return examples.get(error_type, examples["no-untyped-def"])


def main():
    """テスト実行"""
    validator = SyntaxValidator()
    
    # テストケース
    test_codes = [
        # 正常なコード
        "def function(param: Any) -> None:\n    pass",
        
        # エラーのあるコード
        "def function(param -> None: Any = None) -> None:\n    pass",
        
        # 複雑なエラー
        "def __init__(self, validator -> None: Any, processor: Any) -> None:\n    pass",
    ]
    
    for i, code in enumerate(test_codes, 1):
        print(f"\n=== テストケース {i} ===")
        print(f"入力コード:\n{code}")
        
        result = validator.comprehensive_validation(code)
        
        print(f"検証結果:")
        print(f"  構文OK: {result['syntax_valid']}")
        print(f"  型注釈OK: {result['type_annotations_valid']}")
        print(f"  スコア: {result['validation_score']:.2f}")
        
        if result['fixed_code']:
            print(f"修正後コード:\n{result['fixed_code']}")
        
        if result['syntax_errors']:
            print(f"構文エラー: {result['syntax_errors']}")
        if result['type_errors']:
            print(f"型エラー: {result['type_errors']}")


if __name__ == "__main__":
    main()