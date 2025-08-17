# Scripts - 便利なツール集

このディレクトリには、Kumihan-Formatterの開発・保守に役立つスクリプトが含まれています。

## 📁 スクリプト一覧

### 🧹 smart_cleanup.sh（推奨）
**目的**: しきい値チェック付きスマートメモリクリーンアップ

**自動実行**:
- `git commit`時にpre-commitフックで自動実行
- tmp/ディレクトリが20MB以上の場合のみ実行
- 静音モードで高速動作

**手動実行**:
```bash
# 基本実行（しきい値チェック付き）
./scripts/smart_cleanup.sh

# 強制実行（しきい値無視）
./scripts/smart_cleanup.sh --force

# 静音モード（git hook用）
./scripts/smart_cleanup.sh --quiet

# ログファイル出力
./scripts/smart_cleanup.sh --log logs/cleanup.log

# ヘルプ表示
./scripts/smart_cleanup.sh --help
```

### 🧹 cleanup_memory.sh（レガシー）
**目的**: 従来のメモリクリーンアップ（互換性維持）

**使い方**:
```bash
./scripts/cleanup_memory.sh
```

## 🎯 推奨使用方法

### 1. 自動実行（推奨）
`git commit`時に自動でスマートクリーンアップが実行されます：
```bash
git add .
git commit -m "変更をコミット"
# ↑ この時点で自動的にクリーンアップが実行される
```

### 2. 手動実行
必要に応じて手動でクリーンアップ：
```bash
# 通常のクリーンアップ
./scripts/smart_cleanup.sh

# 強制クリーンアップ
./scripts/smart_cleanup.sh --force
```

### 3. VS Code統合
`Cmd+Shift+P` → `Tasks: Run Task` → `Memory Cleanup`

## 🔧 しきい値について
- **デフォルト**: tmp/ディレクトリが20MB以上で実行
- **理由**: 小さなファイルでは実行時間の方が長くなるため
- **変更**: `scripts/smart_cleanup.sh`内の`THRESHOLD_MB`を編集

## 📊 何をクリーンアップするか
1. **大きな指示書ファイル**: 10KB以上の`.md`ファイル
2. **古い一時ファイル**: 7日以上前の`.md`、`.json`、`.txt`
3. **Pythonキャッシュ**: `__pycache__`ディレクトリ
4. **空のディレクトリ**: tmp/内の空フォルダ

## 💡 初心者向け補足
- **安全性**: ソースコードは削除されません
- **効率性**: 必要な時だけ自動実行
- **透明性**: 何を削除したか詳細表示

## 🔧 実行権限について
スクリプトには実行権限が必要です。もし権限エラーが出たら：
```bash
chmod +x scripts/cleanup_memory.sh
```

## 💡 ヒント
- スクリプト実行前にファイルをバックアップしたい場合は、事前に`git commit`しておくと安心です
- 実行結果は必ず確認して、想定通りにクリーンアップされたかチェックしましょう