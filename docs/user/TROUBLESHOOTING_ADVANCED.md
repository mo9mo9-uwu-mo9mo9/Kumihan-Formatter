# 🔬 高度なトラブルシューティング

> **デバッグ・予防・リセット手順の詳細ガイド**

[← トラブルシューティング目次に戻る](TROUBLESHOOTING.md)

---

## 📋 高度なトラブルシューティング目次

- [段階的問題切り分け手順](#-段階的問題切り分け手順)
- [ログファイルの確認方法](#-ログファイルの確認方法)
- [エラーメッセージの解読](#-エラーメッセージの解読)
- [予防的対策](#️-予防的対策)
- [完全リセット手順](#-完全リセット手順)

---

## 🕵️ **段階的問題切り分け手順**

### **Level 1: 環境確認**
```bash
# システム基本情報
echo "=== システム情報 ==="
uname -a                    # OS情報
python --version            # Pythonバージョン
pip --version               # pipバージョン
which python                # Python実行ファイル場所

# プロジェクト環境確認
echo "=== プロジェクト情報 ==="
pwd                         # 現在の作業ディレクトリ
ls -la                      # ファイル一覧
ls -la .venv/               # 仮想環境確認（存在する場合）
```

### **Level 2: 最小限ファイルでのテスト**

**minimal_test.txt:**
```text
;;;見出し1
テスト
;;;

これはテストです。

;;;太字
重要
;;;
```

```bash
# 最小ファイルでの変換テスト
echo ";;;見出し1\nテスト\n;;;\n\nこれはテストです。" > minimal_test.txt
python -m kumihan_formatter minimal_test.txt --no-preview

# 結果確認
ls -la dist/
cat dist/minimal_test.html | head -20
```

### **Level 3: 記法チェック**
```bash
# 記法エラーの特定
python -c "
with open('your_file.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

block_start = None
for i, line in enumerate(lines, 1):
    if line.strip().startswith(';;;'):
        if line.strip().endswith(';;;'):
            print(f'Line {i}: Single line marker')
        elif block_start is None:
            block_start = i
            print(f'Line {i}: Block start')
        else:
            print(f'Line {i}: Block end (started at {block_start})')
            block_start = None

if block_start:
    print(f'WARNING: Unclosed block starting at line {block_start}')
"
```

### **Level 4: 詳細デバッグ**
```bash
# 詳細ログ出力
python -m kumihan_formatter your_file.txt --verbose > debug.log 2>&1

# Python実行時エラー詳細
python -u -m kumihan_formatter your_file.txt

# ステップバイステップ実行
python -m pdb -m kumihan_formatter your_file.txt
```

---

## 📊 **ログファイルの確認方法**

### **ログファイルの場所**
```bash
# 一般的なログ場所
ls -la ~/.kumihan/          # ユーザー設定ディレクトリ
ls -la ./logs/              # プロジェクトローカル
ls -la /tmp/kumihan_*       # 一時ログファイル

# Windows
dir %APPDATA%\Kumihan\
dir %TEMP%\kumihan_*
```

### **ログの読み方**
```bash
# 最新ログファイル確認
tail -f ~/.kumihan/debug.log

# エラーレベルの抽出
grep -i "error\|exception\|traceback" debug.log

# 時系列でのエラー確認
grep "$(date +%Y-%m-%d)" debug.log | grep -i error
```

**ログレベルの意味:**
- **DEBUG**: 詳細な実行情報
- **INFO**: 一般的な処理情報
- **WARNING**: 注意すべき状況
- **ERROR**: エラー（処理継続可能）
- **CRITICAL**: 致命的エラー（処理停止）

---

## 🐛 **エラーメッセージの解読**

### **一般的なエラーパターン**

#### **1. `UnicodeDecodeError`**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x82 in position 15: invalid start byte
```
**原因**: ファイルがUTF-8以外の文字コード
**解決**: ファイルをUTF-8で保存し直す

#### **2. `KeyError: 'template_name'`**
```
KeyError: 'template_name'
```
**原因**: 設定ファイルの記述エラー
**解決**: config.yamlの構文チェック

#### **3. `FileNotFoundError: [Errno 2] No such file or directory`**
```
FileNotFoundError: [Errno 2] No such file or directory: 'images/missing.jpg'
```
**原因**: 画像ファイルが存在しない
**解決**: 画像ファイルのパス・存在確認

#### **4. `MemoryError`**
```
MemoryError
```
**原因**: メモリ不足
**解決**: ファイル分割またはシステムメモリ増設

#### **5. `RecursionError: maximum recursion depth exceeded`**
```
RecursionError: maximum recursion depth exceeded
```
**原因**: 無限ループ（記法のネストエラー）
**解決**: 記法の書き直し

#### **6. `PermissionError: [Errno 13] Permission denied`**
```
PermissionError: [Errno 13] Permission denied: 'dist/output.html'
```
**原因**: ファイル・ディレクトリの権限不足
**解決**: 権限変更またはファイル閉じる

---

## 🛡️ **予防的対策**

### **推奨環境構築**

#### **最適なディレクトリ構造**
```
KumihanProjects/
├── project1/
│   ├── main.txt
│   ├── images/
│   ├── config.yaml
│   ├── backup/
│   └── dist/
├── project2/
└── templates/
    ├── basic_config.yaml
    ├── npc_template.txt
    └── location_template.txt
```

#### **推奨ファイル命名規則**
- **テキストファイル**: `scenario_v1.0.txt`
- **画像ファイル**: `img_01_mansion.jpg`
- **設定ファイル**: `config_print.yaml`
- **出力ファイル**: `scenario_final.html`

### **定期メンテナンス**

#### **月次チェック項目**
```bash
# 依存関係の更新確認
pip list --outdated

# ディスク容量確認
df -h                       # macOS/Linux
dir C: /s                   # Windows

# バックアップの整理
find backup/ -mtime +30 -name "*.txt" -ls  # 30日以上前のファイル

# 一時ファイルの清掃
rm -rf /tmp/kumihan_*       # macOS/Linux
del %TEMP%\kumihan_*        # Windows
```

#### **年次チェック項目**
```bash
# Python環境の更新
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

# プロジェクトファイルの整理
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

---

## 🆘 **完全リセット手順**

### **段階的リセット手順**

#### **Level 1: 仮想環境のリセット**
```bash
# 1. 現在の仮想環境を削除
rm -rf .venv                # macOS/Linux
rmdir /s .venv              # Windows

# 2. 新しい仮想環境を作成
python -m venv .venv

# 3. 仮想環境をアクティベート
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

# 4. 最新のpipにアップグレード
python -m pip install --upgrade pip

# 5. 依存関係を再インストール
pip install -e .

# 6. 動作確認
python -m kumihan_formatter --version
python -m kumihan_formatter examples/sample.txt --no-preview
```

#### **Level 2: 設定ファイルのリセット**
```bash
# 1. ユーザー設定ディレクトリの確認
ls -la ~/.kumihan/          # macOS/Linux
dir %APPDATA%\Kumihan\      # Windows

# 2. 設定ファイルのバックアップ
cp ~/.kumihan/config.yaml ~/.kumihan/config.yaml.backup

# 3. 設定ファイルの削除
rm ~/.kumihan/config.yaml   # macOS/Linux
del %APPDATA%\Kumihan\config.yaml  # Windows

# 4. デフォルト設定での動作確認
python -m kumihan_formatter examples/sample.txt
```

#### **Level 3: 完全なクリーンインストール**
```bash
# 1. プロジェクトディレクトリの完全バックアップ
cp -r KumihanProjects KumihanProjects_backup

# 2. Kumihan-Formatterの完全削除
rm -rf Kumihan-Formatter

# 3. 最新版の再ダウンロード
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 4. 初回セットアップ
# Windows: セットアップ_Windows.bat
# macOS: ./セットアップ_Mac.command

# 5. 動作確認
python -m kumihan_formatter examples/sample.txt
```

### **リセット後の確認項目**
```bash
# 基本動作確認
echo ";;;見出し1\nテスト\n;;;\nこれはテストです。" > reset_test.txt
python -m kumihan_formatter reset_test.txt

# 確認項目チェックリスト
# [ ] Python環境が正常に動作する
# [ ] 依存関係がすべてインストールされている
# [ ] 基本的な変換が成功する
# [ ] HTML出力が正常に生成される
# [ ] ブラウザで正常に表示される
```

---

## 🔧 **高度なデバッグツール**

### **Pythonデバッガ（pdb）の使用**
```bash
# ブレークポイント付きでの実行
python -m pdb -m kumihan_formatter your_file.txt

# 基本的なpdbコマンド
# l(ist)    - 現在のコード表示
# n(ext)    - 次の行に進む
# s(tep)    - 関数内に入る
# c(ontinue) - 実行継続
# p <var>   - 変数の値を表示
# q(uit)    - デバッガ終了
```

### **メモリ使用量の詳細監視**
```bash
# メモリプロファイリング（要memory_profiler）
pip install memory_profiler
python -m memory_profiler -m kumihan_formatter your_file.txt

# 実行時間の詳細分析
python -m cProfile -s cumulative -m kumihan_formatter your_file.txt > profile.txt
```

### **ログレベルの調整**
```python
# debug_config.yaml
logging:
  level: DEBUG
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: debug.log

# 使用方法
python -m kumihan_formatter your_file.txt --config debug_config.yaml
```

---

## 📞 **上級者向けサポート**

### **技術的問題の報告テンプレート**
```
## 高度なトラブルシューティング報告

### 実行環境詳細
- Python実装: [CPython 3.9.7 / PyPy 7.3.7]
- 仮想環境: [venv / conda / pipenv]
- インストール方法: [pip / git clone]
- 実行方法: [CLI / API / スクリプト]

### デバッグ情報
- ログレベル: [DEBUG / INFO]
- プロファイリング結果: [添付]
- メモリ使用量: [ピーク時のMB]
- 実行時間: [詳細時間]

### 問題の詳細分析
[段階的切り分けの結果、最小再現コード等]

### 試行したデバッグ手法
- [ ] pdbデバッガ使用
- [ ] プロファイリング実行
- [ ] ログレベル調整
- [ ] 段階的切り分け
- [ ] 完全リセット
```

---

## 📚 **関連リソース**

### **技術ドキュメント**
- **[トラブルシューティング目次](TROUBLESHOOTING.md)** - 基本的な問題解決
- **[開発者ガイド](../dev/ARCHITECTURE.md)** - システム内部構造

### **コミュニティ**
- **[GitHub Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)** - バグ報告・機能要望
- **[GitHub Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)** - 技術的議論

---

**高度な問題も必ず解決できます！ 🔬✨**