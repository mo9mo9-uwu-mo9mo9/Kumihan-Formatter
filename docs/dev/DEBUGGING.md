# Kumihan-Formatter デバッグガイド

## 概要

Kumihan-Formatterには開発者向けのデバッグ機能が組み込まれています。このガイドでは、各種デバッグツールの使用方法と問題解決のアプローチを説明します。

## デバッグ機能一覧

### 1. GUIデバッグロガー

GUIアプリケーションの動作を詳細に追跡するための包括的なデバッグシステム。

#### 基本使用方法
```bash
# GUIデバッグモードで起動
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher
```

#### 詳細設定
```bash
# ログレベル指定
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_LEVEL=DEBUG python3 -m kumihan_formatter.gui_launcher

# カスタムログファイル
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_FILE=/tmp/custom_debug.log python3 -m kumihan_formatter.gui_launcher

# コンソール出力も有効
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_CONSOLE_LOG=true python3 -m kumihan_formatter.gui_launcher
```

#### 機能詳細

**ログ記録対象:**
- GUI初期化プロセス
- モジュールインポート処理
- ボタンクリックなどのUIイベント
- ファイル選択、ディレクトリ操作
- エラーとスタックトレース
- パフォーマンス計測

**ログファイル出力:**
- デフォルト場所: `/tmp/kumihan_gui_debug.log`
- ローテーション機能付き
- セッションID付きで識別可能

**リアルタイムログビューアー:**
- GUI内で「ログ」ボタンをクリック
- レベル別フィルタリング（DEBUG, INFO, WARNING, ERROR）
- 自動スクロール機能
- ログクリア機能
- 外部エディタでファイルを開く機能

### 2. 開発ログ機能 (CLI)

コマンドライン版での詳細ログ機能。

```bash
# 開発ログ有効化
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# ログファイル確認
ls /tmp/kumihan_formatter/
cat /tmp/kumihan_formatter/dev_log_*.log
```

#### 特徴
- 出力先: `/tmp/kumihan_formatter/`
- ファイル名: `dev_log_<セッションID>.log`
- 自動クリーンアップ: 24時間経過後に削除
- サイズ制限: 5MB（超過時は自動ローテーション）

## 一般的な問題と対処法

### GUIアプリがクラッシュする場合

1. **デバッグモードで起動**
   ```bash
   KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher
   ```

2. **ログファイルを確認**
   ```bash
   tail -f /tmp/kumihan_gui_debug.log
   ```

3. **インポートエラーの確認**
   - ログでインポート失敗の詳細を確認
   - Pythonパスの問題を特定

### GUIが表示されない場合

1. **コンソール出力を有効化**
   ```bash
   KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_CONSOLE_LOG=true python3 -m kumihan_formatter.gui_launcher
   ```

2. **tkinterの動作確認**
   ```python
   import tkinter as tk
   root = tk.Tk()
   root.mainloop()
   ```

### パフォーマンス問題の調査

1. **パフォーマンスログの確認**
   - ログビューアーで各操作の実行時間を確認
   - ボトルネックとなる処理を特定

2. **メモリ使用量の監視**
   - psutilがある場合、起動時メモリ使用量を記録

### 変換処理のデバッグ

1. **CLIでの詳細ログ**
   ```bash
   KUMIHAN_DEV_LOG=true kumihan convert --debug input.txt output.txt
   ```

2. **構文チェック**
   ```bash
   kumihan check-syntax manuscript.txt
   ```

## 開発者向けTips

### デバッグロガーの活用

**カスタムログ追加:**
```python
from kumihan_formatter.core.debug_logger import debug, info, warning, error

# 関数の開始/終了をログ
@log_gui_method
def my_function(self):
    info("カスタム処理開始")
    # 処理内容
    info("カスタム処理完了")

# GUIイベントのログ
log_gui_event("button_click", "custom_button", "追加情報")
```

**パフォーマンス計測:**
```python
import time
from kumihan_formatter.core.debug_logger import log_performance

start_time = time.time()
# 処理内容
duration = time.time() - start_time
log_performance("処理名", duration)
```

### ログビューアーの使い方

1. **デバッグモードでGUI起動**
2. **「ログ」ボタンをクリック**
3. **フィルタリング設定:**
   - レベル選択でログを絞り込み
   - 自動スクロールのON/OFF切り替え
4. **ログクリア:** 不要なログを削除
5. **外部エディタ:** 詳細分析のためファイルを開く

### トラブルシューティング手順

1. **現象の再現**
   - デバッグモードで同じ操作を実行
   - ログで問題箇所を特定

2. **ログ分析**
   - ERRORレベルでフィルタリング
   - スタックトレースを確認
   - 直前のINFO/DEBUGログで原因を推定

3. **修正と検証**
   - 修正後、同じ手順で動作確認
   - ログで正常な動作を確認

## 本番環境での注意事項

- デバッグ機能は開発/テスト環境でのみ使用
- 本番環境では環境変数を設定しない
- ログファイルのサイズと保存期間に注意
- 機密情報がログに含まれないよう確認

## 関連ファイル

- `kumihan_formatter/core/debug_logger.py` - デバッグロガー本体
- `kumihan_formatter/core/log_viewer.py` - ログビューアーウィンドウ
- `kumihan_formatter/gui_launcher.py` - GUI統合部分
- `/tmp/kumihan_gui_debug.log` - デフォルトログファイル
- `/tmp/kumihan_formatter/` - 開発ログディレクトリ

## 更新履歴

- 2025-07-14: GUIデバッグロガー機能を追加
- 2025-07-08: 開発ログ機能を追加 (Issue#446)
