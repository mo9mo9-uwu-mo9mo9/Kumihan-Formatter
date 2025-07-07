# 🔧 技術的問題トラブルシューティング

> **開発者・上級ユーザー向けの技術的な問題解決ガイド**
>
> Python環境、OS固有の問題、パフォーマンス、変換エラー、出力問題を統合的に扱います。

---

## 📋 技術的問題の分類

### 🐍 Python環境問題
### 💻 OS固有問題
### ⚡ パフォーマンス問題
### 🔄 変換・出力問題

---

## 🐍 Python環境問題

### ❌ `Python not found` / `python: command not found`

**症状**
```bash
'python' は、内部コマンドまたは外部コマンド、
操作可能なプログラムまたはバッチ ファイルとして認識されていません。
```

**原因**
- Pythonがインストールされていない
- PATHが正しく設定されていない
- Python実行ファイル名が異なる (`python3`, `py` など)

**解決法**

1. **Pythonインストール確認**
   ```bash
   # 各コマンドを試す
   python --version
   python3 --version
   py --version
   ```

2. **Windowsの場合**
   ```bash
   # Python Launcherを使用
   py -3 --version

   # または環境変数PATHにPythonを追加
   # システム環境変数 → Path → 編集 → 新規
   # C:\Python39 を追加
   ```

3. **macOSの場合**
   ```bash
   # Homebrewでインストール
   brew install python3

   # または.bash_profileに追加
   echo 'alias python="python3"' >> ~/.bash_profile
   source ~/.bash_profile
   ```

### ❌ Virtual environment not found

**症状**
```bash
ImportError: No module named 'kumihan_formatter'
```

**原因**
- 仮想環境が正しく作成されていない
- 仮想環境がアクティベートされていない

**解決法**

1. **仮想環境作成（Windows）**
   ```bash
   cd Kumihan-Formatter
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

2. **仮想環境作成（macOS）**
   ```bash
   cd Kumihan-Formatter
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

### ❌ ImportError / モジュールエラー

**症状**
```python
ImportError: No module named 'click'
ModuleNotFoundError: No module named 'jinja2'
```

**原因**
- 依存関係がインストールされていない
- 仮想環境外で実行している

**解決法**

1. **依存関係一括インストール**
   ```bash
   # 仮想環境内で実行
   pip install -e .[dev]

   # または個別インストール
   pip install click jinja2 pyyaml rich
   ```

2. **requirements.txtがある場合**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 OS固有問題

### Windows固有問題

#### ❌ 権限エラー / Permission Denied

**症状**
```
PermissionError: [Errno 13] Permission denied
```

**解決法**
1. **管理者権限で実行**
   - PowerShellを「管理者として実行」
   - コマンドプロンプトを「管理者として実行」

2. **ウイルス対策ソフトの例外設定**
   - Kumihan-Formatterフォルダを例外に追加
   - リアルタイム保護を一時的に無効化

#### ❌ 文字エンコーディング問題

**症状**
```
UnicodeDecodeError: 'shift_jis' codec can't decode
```

**解決法**
1. **文字コード変更**
   ```bash
   # PowerShellの場合
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

   # またはファイルをUTF-8で保存し直す
   ```

### macOS固有問題

#### ❌ Security警告 / 開発元不明

**症状**
```
"python"は開発元を確認できないため開けません
```

**解決法**
1. **セキュリティ設定変更**
   - システム環境設定 → セキュリティとプライバシー
   - 「このまま許可」をクリック

2. **コマンドライン実行**
   ```bash
   xattr -d com.apple.quarantine /path/to/file
   ```

#### ❌ Command Line Tools未インストール

**症状**
```
xcrun: error: invalid active developer path
```

**解決法**
```bash
# Xcode Command Line Toolsインストール
xcode-select --install
```

---

## ⚡ パフォーマンス問題

### 🐌 変換速度が遅い

**症状**
- 大きなファイル（10MB以上）の変換に10分以上かかる
- CPUが100%になって固まる

**原因と解決法**

1. **ファイルサイズ問題**
   ```bash
   # ファイルサイズ確認
   ls -lh your-file.txt

   # 1MB以下に分割して処理
   split -b 1M your-file.txt part_
   ```

2. **メモリ不足**
   ```bash
   # メモリ使用量確認（Windows）
   tasklist /fi "imagename eq python.exe"

   # メモリ使用量確認（macOS）
   ps aux | grep python
   ```

3. **最適化オプション使用**
   ```bash
   # キャッシュ無効化で高速化
   python -O -m kumihan_formatter.cli input.txt
   ```

### 💾 メモリ不足エラー

**症状**
```
MemoryError: Unable to allocate array
```

**解決法**

1. **ストリーミング処理使用**
   ```python
   # 大きなファイル用の処理方法
   python -m kumihan_formatter input.txt --streaming
   ```

2. **ファイル分割処理**
   ```bash
   # 1000行ずつ分割
   split -l 1000 large-file.txt chunk_

   # 各チャンクを個別処理
   for file in chunk_*; do
       python -m kumihan_formatter "$file"
   done
   ```

### 🔥 CPU使用率が高い

**症状**
- CPUが常時80%以上
- ファンが高速回転

**解決法**

1. **プロセス優先度下げる**
   ```bash
   # Windows
   start /LOW python -m kumihan_formatter input.txt

   # macOS
   nice -n 10 python -m kumihan_formatter input.txt
   ```

2. **並列処理制限**
   ```bash
   # 並列処理無効化
   python -m kumihan_formatter input.txt --single-thread
   ```

---

## 🔄 変換・出力問題

### ❌ 文字化け・エンコーディングエラー

**症状**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```

**解決法**

1. **エンコーディング指定**
   ```bash
   # Shift_JISファイルの場合
   python -m kumihan_formatter input.txt --encoding shift_jis

   # 自動検出
   python -m kumihan_formatter input.txt --encoding auto
   ```

2. **ファイル変換**
   ```bash
   # Windowsでshift_jis → utf-8変換
   powershell -Command "Get-Content input.txt -Encoding Default | Set-Content input_utf8.txt -Encoding UTF8"

   # macOSでshift_jis → utf-8変換
   iconv -f shift_jis -t utf-8 input.txt > input_utf8.txt
   ```

### ❌ HTML出力エラー

**症状**
- HTMLファイルが生成されない
- 空のHTMLファイルが作成される

**原因と解決法**

1. **出力権限問題**
   ```bash
   # 出力ディレクトリの権限確認
   ls -la output/

   # 権限変更
   chmod 755 output/
   ```

2. **テンプレートエラー**
   ```bash
   # デバッグモードで実行
   python -m kumihan_formatter input.txt --debug

   # テンプレート確認
   python -c "from kumihan_formatter import renderer; print(renderer.template_available())"
   ```

### ❌ 画像が表示されない

**症状**
- HTML内で画像のリンクが切れている
- `;;;sample.jpg;;;` が正しく変換されない

**解決法**

1. **画像パス確認**
   ```bash
   # 画像ファイル存在確認
   ls -la images/

   # 相対パス修正
   # ;;;./images/sample.jpg;;; 形式に変更
   ```

2. **画像ファイル形式確認**
   ```bash
   # サポート形式: png, jpg, jpeg, gif, svg
   file images/sample.jpg
   ```

### ❌ CSSスタイルが適用されない

**症状**
- HTMLは生成されるがスタイルが反映されない
- デザインが崩れている

**解決法**

1. **テンプレート確認**
   ```bash
   # テンプレートファイル確認
   ls -la kumihan_formatter/templates/

   # カスタムテンプレート使用
   python -m kumihan_formatter input.txt --template custom.html.j2
   ```

2. **CSSファイル確認**
   ```bash
   # 内蔵CSSの再生成
   python -c "from kumihan_formatter import renderer; renderer.regenerate_css()"
   ```

---

## 🔍 診断・デバッグ手順

### 段階的診断

1. **基本環境確認**
   ```bash
   python --version
   pip list | grep kumihan
   ```

2. **詳細デバッグ実行**
   ```bash
   python -m kumihan_formatter input.txt --verbose --debug
   ```

3. **ログファイル確認**
   ```bash
   # ログ出力先確認
   python -c "import tempfile; print(tempfile.gettempdir())"

   # ログファイル表示
   cat /tmp/kumihan_formatter.log
   ```

### 問題報告テンプレート

技術的問題が解決しない場合、以下の情報を含めてGitHubでIssueを作成してください：

```
### 環境情報
- OS: [Windows 10 / macOS Big Sur / etc]
- Python版: [3.9.0]
- Kumihan-Formatter版: [0.3.0]

### 実行コマンド
```bash
python -m kumihan_formatter input.txt
```

### エラーメッセージ
```
[エラーメッセージ全文をここに]
```

### 期待する結果
[期待していた動作]

### 実際の結果
[実際に起こった動作]

### 追加情報
- ファイルサイズ: [1.2MB]
- 特殊文字使用: [あり/なし]
- 実行時間: [30秒]
```

---

## 📞 サポート・お問い合わせ

技術的問題が解決しない場合：

1. **GitHub Issues**: [問題報告・機能要求](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
2. **ドキュメント**: [完全ガイド](README.md)
3. **FAQ**: [よくある質問](FAQ.md)

**🎯 目標解決時間**
- 基本的な問題: 5分以内
- 環境問題: 15分以内
- 複雑な技術問題: 30分以内
