# CLAUDE_EXAMPLES.md

> Kumihan-Formatter – Claude Code コード例集
> **目的**: 構造化ログやデバッグ機能の具体的な使用例
> **バージョン**: 1.0.0 (2025-01-15)

## 構造化ログ機能 (Issue#472)

### 基本的な構造化ログ
```python
from kumihan_formatter.core.utilities.logger import get_structured_logger

logger = get_structured_logger(__name__)

# 基本的な情報ログ
logger.info("ファイル処理開始", file_path="input.txt", size_bytes=1024)

# エラー時の推奨アクション付きログ
logger.error_with_suggestion(
    "ファイルが見つかりません",
    "ファイルパスと権限を確認してください",
    error_type="FileNotFoundError",
    file_path="missing.txt"
)

# ファイル操作ログ
logger.file_operation("read", "/path/to/file.txt", success=True, size_bytes=2048)

# パフォーマンス測定ログ
logger.performance("file_conversion", 0.125, lines=500)

# 状態変更ログ
logger.state_change("config updated", old_value="debug", new_value="info")
```

### 自動パフォーマンス測定デコレータ
```python
from kumihan_formatter.core.utilities.logger import log_performance_decorator

# 基本的なパフォーマンス測定
@log_performance_decorator(operation="file_conversion")
def convert_file(input_path: str) -> str:
    # ファイル変換処理
    return output_path

# メモリ使用量も測定
@log_performance_decorator(include_memory=True)
def heavy_processing(data: list) -> dict:
    # 重い処理
    return result

# スタックトレースも記録
@log_performance_decorator(include_stack=True)
def debug_function(param: str) -> None:
    # デバッグ対象の処理
    pass
```

### デバッグ用ユーティリティ
```python
from kumihan_formatter.core.utilities.logger import (
    call_chain_tracker,
    memory_usage_tracker
)

# 現在のコール チェーンを取得
call_info = call_chain_tracker(max_depth=5)
logger.debug("Call chain", **call_info)

# メモリ使用量を取得
memory_info = memory_usage_tracker()
logger.info("Memory usage", **memory_info)
```

### 機密情報の自動フィルタリング（パフォーマンス最適化済み）
```python
# 機密情報は自動的に [FILTERED] に置換される
logger.info("User login", username="user123", password="secret")
# 出力: {"username": "user123", "password": "[FILTERED]"}
```

### 構造化ログの特徴
- **JSON形式**: 機械解析可能な構造化データ
- **コンテキスト情報**: 豊富なメタデータ付きログ
- **機密情報フィルタリング**: パスワード・トークンなどの自動除去
- **パフォーマンス最適化**: キーキャッシュによる高速化
- **Claude Code最適化**: 自動解析・デバッグ支援

**JSON出力例**:
```json
{
    "timestamp": "2025-01-15T15:30:00",
    "level": "INFO",
    "module": "convert_processor",
    "message": "File converted",
    "context": {
        "file_path": "input.txt",
        "output_size": 2048,
        "duration_ms": 150
    }
}
```

## 開発ログ機能 (Issue#446)

Claude Code向けの開発ログ機能：

```bash
# 開発ログの有効化
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# ログファイルの確認
ls /tmp/kumihan_formatter/
cat /tmp/kumihan_formatter/dev_log_*.log
```

### 開発ログの特徴
- **出力先**: `/tmp/kumihan_formatter/`
- **有効化**: `KUMIHAN_DEV_LOG=true`環境変数
- **ファイル名**: `dev_log_<セッションID>.log`
- **自動クリーンアップ**: 24時間経過後に削除
- **サイズ制限**: 5MB（超過時は自動ローテーション）
- **本番環境**: 環境変数未設定時は無効
