# Gemini協業指示書 - Flake8/Lint修正テンプレート

## 作業概要
- **作業種別**: Flake8/Lint エラー修正
- **対象**: `kumihan_formatter/` パッケージ全体
- **自動化レベル**: FULL_AUTO / SEMI_AUTO
- **推定Token削減**: 90-95%

## 🎯 修正対象エラーパターン

### 1. F401 - 未使用インポート
```python
# ❌ 修正前
import os  # 未使用
import sys
from typing import Dict, List, Union  # Union未使用

def main():
    print(sys.version)

# ✅ 修正後
import sys
from typing import Dict, List

def main():
    print(sys.version)
```

### 2. E501 - 長い行（88文字超過）
```python
# ❌ 修正前
very_long_function_call(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10)

# ✅ 修正後
very_long_function_call(
    arg1, arg2, arg3, arg4, arg5,
    arg6, arg7, arg8, arg9, arg10
)
```

### 3. E302/E305 - 空行スタイル
```python
# ❌ 修正前
def function1():
    pass
def function2():
    pass

# ✅ 修正後  
def function1():
    pass


def function2():
    pass
```

### 4. W291/W293 - 末尾空白・空行空白
```python
# ❌ 修正前（空白文字あり）
def function():　　
    pass　

# ✅ 修正後（空白文字なし）
def function():
    pass
```

### 5. C901 - 関数複雑度
```python
# ❌ 修正前（複雑度高）
def complex_function(data):
    if condition1:
        if condition2:
            if condition3:
                # 深いネスト...
                
# ✅ 修正後（関数分割）
def _handle_condition1(data):
    # 処理1
    
def _handle_condition2(data):  
    # 処理2
    
def complex_function(data):
    if condition1:
        return _handle_condition1(data)
    # 簡潔に
```

## 📋 実行手順

### Step 1: 現状確認・エラー取得
```bash
cd /path/to/Kumihan-Formatter
python3 -m flake8 kumihan_formatter > flake8_errors.txt
cat flake8_errors.txt
```

### Step 2: エラー分類・修正計画
```python
# エラー種別カウント
grep -c "F401" flake8_errors.txt  # 未使用インポート
grep -c "E501" flake8_errors.txt  # 長い行
grep -c "C901" flake8_errors.txt  # 複雑度
```

### Step 3: 自動修正可能エラーの処理
```bash
# 自動修正ツール使用（可能な場合）
autopep8 --in-place --aggressive --aggressive kumihan_formatter/*.py

# Black適用（フォーマット統一）
python3 -m black kumihan_formatter

# isort適用（インポート順序）
python3 -m isort kumihan_formatter
```

### Step 4: 手動修正（自動修正不可）
- C901 関数複雑度 → 関数分割・ロジック簡潔化
- F401 特定パターン → 適切なインポート削除
- カスタムエラー → 個別対応

### Step 5: 修正後検証
```bash
# 構文チェック（Layer 1）
python3 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['修正ファイル1', '修正ファイル2']]"

# Lint最終チェック（Layer 2）
python3 -m flake8 kumihan_formatter
echo "Exit Code: $?"  # 0なら成功
```

## 🛡️ 品質保証チェックリスト

### 必須確認項目
- [ ] Flake8完全通過（exit code 0）
- [ ] 構文エラー発生なし
- [ ] インポート・依存関係正常
- [ ] 既存テスト通過確認
- [ ] 機能動作の正常性

### 自動修正後の注意点
- [ ] Black/autopep8後の意図しない変更確認
- [ ] インポート削除による欠落チェック
- [ ] 長い行分割での可読性確認
- [ ] 関数分割での機能保持確認

## 📊 報告書フォーマット

### Lint修正完了報告
```markdown
## Flake8/Lint修正完了報告

### 修正結果サマリー
- **修正前エラー数**: X件 (F401: Y件, E501: Z件, C901: W件)
- **修正後エラー数**: 0件
- **修正ファイル数**: N件
- **自動修正率**: M%

### エラー種別別修正内容
1. **F401 (未使用インポート)**: Y件
   - cli.py: `import os` 削除
   - parser.py: `from typing import Union` 削除
   
2. **E501 (長い行)**: Z件
   - main_renderer.py: 関数呼び出し分割 (3箇所)
   - config_models.py: 設定辞書定義分割 (2箇所)
   
3. **C901 (複雑度)**: W件
   - cli.py: `interactive_repl`関数分割

### 品質検証結果
✅ python3 -m flake8 kumihan_formatter
   exit code: 0 (完全通過)
   
✅ python3 -m black --check kumihan_formatter
   All files would be left unchanged
   
✅ python3 -m isort --check-only kumihan_formatter
   SUCCESS
   
### 注意・課題
- 長い行分割で一部可読性が変化（要レビュー）
- 関数分割により新たなprivateメソッド追加

### Claude確認依頼項目
- [ ] 関数分割の妥当性確認
- [ ] 可読性への影響評価
- [ ] パフォーマンス影響チェック
```

## ⚠️ 緊急時対応・フェイルセーフ

### 自動修正失敗時
1. **元ファイル即座復元**（バックアップから）
2. **エラー詳細ログ保存**
3. **Claude引き継ぎ依頼**
4. **手動修正モード切替**

### 修正品質低下時
- 自動修正 → 手動修正切替
- 複雑度高い箇所 → Claude専任依頼
- 重要機能影響 → 段階的修正・検証強化

### フェイルセーフ基準
```python
FAILSAFE_TRIGGERS = [
    "構文エラー発生",
    "テスト失敗(既存)",
    "インポートエラー",
    "予期しない機能変更"
]
```

---
*テンプレート生成日: 2025-08-14*  
*Issue #876反省改善 - Lint修正効率化*