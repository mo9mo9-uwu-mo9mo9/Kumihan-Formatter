# Windows環境でのトラブルシューティング

## 文字化け問題の解決

### 問題の症状
- batファイル実行時に日本語が文字化けする
- `'https:'` や `'繝ｫ'` のような不正な文字が表示される
- `'errorlevel' は、内部コマンドまたは外部コマンド...` のエラーが表示される

### 解決方法

#### 方法1: 安全版batファイルの使用（推奨）
```batch
# 通常版の代わりに安全版を使用
kumihan_convert_safe.bat      # kumihan_convert.bat の代わり
run_examples_safe.bat         # run_examples.bat の代わり
```

#### 方法2: コマンドプロンプトの設定変更
1. コマンドプロンプトを管理者として実行
2. 以下のコマンドを実行：
```cmd
chcp 65001
```
3. その後、通常のbatファイルを実行

#### 方法3: PowerShellの使用
コマンドプロンプトの代わりにPowerShellを使用：
```powershell
# PowerShellでUTF-8エンコーディングを設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# その後、batファイルを実行
.\kumihan_convert.bat
```

#### 方法4: 環境変数の設定
システム環境変数に以下を追加：
```
PYTHONIOENCODING=utf-8
```

### Windows バージョン別対応

#### Windows 10 Build 1903以降
- デフォルトでUTF-8サポートが改善されています
- 「地域」設定で「ベータ: ワールドワイド言語サポートでUnicodeUTF-8を使用」をオンにする

#### Windows 10 古いバージョン / Windows 8.1
- 安全版batファイル（`*_safe.bat`）の使用を強く推奨
- または PowerShell の使用を推奨

### その他のエラー対処

#### Python関連エラー
```
Error: Python not found
```
**解決法**: Python 3.9以上をインストール
- https://www.python.org/downloads/ からダウンロード
- インストール時に「Add Python to PATH」をチェック

#### 仮想環境関連エラー
```
Virtual environment not found
```
**解決法**: 
1. `kumihan_convert.bat` を先に実行
2. 自動セットアップを完了させる

#### 権限関連エラー
```
Access denied
```
**解決法**: 
1. コマンドプロンプトを管理者として実行
2. またはファイル/フォルダの権限を確認

### 追加ヘルプ

#### 完全クリーンインストール
問題が解決しない場合：
1. `.venv` フォルダを削除
2. `kumihan_convert.bat` を実行して再セットアップ

#### サポート
問題が続く場合は、以下の情報とともにGitHub Issueで報告してください：
- Windows バージョン
- Python バージョン
- エラーメッセージの完全なコピー
- 使用したbatファイル名