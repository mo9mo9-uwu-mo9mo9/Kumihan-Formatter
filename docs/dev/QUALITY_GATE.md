# 品質ゲート・詳細ガイド（Issue #589更新）

> **目的**: Claude Code開発時の品質チェック体制の詳細仕様
> **対象**: 実装前チェック、品質保証、違反時対応
> **更新**: Issue #589でティア別品質システムに移行

## 🎯 新しい品質ゲートシステム（Issue #589対応）

### 実装前必須チェック

**Claude Code は実装作業前に以下を必ず実行すること：**

```bash
# ティア別品質ゲートチェック（新システム）
make quality-gate

# または直接実行
python scripts/tiered_quality_gate.py

# コミット前の統合チェック
make pre-commit
```

### 🔒 絶対ルール（違反禁止）

#### 1. **mypy strict mode は絶対必須**
- `SKIP=mypy-strict` の使用は**絶対禁止**
- 型エラーが1個でもあるとコミット不可
- 実装前に必ず型安全性を確保

#### 2. **ティア別品質基準（Issue #583対応）**
- **Critical Tier**: Core機能・Commands（テストカバレッジ80%目標）
- **Important Tier**: レンダリング・バリデーション（60%推奨）
- **Supportive Tier**: ユーティリティ・キャッシング（統合テストで代替可）
- **Special Tier**: GUI・パフォーマンス系（E2E・ベンチマークで代替）

#### 3. **品質チェック通過基準**
- Black, isort, flake8 の完全通過
- ティア別品質基準の達成
- アーキテクチャルールの遵守

## ⚡ 新実装フロー（Issue #589対応）

```bash
# 1. ティア別品質ゲートチェック
make quality-gate

# 2. ファイル分析・ティア確認
python scripts/gradual_improvement_planner.py

# 3. 実装作業
# Critical/Important Tierは厳格なテスト
# Supportive/Special Tierは現実的基準

# 4. 統合チェック
make pre-commit

# 5. コミット
git commit -m "..."
```

## 💥 違反時の対応

### ティア別品質ゲート結果（Issue #589新システム）
```bash
🎯 Tiered Quality Gate Results:
✅ Critical Tier: 90% coverage (target: 80%)
⚠️  Important Tier: 55% coverage (recommended: 60%)
✅ Supportive Tier: Integration tests passing
✅ Special Tier: Benchmark tests passing
```

**対応手順**:
1. ⚠️警告項目の段階的改善計画確認
2. Critical Tierの品質維持
3. Important Tierの改善推奨事項実行
4. 再度ティア別チェック実行

### GitHub Actions連携（Issue #602対応）
```bash
# CIでの自動チェック
✅ quality-check: 必須品質チェック
⚠️  quality-optional: 週次品質分析（参考）
✅ claude: Claude自動レビュー
```

## 🎯 段階的品質向上目標（Issue #583解決）

- **Critical Tier**: 80%カバレッジ維持（必須）
- **Important Tier**: 60%カバレッジ推奨
- **技術的負債**: ティア別改善で段階的解消
- **現実的基準**: 300行制限撤廃、実用性重視
- **アーキテクチャ**: 300行制限・単一責任原則
