# 品質ゲート仕様書

> **Kumihan-Formatter 品質管理システム**  
> バージョン: 1.0.0 (2025-01-29)  
> 【根本改革】段階的品質向上プロジェクト対応

## 🎯 品質ゲートシステム概要

Kumihan-Formatterでは、技術的負債を根絶し、持続可能な高品質ソフトウェア開発を実現するため、**段階的品質向上システム**を導入しています。

### 基本設計原則

1. **段階的改善**: 現実的な目標設定による継続的品質向上
2. **ティア別管理**: 機能重要度に応じた品質基準の階層化
3. **自動化強制**: 手動チェックの排除による品質担保
4. **CI/CD統合**: GitHub Actionsによる自動品質ゲート実行
5. **可視化重視**: 品質メトリクス明確化とトレンド分析

---

## 📊 ティア別品質基準

### Critical Tier（最重要層）- 90%カバレッジ必須

**対象モジュール**:
```python
CRITICAL_MODULES = [
    "kumihan_formatter.core.*",           # コアシステム
    "kumihan_formatter.commands.*",       # コマンドシステム
    "kumihan_formatter.parser",           # パーサー
    "kumihan_formatter.renderer",         # レンダラー
]
```

**品質要件**:
- ✅ **テストカバレッジ**: ≥90%（強制）
- ✅ **セキュリティテスト**: 100%パス必須
- ✅ **型チェック**: mypy strict mode 100%準拠
- ✅ **パフォーマンス**: ベンチマーク基準値維持

### Important Tier（重要層）- 80%カバレッジ推奨

**対象モジュール**:
```python
IMPORTANT_MODULES = [
    "kumihan_formatter.validators.*",     # バリデーション
    "kumihan_formatter.config.*",         # 設定管理
    "kumihan_formatter.ui.*",             # ユーザーインターフェース
]
```

**品質要件**:
- ✅ **テストカバレッジ**: ≥80%（推奨）
- ✅ **統合テスト**: 主要ユースケース網羅
- ✅ **エラーハンドリング**: 例外処理100%カバー

### Supportive Tier（支援層）- 統合テストで代替可

**対象モジュール**:
```python
SUPPORTIVE_MODULES = [
    "kumihan_formatter.utilities.*",      # ユーティリティ
    "kumihan_formatter.cache.*",          # キャッシング
    "kumihan_formatter.logging.*",        # ログ管理
]
```

**品質要件**:
- ✅ **統合テスト**: E2Eテストでの動作確認
- ✅ **ログ品質**: エラートレーサビリティ確保

### Special Tier（特殊層）- 専用テスト手法

**対象モジュール**:
```python
SPECIAL_MODULES = [
    "kumihan_formatter.gui.*",            # GUI機能
    "kumihan_formatter.performance.*",    # パフォーマンス最適化
]
```

**品質要件**:
- ✅ **E2Eテスト**: ユーザーシナリオベーステスト
- ✅ **ベンチマークテスト**: パフォーマンス基準値クリア

---

## 🚦 自動品質ゲートチェック

### 1. テストカバレッジゲート

```python
# scripts/coverage_gate_checker.py の実装例

def check_coverage_by_tier():
    """ティア別カバレッジチェック"""
    results = {}
    
    # Critical Tier: 90%必須
    critical_coverage = get_coverage_for_modules(CRITICAL_MODULES)
    results['critical'] = {
        'coverage': critical_coverage,
        'required': 90.0,
        'passed': critical_coverage >= 90.0
    }
    
    # Important Tier: 80%推奨
    important_coverage = get_coverage_for_modules(IMPORTANT_MODULES)
    results['important'] = {
        'coverage': important_coverage,
        'required': 80.0,
        'passed': important_coverage >= 80.0
    }
    
    return results
```

### 2. セキュリティゲート

```python
# セキュリティテスト必須項目
REQUIRED_SECURITY_TESTS = [
    'sql_injection_protection',
    'xss_protection', 
    'csrf_protection',
    'file_upload_security',
    'input_validation',
    'authentication_security'
]

def security_gate_check():
    """セキュリティゲートチェック"""
    passed_tests = 0
    total_tests = len(REQUIRED_SECURITY_TESTS)
    
    for test_name in REQUIRED_SECURITY_TESTS:
        if run_security_test(test_name):
            passed_tests += 1
    
    return {
        'pass_rate': (passed_tests / total_tests) * 100,
        'required_rate': 100.0,
        'passed': passed_tests == total_tests
    }
```

### 3. コード品質ゲート

```yaml
# .github/workflows/quality-gate.yml 品質チェック設定
code_quality_checks:
  - name: "Black Format Check"
    command: "python -m black --check --diff ."
    required: true
    
  - name: "isort Import Order"
    command: "python -m isort --check-only --diff ."
    required: true
    
  - name: "flake8 Linting"
    command: "python -m flake8 kumihan_formatter/ tests/ scripts/"
    required: true
    
  - name: "mypy Type Check"
    command: "python -m mypy kumihan_formatter/ --strict"
    required: true
```

---

## 📈 品質メトリクス測定

### 主要メトリクス

1. **テストカバレッジ率**
   - Line Coverage（行カバレッジ）
   - Branch Coverage（分岐カバレッジ）
   - Function Coverage（関数カバレッジ）

2. **コード複雑度**
   - Cyclomatic Complexity（循環的複雑度）
   - Cognitive Complexity（認知的複雑度）

3. **技術的負債指標**
   - Code Smells（コード臭）
   - Duplication Rate（重複率）
   - Maintainability Index（保守性指数）

### 測定自動化

```python
# scripts/quality_metrics_collector.py

class QualityMetricsCollector:
    def collect_all_metrics(self):
        """全品質メトリクスの収集"""
        return {
            'coverage': self._collect_coverage_metrics(),
            'complexity': self._collect_complexity_metrics(),
            'debt': self._collect_technical_debt_metrics(),
            'security': self._collect_security_metrics(),
            'performance': self._collect_performance_metrics()
        }
    
    def _collect_coverage_metrics(self):
        """カバレッジメトリクス収集"""
        result = subprocess.run(['pytest', '--cov-report=json'], 
                              capture_output=True, text=True)
        coverage_data = json.loads(result.stdout)
        
        return {
            'line_coverage': coverage_data['totals']['percent_covered'],
            'branch_coverage': coverage_data['totals']['percent_covered_display'],
            'missing_lines': coverage_data['totals']['missing_lines']
        }
```

---

## 🔧 品質ゲート実行システム

### GitHub Actions統合

```yaml
# .github/workflows/quality-gate-enforcement.yml

name: Quality Gate Enforcement

on:
  push:
    branches: [ "feat/*", "fix/*" ]
  pull_request:
    branches: [ main, develop ]

jobs:
  quality-gate-check:
    runs-on: ubuntu-latest
    steps:
      - name: Tier-based Coverage Check
        run: |
          python scripts/tiered_quality_gate.py
          
      - name: Security Gate Enforcement
        run: |
          python scripts/security_gate_checker.py
          
      - name: Code Quality Gate
        run: |
          make lint && make type-check
```

### ローカル実行コマンド

```bash
# 品質ゲート全項目チェック
make quality-gate

# ティア別品質チェック
python scripts/tiered_quality_gate.py

# セキュリティゲートチェック
python scripts/security_gate_checker.py

# 品質メトリクス収集
python scripts/quality_metrics_collector.py
```

---

## 📋 品質ゲート突破チェックリスト

### 開発者向けセルフチェック

**Critical Tier対応**:
- [ ] テストカバレッジ90%以上達成
- [ ] 全セキュリティテスト100%パス
- [ ] mypy strict mode準拠
- [ ] パフォーマンス基準値クリア

**Important Tier対応**:
- [ ] テストカバレッジ80%以上達成
- [ ] 統合テスト主要ケース網羅
- [ ] エラーハンドリング100%実装

**全ティア共通**:
- [ ] Black フォーマット100%準拠
- [ ] isort インポート順序100%準拠
- [ ] flake8 リントエラー0件
- [ ] CI/CD全ジョブ成功

### CI/CD自動チェック項目

```python
# 自動チェック項目定義
QUALITY_GATE_CHECKS = {
    'critical_coverage': {'threshold': 90.0, 'blocking': True},
    'important_coverage': {'threshold': 80.0, 'blocking': False},
    'security_tests': {'threshold': 100.0, 'blocking': True},
    'code_format': {'threshold': 100.0, 'blocking': True},
    'type_check': {'threshold': 100.0, 'blocking': True},
    'performance': {'threshold': 'baseline', 'blocking': True}
}
```

---

## 🎓 品質ゲート運用ガイド

### よくある問題と解決策

#### Q: Critical Tierのカバレッジが90%に届かない
**A**: 段階的改善アプローチを採用
1. 最重要機能から優先的にテスト追加
2. テスト自動生成ツールの活用
3. TDD-First開発への移行

#### Q: セキュリティテストが複雑すぎる
**A**: セキュリティテスト基底クラスの活用
1. `SecurityTestBase`クラスを継承
2. 共通パターンの再利用
3. セキュリティチェックリストの段階的実装

#### Q: 品質ゲートが開発速度を阻害する
**A**: 段階的導入とツール活用
1. ティア別導入（Critical → Important → Supportive）
2. 自動修正ツールの積極活用
3. 開発者教育とベストプラクティス共有

### 改善継続プロセス

1. **週次品質レビュー**
   - 品質メトリクス トレンド分析
   - ボトルネック特定と対策立案

2. **月次品質基準見直し**
   - ティア別基準の妥当性検証
   - 新技術導入に伴う基準更新

3. **四半期品質戦略検討**
   - 品質向上ロードマップ更新
   - ツール・プロセス改善計画

---

## 🔗 関連リソース

### 品質関連スクリプト
- `scripts/tiered_quality_gate.py` - ティア別品質ゲートチェック
- `scripts/quality_metrics_collector.py` - 品質メトリクス収集
- `scripts/gradual_improvement_planner.py` - 段階的改善計画
- `scripts/tdd_root_cause_analyzer.py` - 根本原因分析

### 関連ドキュメント
- [TDD開発システム実装マニュアル](./TDD_DEVELOPMENT_GUIDE.md)
- [セキュリティテスト実装ガイド](./SECURITY_TESTING.md)
- [システム全体アーキテクチャ](./ARCHITECTURE.md)
- [開発ガイド](./dev/DEVELOPMENT_GUIDE.md)

### 外部ツール・サービス
- **Codecov**: カバレッジ可視化とトレンド分析
- **SonarQube**: コード品質とセキュリティ分析
- **GitHub Actions**: CI/CDパイプライン自動実行

---

**💡 重要**: 品質ゲートは開発の障壁ではなく、高品質ソフトウェア開発を支援するツールです。段階的改善により、継続可能な品質向上を実現しましょう。