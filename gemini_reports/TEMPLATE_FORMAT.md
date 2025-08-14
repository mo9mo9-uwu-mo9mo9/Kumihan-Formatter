# Gemini協業指示書 - Black/isort フォーマット修正テンプレート

## 作業概要
- **作業種別**: Black/isort コードフォーマット統一
- **対象**: `kumihan_formatter/` パッケージ全体
- **自動化レベル**: FULL_AUTO
- **推定Token削減**: 95-99%

## 🎯 フォーマット対象パターン

### 1. Black - コードフォーマット統一
```python
# ❌ 修正前（フォーマット不統一）
def function(a,b,c):
    if(condition1 and condition2):
        result={'key1':value1,'key2':value2}
        return result

# ✅ 修正後（Black適用）
def function(a, b, c):
    if condition1 and condition2:
        result = {"key1": value1, "key2": value2}
        return result
```

### 2. isort - インポート順序統一
```python
# ❌ 修正前（インポート順序バラバラ）
from pathlib import Path
import sys
import os
from typing import Any, Dict
from kumihan_formatter.core import Parser

# ✅ 修正後（isort適用）
import os
import sys
from pathlib import Path
from typing import Any, Dict

from kumihan_formatter.core import Parser
```

### 3. 行長・インデント統一
```python
# ❌ 修正前（不統一インデント）
class Example:
  def method(self):
      if condition:
        return True

# ✅ 修正後（4スペース統一）  
class Example:
    def method(self):
        if condition:
            return True
```

## 📋 実行手順

### Step 1: 現状確認
```bash
cd /path/to/Kumihan-Formatter

# Black チェック（変更必要箇所確認）
python3 -m black --check --diff kumihan_formatter

# isort チェック（インポート順序確認）
python3 -m isort --check-only --diff kumihan_formatter
```

### Step 2: バックアップ作成（安全対策）
```bash
# 重要ファイルのバックアップ
cp -r kumihan_formatter kumihan_formatter_backup_$(date +%Y%m%d_%H%M%S)
```

### Step 3: Black フォーマット実行
```bash
# 段階的実行（推奨）
python3 -m black kumihan_formatter/core/
python3 -m black kumihan_formatter/config/  
python3 -m black kumihan_formatter/cli.py
# または全体一括
python3 -m black kumihan_formatter
```

### Step 4: isort インポート整理実行
```bash
# 段階的実行（推奨）
python3 -m isort kumihan_formatter/core/
python3 -m isort kumihan_formatter/config/
python3 -m isort kumihan_formatter/cli.py
# または全体一括
python3 -m isort kumihan_formatter
```

### Step 5: フォーマット後検証
```bash
# 構文チェック（Layer 1）
python3 -c "
import ast, os
for root, dirs, files in os.walk('kumihan_formatter'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath) as f:
                ast.parse(f.read())
print('構文チェック完了')
"

# フォーマット確認（Layer 2）
python3 -m black --check kumihan_formatter
python3 -m isort --check-only kumihan_formatter
```

## 🛡️ 品質保証チェックリスト

### 必須確認項目
- [ ] Black完全通過（"would be left unchanged"）
- [ ] isort完全通過（"SUCCESS"メッセージ）
- [ ] 全.pyファイルの構文正常性
- [ ] インデント・スペース統一性確認
- [ ] 文字列・コメント内容の保持

### フォーマット変更の影響確認
- [ ] 文字列リテラル内容の非変更
- [ ] コメント配置の適切性
- [ ] 複数行文字列の保持
- [ ] docstring フォーマット保持
- [ ] f-string 構文の正常性

### 実行前後差分確認
```bash
# 差分確認（重要箇所のみ）
git diff --name-only  # 変更ファイル一覧
git diff --stat       # 変更統計
git diff kumihan_formatter/cli.py  # 重要ファイル詳細確認
```

## 📊 報告書フォーマット

### フォーマット修正完了報告
```markdown
## Black/isort フォーマット修正完了報告

### 処理結果サマリー
- **処理対象ファイル数**: X件
- **Black変更ファイル数**: Y件
- **isort変更ファイル数**: Z件  
- **処理時間**: N秒

### 変更内容詳細
#### Black変更箇所
1. **kumihan_formatter/cli.py**
   - インデント統一: タブ→4スペース
   - 辞書・リストのスペース調整
   - 長い行の適切な改行

2. **kumihan_formatter/core/rendering/main_renderer.py**
   - 文字列クォート統一: ' → "
   - 演算子周りのスペース調整
   - 関数定義の改行統一

#### isort変更箇所  
1. **kumihan_formatter/parser.py**
   - 標準ライブラリ → サードパーティ → ローカルの順序統一
   - import/from import のグループ分け
   
2. **kumihan_formatter/core/block_parser/content_parser.py**
   - 未使用インポートの自動削除
   - TYPE_CHECKING インポートの適切な配置

### 品質検証結果
✅ python3 -m black --check kumihan_formatter
   All done! ✨ 🍰 ✨
   X files would be left unchanged.

✅ python3 -m isort --check-only kumihan_formatter  
   SUCCESS

✅ 構文チェック完了
   X ファイル全て正常

### 差分統計
- **追加行数**: +A行
- **削除行数**: -B行  
- **実質変更**: C行（主にフォーマット調整）

### Claude確認依頼項目
- [ ] 重要ファイルの変更妥当性確認
- [ ] フォーマット変更による可読性向上確認
- [ ] 予期しない機能影響の有無確認
- [ ] コミット準備完了確認
```

## 🎨 フォーマット設定確認

### pyproject.toml 設定値
```toml
[tool.black]
line-length = 88
target-version = ['py312']
include = '\.pyi?$'

[tool.isort]  
profile = "black"
multi_line_output = 3
line_length = 88
```

### エディタ設定の統一性
- VSCode: `.vscode/settings.json`
- 他エディタ: フォーマッタ設定との整合性

## ⚠️ 緊急時対応・ロールバック

### フォーマット失敗時
1. **即座作業停止**
2. **バックアップから復元**
   ```bash
   rm -rf kumihan_formatter
   cp -r kumihan_formatter_backup_XXXXXX kumihan_formatter
   ```
3. **Claude報告・原因調査依頼**

### 品質問題発生時
```bash
# Git使用時の緊急復元
git checkout -- kumihan_formatter/  # 作業前状態に復元
git clean -fd                       # 追加ファイル削除
```

### フェイルセーフ基準
- 構文エラー → 即座停止・復元
- 重要機能のロジック変更検出 → 手動確認待ち
- 既存テスト失敗 → 原因調査・Claude引き継ぎ

---
*テンプレート生成日: 2025-08-14*  
*Issue #876反省改善 - フォーマット作業効率化*