# 技術的負債予防・対応ガイド

> **目的**: Issue #476対応の技術的負債予防ルール詳細
> **対象**: 300行制限、アーキテクチャ原則、自動チェック

## 📏 300行ルール（厳守）

- **ファイル**: 300行以内（例外なし）
- **クラス**: 100行以内推奨
- **関数**: 20行以内推奨
- **⚠️ 違反時**: pre-commit hookが自動でブロック

## 🏗️ アーキテクチャ原則

- **Single Responsibility Principle**: 1ファイル1責任
- **関数分割**: 複雑な処理は機能単位で分離
- **Boy Scout Rule**: コードを触ったら少しでも改善
- **循環依存**: 禁止（アーキテクチャチェックで検出）

## 🔧 自動チェック体制

```bash
# コミット時自動実行（pre-commit hook）
scripts/check_file_size.py      # ファイルサイズチェック
scripts/architecture_check.py   # アーキテクチャ品質チェック

# 手動実行（必要時のみ）
.venv/bin/python scripts/check_file_size.py
.venv/bin/python scripts/architecture_check.py
```

## ⚠️ pre-commit hookエラー対応

Claude Code使用時に以下のメッセージが表示される場合：
```
PreToolUse:Bash [~/.claude/hook_pre_commands.sh] failed with
non-blocking status code 1: No stderr output
```

**これは正常動作です。** status code 1は非ブロッキングエラーで、技術的負債の警告を表示しています。

### 📋 対応手順

1. **エラー内容を確認**
   ```bash
   python3 scripts/check_file_size.py --max-lines=300
   ```

2. **300行制限違反の修正**
   - ファイルを機能別に分割
   - Single Responsibility Principleに従う
   - 大きな関数・クラスを小さく分割

3. **修正例**
   ```bash
   # 違反ファイルの確認
   find kumihan_formatter -name "*.py" -exec wc -l {} + | awk '$1 > 300'

   # 分割実行（例）
   # large_file.py → feature_a.py + feature_b.py + feature_c.py
   ```

4. **修正後の確認**
   ```bash
   python3 scripts/check_file_size.py --max-lines=300
   # ✅ 違反件数が減少していることを確認
   ```

### 🚨 重要

- **status code 1は処理継続**: エラーではなく警告
- **無視しない**: 技術的負債の蓄積を防ぐため必ず対応
- **継続的改善**: Boy Scout Ruleに従って少しずつ改善

## 段階的品質向上戦略

- **新規実装**: 100%厳格品質チェック適用
- **既存コード**: 技術的負債を段階的に解決
- **レガシー除外**: `technical_debt_legacy_files.txt`で管理
- **段階的移行**: 既存ファイルは修正時に品質基準適用
