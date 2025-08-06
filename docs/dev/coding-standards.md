# コーディング規約

> Kumihan-Formatter プロジェクト開発規約
> **最終更新**: 2025-08-06 - Issue #807対応：tmp/配下強制出力ルール追加

## 📋 概要

本ドキュメントはKumihan-Formatterプロジェクトの開発における必須のコーディング規約を定義します。全ての開発者・コントリビューターは本規約に厳格に従う必要があります。

## 🚨 ファイル出力管理（絶対遵守）

### tmp/配下強制出力ルール

**【絶対原則】**: 全ての一時出力ファイルは必ず`tmp/`ディレクトリ配下に出力すること

#### 適用対象
- ログファイル（`.log`, `.txt`）
- デバッグ出力（`.debug`, `.trace`）
- 変換結果（`.html`, `.pdf`, `.json`）
- テストファイル（テスト用の一時データ）
- 設定ファイル（一時的な設定ファイル）
- キャッシュファイル（`.cache`, `.tmp`）

#### 実装パターン

##### ✅ 正しい実装例

```python
import os
from pathlib import Path

# パターン1: os.path使用
def save_log_file(content: str, filename: str) -> None:
    """ログファイルをtmp/配下に保存"""
    os.makedirs("tmp", exist_ok=True)
    output_path = os.path.join("tmp", filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

# パターン2: pathlib使用（推奨）
def save_debug_output(data: dict, filename: str) -> None:
    """デバッグデータをtmp/配下に保存"""
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    output_path = tmp_dir / filename
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# パターン3: 設定クラス使用
class OutputManager:
    """出力管理クラス"""
    
    def __init__(self):
        self.tmp_dir = Path("tmp")
        self.tmp_dir.mkdir(exist_ok=True)
    
    def save_file(self, content: str, filename: str) -> Path:
        """ファイルをtmp/配下に保存し、パスを返す"""
        output_path = self.tmp_dir / filename
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)
        return output_path

# パターン4: ロガー設定
import logging

def setup_logger(name: str) -> logging.Logger:
    """tmp/配下にログファイルを出力するロガー設定"""
    os.makedirs("tmp", exist_ok=True)
    
    logger = logging.getLogger(name)
    handler = logging.FileHandler("tmp/application.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger
```

##### ❌ 違反例（絶対禁止）

```python
# 違反1: プロジェクトルート直下への出力
with open("output.log", "w") as f:  # NG
    f.write(content)

# 違反2: 他のディレクトリへの直接出力
with open("logs/debug.txt", "w") as f:  # NG
    f.write(debug_data)

# 違反3: 相対パス使用での直接出力
with open("../output.json", "w") as f:  # NG
    json.dump(data, f)

# 違反4: カレントディレクトリへの出力
os.chdir(".")
with open("result.html", "w") as f:  # NG
    f.write(html_content)
```

#### ディレクトリ構造管理

```python
# tmp/配下のサブディレクトリ使用例
def organize_tmp_files():
    """tmp/配下を整理して使用"""
    base_tmp = Path("tmp")
    
    # 用途別サブディレクトリ
    logs_dir = base_tmp / "logs"
    debug_dir = base_tmp / "debug"
    results_dir = base_tmp / "results"
    
    # ディレクトリ作成
    for dir_path in [logs_dir, debug_dir, results_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return {
        "logs": logs_dir,
        "debug": debug_dir,
        "results": results_dir
    }
```

#### エラーハンドリング

```python
def safe_tmp_output(content: str, filename: str) -> bool:
    """安全なtmp/出力（エラーハンドリング付き）"""
    try:
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        
        output_path = tmp_dir / filename
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"ファイル出力成功: {output_path}")
        return True
        
    except PermissionError:
        logger.error(f"権限エラー: tmp/{filename} への書き込み権限がありません")
        return False
    except OSError as e:
        logger.error(f"ファイルシステムエラー: {e}")
        return False
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return False
```

### 理由・背景

#### 1. プロジェクト整理
- **問題**: ルート直下の散乱ファイルによる可読性低下
- **解決**: tmp/配下集約による明確な構造化

#### 2. バージョン管理
- **問題**: 一時ファイルの誤コミット
- **解決**: .gitignoreでtmp/配下を除外設定

#### 3. CI/CD効率化
- **問題**: 不要ファイルによるビルド時間増加
- **解決**: tmp/配下のみクリーンアップで高速化

#### 4. クロスプラットフォーム対応
- **問題**: OS依存のパス問題
- **解決**: 統一されたtmp/パスでの互換性確保

### 検証・監視

#### 自動検証コマンド

```bash
# 1. tmp/配下出力の検証
find . -name "*.py" -exec grep -l "open(" {} \; | xargs grep -v "tmp/" | grep -E "\.(log|txt|json|xml|html|debug|cache)"

# 2. 違反ファイルの検出
find . -maxdepth 1 -type f \( -name "*.log" -o -name "*.txt" -o -name "*.json" -o -name "*.xml" -o -name "*.html" -o -name "*.debug" -o -name "*.cache" \)

# 3. プロジェクト内tmp/ディレクトリの確認
find . -type d -name "tmp" | head -5

# 4. 最近作成された疑わしいファイル
find . -maxdepth 2 -type f -newer $(find . -name "*.py" | head -1) | grep -v -E "(\.git|\.venv|__pycache__|\.pyc)"
```

#### CI/CD統合

```yaml
# .github/workflows/file-output-check.yml (例)
name: File Output Validation

on: [push, pull_request]

jobs:
  check-tmp-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check tmp/ directory compliance
        run: |
          # 違反ファイル検出
          violation_files=$(find . -maxdepth 1 -type f \( -name "*.log" -o -name "*.txt" -o -name "*.json" -o -name "*.xml" -o -name "*.html" -o -name "*.debug" \))
          
          if [ ! -z "$violation_files" ]; then
            echo "❌ tmp/配下出力ルール違反ファイル検出:"
            echo "$violation_files"
            exit 1
          fi
          
          echo "✅ tmp/配下出力ルール遵守確認"
```

## 🔧 その他のコーディング規約

### Python基本規約
- **バージョン**: Python 3.12以上
- **フォーマッタ**: Black（自動適用）
- **import整理**: isort（自動適用）  
- **型チェック**: mypy strict mode
- **エンコーディング**: UTF-8統一

### ログ管理
```python
# 必須: 統一ロガー使用
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)
```

### エラーハンドリング
```python
# 推奨: 具体的な例外処理
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"具体的エラー処理: {e}")
    raise
except Exception as e:
    logger.error(f"予期しないエラー: {e}")
    raise
```

---
*✨ Generated by Claude Code for Kumihan-Formatter (Development)*