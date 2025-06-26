# エラーハンドリングガイド

> **Kumihan-Formatter ユーザーフレンドリーエラーシステム実装ガイド**

---

## 📋 概要

Kumihan-Formatterは、ユーザーが直面する技術的なエラーメッセージを分かりやすい日本語メッセージと具体的な解決方法に変換する包括的なエラーハンドリングシステムを実装しています。

### 🎯 設計目標

- **自己解決率70%向上**: エラーメッセージだけで問題解決可能
- **初心者に優しい**: 技術用語を避け、次のアクションが明確
- **具体的な解決方法**: 段階的な手順と代替手段を提示
- **プラットフォーム対応**: OS別の最適な解決方法を提案

---

## 🏗️ システム構成

### コンポーネント概要

```text
kumihan_formatter/core/error_system.py
├── ErrorLevel (enum)              # エラーレベル分類
├── ErrorCategory (enum)           # エラーカテゴリ分類
├── ErrorSolution (dataclass)      # 解決方法構造
├── UserFriendlyError (dataclass)  # ユーザーフレンドリーエラー
├── SmartSuggestions (class)       # スマート提案システム
├── ErrorCatalog (class)           # 定義済みエラーパターン
└── ErrorHandler (class)           # エラーハンドラ
```

### エラーレベル分類

| レベル | 説明 | 表示色 | 使用場面 |
|--------|------|--------|----------|
| `INFO` | 情報 | 青色 | 処理状況・ヒント |
| `WARNING` | 警告 | 黄色 | 記法エラー・注意事項 |
| `ERROR` | エラー | 赤色 | ファイル・権限・エンコーディング |
| `CRITICAL` | 致命的 | 赤背景 | 予期しないシステムエラー |

### エラーカテゴリ分類

| カテゴリ | 説明 | 対象エラー |
|----------|------|------------|
| `FILE_SYSTEM` | ファイル関連 | ファイル未発見・空ファイル・サイズ |
| `ENCODING` | エンコーディング関連 | 文字化け・文字コード |
| `SYNTAX` | 記法関連 | Kumihan記法エラー |
| `PERMISSION` | 権限関連 | ファイルアクセス権限 |
| `SYSTEM` | システム関連 | メモリ・ディスク容量 |
| `NETWORK` | ネットワーク関連 | 通信エラー |
| `UNKNOWN` | 不明 | 予期しないエラー |

---

## 💻 実装例

### 基本的な使用方法

```python
from kumihan_formatter.core.error_system import ErrorHandler, ErrorCatalog

# エラーハンドラの初期化
error_handler = ErrorHandler(console_ui=ui)

try:
    # ファイル操作など
    content = Path("test.txt").read_text()
except FileNotFoundError as e:
    # 例外をユーザーフレンドリーエラーに変換
    friendly_error = error_handler.handle_exception(
        e, context={"file_path": "test.txt"}
    )
    
    # エラーを表示
    error_handler.display_error(friendly_error, verbose=True)
```

### カスタムエラーの作成

```python
from kumihan_formatter.core.error_system import (
    UserFriendlyError, ErrorLevel, ErrorCategory, ErrorSolution
)

# カスタムエラーの作成
custom_error = UserFriendlyError(
    error_code="E007",
    level=ErrorLevel.WARNING,
    category=ErrorCategory.SYNTAX,
    user_message="カスタムエラーメッセージ",
    solution=ErrorSolution(
        quick_fix="即座にできる解決方法",
        detailed_steps=[
            "1. 詳細な手順1",
            "2. 詳細な手順2",
            "3. 詳細な手順3"
        ],
        alternative_approaches=[
            "代替手段1",
            "代替手段2"
        ]
    ),
    context={"custom_data": "value"}
)
```

### スマート提案の活用

```python
from kumihan_formatter.core.error_system import SmartSuggestions

# 無効なキーワードに対する提案
suggestions = SmartSuggestions.suggest_keyword("太文字")
print(suggestions)  # ["太字"]

# エンコーディングエラーの提案
encoding_suggestions = SmartSuggestions.suggest_file_encoding(Path("file.txt"))
# プラットフォーム別の具体的な解決方法が返される
```

---

## 🎨 エラー表示の Before/After

### Before（技術的メッセージ）

```
FileNotFoundError: [Errno 2] No such file or directory: 'test.txt'
```

### After（ユーザーフレンドリーメッセージ）

```
[E001] 📁 ファイル 'test.txt' が見つかりません
💡 解決方法: ファイル名とパスを確認してください

詳細な解決手順:
   1. ファイル名のスペルミスがないか確認
   2. ファイルが正しい場所に保存されているか確認
   3. 拡張子が .txt になっているか確認
   4. ファイルが他のアプリケーションで開かれていないか確認

代替手段:
   • ファイルをKumihan-Formatterのフォルダにコピーして再実行
   • フルパス（絶対パス）で指定して実行
```

---

## 🔧 開発者向けガイド

### 新しいエラーパターンの追加

1. **ErrorCatalogクラスに新しいメソッドを追加**

```python
@staticmethod
def create_new_error_type(param1: str, param2: int) -> UserFriendlyError:
    """新しいエラータイプの作成"""
    return UserFriendlyError(
        error_code="E008",  # 新しいエラーコード
        level=ErrorLevel.ERROR,
        category=ErrorCategory.SYSTEM,
        user_message=f"新しいエラー: {param1}",
        solution=ErrorSolution(
            quick_fix="即座の解決方法",
            detailed_steps=[
                "詳細手順1",
                "詳細手順2"
            ]
        ),
        context={"param1": param1, "param2": param2}
    )
```

2. **ErrorHandlerクラスのhandle_exception メソッドに追加**

```python
def handle_exception(self, exception: Exception, context: Dict[str, Any] = None) -> UserFriendlyError:
    # 既存の処理...
    
    # 新しい例外タイプの処理を追加
    elif isinstance(exception, YourCustomException):
        param1 = context.get('param1', 'default_value')
        param2 = context.get('param2', 0)
        return ErrorCatalog.create_new_error_type(param1, param2)
```

### エラーコード命名規則

| 範囲 | 用途 | 例 |
|------|------|-----|
| E001-E099 | ファイルシステム関連 | E001: ファイル未発見 |
| E100-E199 | エンコーディング関連 | E002: 文字化け |
| E200-E299 | 記法・構文関連 | E003: 記法エラー |
| E300-E399 | 権限関連 | E004: 権限エラー |
| E400-E499 | システム・リソース関連 | E006: ファイルサイズ |
| E900-E999 | 不明・予期しないエラー | E999: 不明エラー |

### テストの書き方

```python
def test_custom_error_handling():
    """カスタムエラーのテスト"""
    mock_console_ui = MagicMock()
    handler = ErrorHandler(console_ui=mock_console_ui)
    
    # カスタム例外でテスト
    exception = YourCustomException("test message")
    error = handler.handle_exception(
        exception, 
        context={"param1": "test_value", "param2": 123}
    )
    
    # 期待される結果を確認
    assert error.error_code == "E008"
    assert "test_value" in error.user_message
    assert error.level == ErrorLevel.ERROR
```

---

## 🚀 パフォーマンス考慮事項

### エラーハンドリングの最適化

1. **遅延評価**: エラーメッセージの生成は必要時のみ
2. **キャッシュ**: 同一エラーパターンの再利用
3. **軽量表示**: verboseモードでのみ詳細情報を表示

### メモリ使用量

- エラー履歴は最大100件まで保持
- 古いエラーは自動的に削除
- 大きなコンテキストデータは参照のみ保持

---

## 📊 エラー統計・分析

### エラー統計の取得

```python
# エラー統計の取得
stats = error_handler.get_error_statistics()
print(f"総エラー数: {stats['total_errors']}")
print(f"カテゴリ別: {stats['by_category']}")
print(f"レベル別: {stats['by_level']}")
```

### ログ出力（将来実装予定）

```python
# 構造化ログ出力
{
    "timestamp": "2025-06-26T10:30:00Z",
    "error_code": "E001",
    "level": "error",
    "category": "file_system",
    "context": {
        "file_path": "test.txt",
        "operation": "read"
    },
    "system_info": {
        "os": "Darwin",
        "python_version": "3.11.0"
    }
}
```

---

## 🔍 トラブルシューティング

### よくある問題

#### 1. エラーメッセージが表示されない

**原因**: ConsoleUIが正しく初期化されていない  
**解決**: ErrorHandlerにconsole_uiを渡すことを確認

```python
# ✗ 間違い
handler = ErrorHandler()

# ✓ 正しい
handler = ErrorHandler(console_ui=ui)
```

#### 2. スマート提案が機能しない

**原因**: 辞書データの読み込みエラー  
**解決**: VALID_KEYWORDSとCOMMON_MISTAKESの定義を確認

#### 3. プラットフォーム固有の提案が出ない

**原因**: platform.system()の戻り値確認  
**解決**: 対応プラットフォーム名の確認

### デバッグ方法

```python
# デバッグ情報の有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# エラーハンドラのverboseモード
error_handler.display_error(error, verbose=True)

# コンテキスト情報の確認
print(f"Error context: {error.context}")
```

---

## 📈 今後の拡張予定

### 短期（v1.0リリースまで）

- [ ] 国際化対応（英語メッセージ）
- [ ] エラーログのファイル出力
- [ ] Web UI用のJSON形式エラー出力

### 中期（v2.0以降）

- [ ] 機械学習による提案精度向上
- [ ] ユーザーフィードバック収集機能
- [ ] エラー解決率の自動測定

### 長期

- [ ] 音声による読み上げ対応
- [ ] 視覚的なエラー表示（図解）
- [ ] コミュニティによる解決方法共有

---

## 🤝 コントリビューション

新しいエラーパターンや改善提案は以下の手順で追加してください：

1. **Issue作成**: 新しいエラーパターンの報告
2. **実装**: ErrorCatalogへの追加とテスト作成
3. **テスト**: 全テストケースの実行
4. **ドキュメント更新**: 本ガイドの更新
5. **プルリクエスト**: レビュー後マージ

---

## 📚 関連ドキュメント

- [CONTRIBUTING.md](../CONTRIBUTING.md) - 開発ガイドライン
- [SPEC.md](../SPEC.md) - Kumihan記法仕様
- [dev/tests/test_error_system.py](../dev/tests/test_error_system.py) - テストケース例

このエラーハンドリングシステムにより、Kumihan-Formatterのユーザー体験が大幅に向上し、初心者でも安心して使用できるツールになります。