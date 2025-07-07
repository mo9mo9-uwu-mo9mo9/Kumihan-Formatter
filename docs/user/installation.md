# インストールガイド

Kumihan-Formatterのインストール方法を詳しく説明します。

## Python環境の準備

### Windows

1. [Python公式サイト](https://www.python.org/downloads/)にアクセス
2. 最新版のPython 3.12以上をダウンロード
3. インストール時に**「Add Python to PATH」にチェック**を入れる
4. インストール完了後、コマンドプロンプトで確認：
   ```cmd
   python --version
   ```

### macOS

1. [Python公式サイト](https://www.python.org/downloads/)からダウンロード
2. または、Homebrewを使用：
   ```bash
   brew install python
   ```
3. ターミナルで確認：
   ```bash
   python3 --version
   ```

## Kumihan-Formatterのインストール

### 方法1: pipでインストール（推奨）

```bash
pip install kumihan-formatter
```

### 方法2: GitHubからダウンロード

1. [GitHubのリリースページ](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases)
2. 最新版のZIPファイルをダウンロード
3. 解凍後、フォルダ内で：
   ```bash
   pip install -e .
   ```

## 動作確認

インストール後、以下のコマンドで確認：

```bash
kumihan-formatter --version
```

## トラブルシューティング

### よくある問題

- **「Pythonが見つかりません」**: PATHの設定を確認
- **「pipが見つかりません」**: Python再インストール時にpipを含める
- **権限エラー**: 管理者権限で実行、または仮想環境を使用

詳細は[トラブルシューティング](TROUBLESHOOTING.md)を参照してください。
