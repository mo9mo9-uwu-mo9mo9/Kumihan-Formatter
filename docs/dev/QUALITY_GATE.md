# 品質ゲート・詳細ガイド

> **目的**: Claude Code開発時の品質チェック体制の詳細仕様
> **対象**: 実装前チェック、品質保証、違反時対応

## 🚨 品質ゲート（絶対遵守）

### 実装前必須チェック

**Claude Code は実装作業前に以下を必ず実行すること：**

```bash
# 品質ゲートチェック（必須）
python scripts/claude_quality_gate.py

# 失敗した場合の修正
make pre-commit
```

### 🔒 絶対ルール（違反禁止）

#### 1. **mypy strict mode は絶対必須**
- `SKIP=mypy-strict` の使用は**絶対禁止**
- 型エラーが1個でもあるとコミット不可
- 実装前に必ず型安全性を確保

#### 2. **TDD（テスト駆動開発）の強制**
- **実装前にテストを書く**（Red-Green-Refactor）
- テストが存在しない機能の実装は禁止
- `python scripts/enforce_tdd.py kumihan_formatter/` で確認

#### 3. **品質チェック通過必須**
- Black, isort, flake8 の完全通過
- 全テストの成功
- アーキテクチャルールの遵守

## ⚡ 実装フロー（厳格遵守）

```bash
# 1. 品質ゲートチェック
python scripts/claude_quality_gate.py

# 2. テスト作成（RED）
# 新機能のテストを先に作成（失敗することを確認）

# 3. 最小実装（GREEN）
# テストが通る最小限の実装

# 4. リファクタリング（REFACTOR）
# テストを保持したまま改善

# 5. 最終確認
make pre-commit

# 6. コミット
git commit -m "..."
```

## 💥 違反時の対応

### 品質ゲート失敗時
```bash
🚨 Quality gate FAILED!
❌ The following checks failed:
   - mypy strict mode
   - TDD compliance

🛑 IMPLEMENTATION BLOCKED
```

**対応**:
1. エラーメッセージを必ず確認
2. 指摘された問題を完全に修正
3. 再度品質ゲートを実行
4. 成功するまで実装作業禁止

### 緊急時の例外処理
- 緊急時でも品質ゲートのスキップは**禁止**
- 問題の根本原因を修正してから進行
- 技術的負債の蓄積を防ぐ

## 🎯 品質保証の目標

- **型安全性**: 100% mypy strict mode 準拠
- **テストカバレッジ**: 新機能は必ずテスト付き
- **コード品質**: リンターエラー0個
- **アーキテクチャ**: 300行制限・単一責任原則
