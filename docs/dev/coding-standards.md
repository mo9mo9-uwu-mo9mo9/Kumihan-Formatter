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

## 🎓 新規開発者向けガイド

### セットアップチェックリスト

#### 1. 開発環境準備
```bash
# Python バージョン確認
python3 --version  # 3.12以上必須

# 仮想環境作成・アクティベート
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -e .[dev]
```

#### 2. 品質ツール確認
```bash
# フォーマッタ・リンタのインストール確認
black --version
mypy --version
pytest --version

# 初回品質チェック実行
make lint      # Black + mypy実行
make test      # pytest実行
```

#### 3. tmp/ディレクトリ確認
```bash
# tmp/ディレクトリの存在確認
ls -la tmp/

# 存在しない場合は作成
mkdir -p tmp
```

### 開発の基本ワークフロー

#### 1. 新機能・修正の開始
```bash
# イシューベースでブランチ作成
git checkout -b feat/issue-123-description

# または
git checkout -b fix/issue-456-bugfix
```

#### 2. コード変更
```python
# 必須: ログ使用パターン
from kumihan_formatter.core.utilities.logger import get_logger

class NewFeature:
    def __init__(self):
        self.logger = get_logger(__name__)  # 必須
    
    def process_data(self, data: str) -> str:
        """新機能の実装例"""
        self.logger.info("処理開始")
        
        # tmp/配下への出力例
        from pathlib import Path
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        
        debug_file = tmp_dir / "debug_output.json"
        with debug_file.open("w") as f:
            # デバッグ情報の出力
            pass
        
        self.logger.info("処理完了")
        return processed_data
```

#### 3. 品質チェック
```bash
# 必須: 変更前に品質チェック
make lint      # コードフォーマット + 型チェック
make test      # テスト実行

# エラーがある場合は修正後に再実行
```

#### 4. コミット・プッシュ
```bash
# 変更をコミット
git add .
git commit -m "feat: 新機能実装 - Issue #123"

# プッシュ
git push origin feat/issue-123-description
```

### よくある間違いと対策

#### 1. ファイル出力エラー
```python
# ❌ 間違い: ルート直下に出力
with open("output.log", "w") as f:
    f.write(log_content)

# ✅ 正解: tmp/配下に出力
from pathlib import Path
tmp_dir = Path("tmp")
tmp_dir.mkdir(exist_ok=True)
with (tmp_dir / "output.log").open("w") as f:
    f.write(log_content)
```

#### 2. ログ使用エラー
```python
# ❌ 間違い: 標準printの使用
print("デバッグ情報")

# ✅ 正解: 統一ロガーの使用
from kumihan_formatter.core.utilities.logger import get_logger
logger = get_logger(__name__)
logger.debug("デバッグ情報")
```

#### 3. 型注釈の漏れ
```python
# ❌ 間違い: 型注釈なし
def process_text(text):
    return text.upper()

# ✅ 正解: 完全な型注釈
def process_text(text: str) -> str:
    return text.upper()
```

### コードレビュー観点

#### 1. 必須チェック項目
- [ ] tmp/配下への出力遵守
- [ ] 統一ロガーの使用
- [ ] 型注釈の完備
- [ ] テストの追加・更新
- [ ] ドキュメントの更新

#### 2. 品質チェック
- [ ] `make lint` 成功
- [ ] `make test` 成功
- [ ] 新機能のテストカバレッジ追加

#### 3. セキュリティチェック
- [ ] 秘密情報のログ出力なし
- [ ] 外部入力の適切な検証
- [ ] パス操作の安全性確保

### デバッグ・トラブルシューティング

#### 1. よくあるエラーと解決法

**エラー: ModuleNotFoundError**
```bash
# 原因: 依存関係の不足
# 解決: 再インストール
pip install -e .[dev]
```

**エラー: mypy型チェック失敗**
```bash
# 原因: 型注釈の不足・誤り
# 解決: 型注釈の追加・修正
mypy kumihan_formatter/  # 詳細エラー確認
```

**エラー: テスト失敗**
```bash
# 原因: 既存テストとの衝突
# 解決: テストの更新
pytest -v  # 詳細な失敗情報確認
```

#### 2. デバッグ用出力
```python
# デバッグ情報をtmp/配下に出力
import json
from pathlib import Path

def debug_output(data: dict, tag: str = "debug"):
    """デバッグ用データ出力"""
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    debug_file = tmp_dir / f"{tag}_output.json"
    with debug_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"デバッグ出力: {debug_file}")
```

### パフォーマンス最適化

#### 1. 大容量データ処理
```python
# ストリーミング処理の活用
def process_large_file(file_path: Path) -> Iterator[str]:
    """大容量ファイルのストリーミング処理"""
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            yield process_line(line)
```

#### 2. メモリ管理
```python
# 明示的なリソース解放
import gc

def memory_intensive_task():
    """メモリ集約的タスク"""
    try:
        # 重い処理
        process_data()
    finally:
        # 明示的なガベージコレクション
        gc.collect()
```

### コントリビューション準備

#### 1. プルリクエスト作成前
```bash
# 必須チェック実行
make lint && make test

# コミットメッセージの確認
git log --oneline -5
```

#### 2. ドキュメント更新
- 新機能: APIドキュメントの追加
- 修正: 変更点の記録
- 重要な変更: アーキテクチャドキュメントの更新

---
*📚 新規開発者向けガイド追加 - Issue #1147対応*
*✨ Generated by Claude Code for Kumihan-Formatter (Development)*