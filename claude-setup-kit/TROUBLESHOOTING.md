# 🔧 Serena-local トラブルシューティング

> 実際の問題とその解決策のみを記載

## 🎯 このガイドについて

このガイドでは、Serena-localの設定・運用中に実際に発生する問題と、検証済みの解決策を提供します。

**重要：このガイドには検証されていない解決策は含まれていません。**

## 🚨 緊急時の対処法

### 設定が完全に破損した場合
```bash
# 設定ファイルのバックアップ（存在する場合）
cp ~/.config/claude_desktop/config.json ~/.config/claude_desktop/config.json.broken
# または macOSの場合
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json.broken

# 緊急修復スクリプトの実行
./claude-setup-kit/scripts/emergency-fix.sh
```

## 📋 問題分類別対処法

### 1. MCP接続関連の問題

#### 問題: Serena-localが認識されない

**症状**
- Claude CodeでSerenaツールが利用できない
- MCPサーバーリストにserenaが表示されない

**診断方法**
```bash
# Claude Desktop設定ファイルの確認
cat ~/.config/claude_desktop/config.json  # Linux
# または
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS

# JSON構文エラーの確認
python -c "import json; json.load(open('~/.config/claude_desktop/config.json'))" 2>/dev/null && echo "JSON OK" || echo "JSON Error"
```

**解決策**
```bash
# 1. JSON構文の修正
python -m json.tool < ~/.config/claude_desktop/config.json

# 2. 設定ファイルの権限確認
ls -la ~/.config/claude_desktop/config.json

# 3. Claude Desktopの完全再起動
# （アプリケーションを完全に終了後、再起動）
```

#### 問題: serenaのパスが間違っている

**症状**
- MCPサーバーエラーが表示される
- 「command not found」エラー

**診断方法**
```bash
# serenaの実際のパス確認
find $HOME -name "serena" -type d 2>/dev/null
which python
```

**解決策**
```bash
# 正しいパスで設定を更新
# 設定ファイル内の"cwd"値を実際のパスに変更
```

### 2. Python環境関連の問題

#### 問題: Python バージョン不一致

**症状**
- serenaが起動しない
- モジュールインポートエラー

**診断方法**
```bash
# Python バージョン確認
python --version
python3 --version

# serena依存関係確認
cd /path/to/serena
uv venv
source .venv/bin/activate
python -m serena_local --help
```

**解決策**
```bash
# Python 3.12以上のインストール
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12

# macOS (Homebrew)
brew install python@3.12

# serenaの再インストール
cd /path/to/serena
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .
```

#### 問題: 仮想環境のアクティベーション失敗

**症状**
- uv venvコマンドエラー
- pip install失敗

**診断方法**
```bash
# UV インストール確認
uv --version

# Python venv モジュール確認
python -m venv --help
```

**解決策**
```bash
# UVの再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # または ~/.zshrc

# 手動で仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate  # Windows

pip install -e .
```

### 3. ファイル権限・アクセス関連の問題

#### 問題: 設定ファイルへの書き込み権限がない

**症状**
- 設定ファイル保存エラー
- Permission denied エラー

**診断方法**
```bash
# 設定ディレクトリの権限確認
ls -la ~/.config/claude_desktop/
ls -la ~/Library/Application\ Support/Claude/  # macOS

# 現在のユーザー確認
whoami
```

**解決策**
```bash
# 権限修正（Linux）
chmod 755 ~/.config/claude_desktop/
chmod 644 ~/.config/claude_desktop/config.json

# 権限修正（macOS）
chmod 755 ~/Library/Application\ Support/Claude/
chmod 644 ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

#### 問題: serenaディレクトリへのアクセス権限がない

**症状**
- MCPサーバー起動エラー
- ディレクトリアクセスエラー

**解決策**
```bash
# serenaディレクトリの権限修正
chmod -R 755 /path/to/serena
chown -R $USER:$USER /path/to/serena
```

### 4. プロジェクト固有の問題

#### 問題: Kumihan-Formatterプロジェクトでツールが動作しない

**症状**
- find_symbolが機能しない
- プロジェクト構造が認識されない

**診断方法**
```bash
# プロジェクトディレクトリ確認
pwd
ls -la kumihan_formatter/

# Python パッケージ構造確認
find . -name "*.py" | head -5
```

**解決策**
```bash
# プロジェクトディレクトリで実行
cd /path/to/Kumihan-Formatter

# Python パスの確認
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Language Serverの再起動
# Claude Codeで以下を実行
# 「Language Serverを再起動してください」
```

### 5. パフォーマンス関連の問題

#### 問題: 応答が非常に遅い

**症状**
- ツール実行に30秒以上かかる
- Claude Codeが応答しない

**診断方法**
```bash
# システムリソース確認
top -n 1 | head -10
free -h  # Linux
vm_stat | head -10  # macOS

# プロセス確認
ps aux | grep python | grep serena
```

**解決策**
```bash
# 1. メモリ不足の場合
# 他のアプリケーションを終了

# 2. プロジェクトサイズが大きい場合
# 部分的なディレクトリで実行

# 3. Language Serverの再起動
# Claude Codeで「Language Serverを再起動」を依頼
```

## 🔍 診断用コマンド集

### 基本診断
```bash
# 環境確認
echo "Python: $(python --version)"
echo "UV: $(uv --version 2>/dev/null || echo 'Not installed')"
echo "Current dir: $(pwd)"

# serena 確認
find $HOME -name "serena" -type d 2>/dev/null

# Claude Desktop設定確認
ls -la ~/.config/claude_desktop/config.json 2>/dev/null || ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json 2>/dev/null

# JSON構文確認
python -c "
import json
import os
config_paths = [
    os.path.expanduser('~/.config/claude_desktop/config.json'),
    os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json')
]
for path in config_paths:
    if os.path.exists(path):
        try:
            with open(path) as f:
                json.load(f)
            print(f'✅ {path}: JSON OK')
        except Exception as e:
            print(f'❌ {path}: JSON Error - {e}')
        break
"
```

### 接続テスト
```bash
# serena動作テスト
cd /path/to/serena
source .venv/bin/activate 2>/dev/null || true
python -m serena_local --help 2>&1 | head -5
```

## 🚫 よくある間違い・誤解

### 誤解1: 「自動で全てが設定される」
**現実**: 全ての設定は手動で行う必要があります

### 誤解2: 「設定は一度で完了する」
**現実**: 環境により複数回の調整が必要な場合があります

### 誤解3: 「エラーは自動で修復される」
**現実**: エラーは手動で診断・修正する必要があります

### 誤解4: 「具体的な数値効果が保証される」
**現実**: 効果は環境・使用方法により大きく変動します

## 📞 サポートが必要な場合

### 自己解決できない場合の対応

1. **問題の明確化**
   - 発生している症状の具体的な記録
   - エラーメッセージの正確な内容
   - 実行したコマンドと結果

2. **環境情報の収集**
   ```bash
   # 環境情報収集スクリプト
   echo "=== Environment Info ===" > debug-info.txt
   echo "OS: $(uname -a)" >> debug-info.txt
   echo "Python: $(python --version)" >> debug-info.txt
   echo "UV: $(uv --version 2>/dev/null || echo 'Not installed')" >> debug-info.txt
   echo "Project: $(pwd)" >> debug-info.txt
   echo "=== Config Files ===" >> debug-info.txt
   ls -la ~/.config/claude_desktop/ >> debug-info.txt 2>/dev/null || ls -la ~/Library/Application\ Support/Claude/ >> debug-info.txt 2>/dev/null
   ```

3. **GitHub Issueでの報告**
   - リポジトリ: Kumihan-Formatter
   - タイトル: [Setup Kit] 具体的な問題内容
   - 内容: 症状・エラー・環境情報・試行した解決策

### サポート対象外

- 使い方の基本的な質問（ドキュメントを参照）
- 環境固有の設定カスタマイズ要求
- 未検証の機能に関する問題
- 他のプロジェクトでの利用に関する問題

---

**注意: このガイドは実際の問題報告と検証に基づいて作成されています。**  
**理論的な問題や未確認の症状は含まれていません。**

*Kumihan-Formatter Serena Setup Kit - Troubleshooting Guide v1.0*