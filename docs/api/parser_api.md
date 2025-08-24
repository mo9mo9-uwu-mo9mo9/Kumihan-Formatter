# Parser API リファレンス

> Kumihan-Formatter パーサーAPIの完全ガイド

## 概要

パーサーAPIは、Kumihanテキスト記法を解析してAST（抽象構文木）ノードに変換する機能を提供します。

## メインクラス: Parser

### クラス概要

```python
from kumihan_formatter.parser import Parser

# 基本的な使用方法
parser = Parser()
nodes = parser.parse(text)
```

### 初期化

```python
def __init__(
    self,
    config: Any = None,
    graceful_errors: bool = False,
    parallel_config: ParallelProcessingConfig | None = None,
) -> None
```

**パラメータ:**
- `config`: パーサー設定（現在は無視、簡素化のため）
- `graceful_errors`: グレースフルエラーハンドリング有効化（Issue #700対応）
- `parallel_config`: 並列処理設定（Issue #759対応）

**初期化例:**
```python
# 基本的な初期化
parser = Parser()

# エラー処理を有効化
parser = Parser(graceful_errors=True)

# 並列処理設定をカスタマイズ
from kumihan_formatter.parser import ParallelProcessingConfig
config = ParallelProcessingConfig(parallel_threshold_lines=500)
parser = Parser(parallel_config=config)
```

## 主要メソッド

### parse()

基本的なパース処理を実行します。

```python
def parse(self, text: str) -> list[Node]
```

**パラメータ:**
- `text`: 解析対象のKumihanテキスト

**戻り値:**
- `list[Node]`: ASTノードのリスト

**使用例:**
```python
text = """
# 見出し1 #
メインタイトル
##

# 太字 #
重要な内容
##
"""

parser = Parser()
nodes = parser.parse(text)
print(f"解析結果: {len(nodes)}個のノード")
```

### parse_optimized()

最適化されたパース処理（Issue #727対応）。

```python
def parse_optimized(self, text: str) -> list[Node]
```

**特徴:**
- 大容量ファイルに対応
- パフォーマンス監視機能
- パターンキャッシュによる高速化

**使用例:**
```python
# 大容量ファイルの処理
with open("large_document.txt", "r", encoding="utf-8") as f:
    text = f.read()

parser = Parser()
nodes = parser.parse_optimized(text)
```

### parse_streaming_from_text()

ストリーミングパース処理（Issue #757対応）。

```python
def parse_streaming_from_text(
    self,
    text: str,
    progress_callback: Optional[Callable[[dict[str, Any]], None]] = None,
) -> Iterator[Node]
```

**パラメータ:**
- `text`: 解析対象テキスト
- `progress_callback`: プログレス更新コールバック

**使用例:**
```python
def progress_handler(progress_info):
    print(f"進捗: {progress_info['progress_percent']:.1f}%")

parser = Parser()
for node in parser.parse_streaming_from_text(text, progress_handler):
    # ノードを順次処理
    process_node(node)
```

### parse_parallel_streaming()

並列ストリーミング処理。

```python
def parse_parallel_streaming(
    self,
    text: str,
    progress_callback: Optional[Callable[[dict[str, Any]], None]] = None,
) -> Iterator[Node]
```

**使用場面:**
- 非常に大きなファイル（1MB以上）
- マルチコアCPUでの高速処理

## エラーハンドリング

### 従来型エラーハンドリング

```python
parser = Parser()
nodes = parser.parse(text)

# エラーチェック
if parser.get_errors():
    for error in parser.get_errors():
        print(f"エラー: {error}")
```

### グレースフルエラーハンドリング（Issue #700）

```python
parser = Parser(graceful_errors=True)
nodes = parser.parse(text)

# グレースフルエラーの確認
if parser.has_graceful_errors():
    errors = parser.get_graceful_errors()
    summary = parser.get_graceful_error_summary()
    print(f"エラー数: {summary['total_errors']}")
```

## パフォーマンス監視

### 統計情報の取得

```python
parser = Parser()
nodes = parser.parse(text)

# 基本統計
stats = parser.get_statistics()
print(f"処理行数: {stats['total_lines']}")
print(f"エラー数: {stats['errors_count']}")

# パフォーマンス統計
perf_stats = parser.get_performance_statistics()
print(f"現在位置: {perf_stats['current_position']}")
```

### 並列処理メトリクス

```python
# 並列処理の統計情報
metrics = parser.get_parallel_processing_metrics()
```

## キャンセル処理

```python
import threading

def background_parse():
    parser = Parser()
    for node in parser.parse_streaming_from_text(large_text):
        # 長時間処理...
        pass

# バックグラウンドで実行
thread = threading.Thread(target=background_parse)
thread.start()

# 必要に応じてキャンセル
parser.cancel_parsing()
```

## 内部設計

### 専用ハンドラー

パーサーは以下の専用ハンドラーを使用します：

- **BlockHandler**: ブロック記法処理（Issue #813対応）
- **InlineHandler**: インライン記法処理
- **ParallelProcessorHandler**: 並列処理制御

### 設計原則

- **単一責任原則**: 各ハンドラーは特定の責任を持つ
- **依存性注入**: ハンドラーにParserインスタンスを注入
- **後方互換性**: 既存APIを完全に維持

## エラータイプ

### 例外クラス

```python
from kumihan_formatter.parser import (
    ParallelProcessingError,
    ChunkProcessingError,
    MemoryMonitoringError
)
```

### グレースフルエラークラス

```python
from kumihan_formatter.core.common.error_base import GracefulSyntaxError

# エラー詳細情報
error = GracefulSyntaxError(
    line_number=10,
    column=5,
    error_type="syntax_error",
    severity="warning",
    message="不正な記法が検出されました",
    context="#太字 未完了の記法",
    suggestion="##を追加してブロックを完了してください"
)
```

## ベストプラクティス

### 1. パフォーマンス最適化

```python
# 大容量ファイル用
if file_size > 1_000_000:  # 1MB以上
    nodes = parser.parse_optimized(text)
else:
    nodes = parser.parse(text)
```

### 2. エラー処理

```python
# プロダクション環境
parser = Parser(graceful_errors=True)
nodes = parser.parse(text)

# 開発環境
parser = Parser()  # 厳密なエラーチェック
```

### 3. 並列処理

```python
# 高性能が必要な場合
config = ParallelProcessingConfig(
    parallel_threshold_lines=100,
    memory_critical_threshold_mb=500
)
parser = Parser(parallel_config=config)
```

## 関連ドキュメント

- [Renderer API](renderer_api.md) - レンダリングAPI
- [CLI API](cli_api.md) - コマンドラインインターフェース
- [アーキテクチャ](../dev/architecture.md) - システム設計思想
- [記法仕様](../specs/notation.md) - Kumihan記法の詳細