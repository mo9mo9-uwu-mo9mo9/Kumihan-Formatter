# テスト品質ガイドライン

> **Kumihan-Formatter** - テスト肥大化防止のための品質基準  
> **Version**: 1.0 - Issue #1120対応版

---

## 🎯 目的

このガイドラインは、テストスイートの品質維持と将来的な肥大化防止を目的とする。
**テスト数の最適化**（2447→1421個）の成果を維持し、持続可能な開発環境を構築する。

---

## 📊 プロジェクト全体基準

### テスト量の上限管理
```yaml
# プロジェクト全体
total_test_methods: 1500個 (上限)
current_baseline: 1421個 (2025年8月時点)
growth_limit: 5% per quarter

# テスト/コード比率
test_to_code_ratio: 25-35% (理想範囲)
maximum_ratio: 40% (警告閾値)
```

### カテゴリ別配分基準
```yaml
# 主要カテゴリ上限（現状ベース + 20%バッファ）
unit_tests: 1450個 (95%)
  ├── unit/rendering: 130個 (9%)
  ├── unit/config: 100個 (7%)  
  ├── unit/ast_nodes: 100個 (7%)
  ├── unit/patterns: 95個 (6%)
  ├── unit/parsing: 80個 (5%)
  └── 其他unit: 945個 (63%)

integration_tests: 100個 (7%)
performance_tests: 50個 (3%)
system_tests: 30個 (2%)
```

---

## 🔍 テスト品質基準

### 1機能あたりのテスト数目安

#### シンプルな関数 (3-5個)
```python
# 推奨パターン
def test_simple_function():
    # 正常系 (1-2個)
    def test_parse_text_valid_input_returns_nodes():
        pass
        
    # 異常系 (1-2個)  
    def test_parse_text_empty_input_returns_empty():
        pass
        
    # エッジケース (0-1個、必要な場合のみ)
    def test_parse_text_large_input_handles_correctly():
        pass
```

#### 複雑なクラス (8-15個)
```python
# 推奨パターン
class TestComplexParser:
    # 初期化・設定 (2-3個)
    def test_parser_init_default_config():
        pass
        
    def test_parser_init_custom_config():
        pass
    
    # 主要機能 (4-6個)
    def test_parse_markdown_headers():
        pass
        
    def test_parse_markdown_lists():
        pass
    
    # エラーハンドリング (2-3個)
    def test_parse_invalid_syntax_raises_error():
        pass
    
    # 統合シナリオ (2-3個)
    def test_parse_complex_document_end_to_end():
        pass
```

### テスト密度の適正化

#### ❌ 避けるべきパターン
```python
# 過度な細分化
def test_function_case1():
def test_function_case2():
def test_function_case3():
# ... (20個以上)

# 重複テスト
def test_parse_text_in_unit():
def test_parse_text_in_integration():  # 同じ内容

# 不要なエッジケース
def test_parse_text_with_1000000_chars():  # 現実的でない
```

#### ✅ 推奨パターン
```python
# 適切な粒度
@pytest.mark.parametrize("input,expected", [
    ("case1", result1),
    ("case2", result2),
    ("case3", result3),
])
def test_function_various_inputs(input, expected):
    pass

# 統合的なテスト
def test_parse_text_comprehensive():
    # 複数のケースを1つのテストで効率的に検証
    pass
```

---

## 📝 テスト命名規約

### 基本パターン
```python
def test_[機能名]_[条件]_[期待結果]():
    """
    機能名: テスト対象の機能を明確に
    条件: テストの前提条件
    期待結果: 期待される動作・結果
    """
    pass
```

### 良い例
```python
def test_parse_markdown_with_headers_returns_ast_nodes():
    """markdownヘッダーを含むテキストがASTノードに変換されることを検証"""
    
def test_render_html_invalid_template_raises_template_error():
    """無効なテンプレートでHTMLレンダリング時にTemplateErrorが発生することを検証"""
    
def test_config_loader_missing_file_uses_defaults():
    """設定ファイル不在時にデフォルト設定が使用されることを検証"""
```

### 悪い例
```python
# ❌ 意味不明
def test_1():
def test_function():
def test_正常系():

# ❌ 長すぎる
def test_正常系_複雑な処理_エッジケース_特殊条件_例外処理():

# ❌ 曖昧
def test_parser():
def test_something():
```

---

## 🏗️ カテゴリ別ガイドライン

### Unit Tests
- **目的**: 個別機能の動作確認
- **上限**: 1450個
- **推奨比率**: 全体の95%
- **focus**: 境界値・エラーハンドリング・基本動作

### Integration Tests  
- **目的**: 複数コンポーネント間の連携確認
- **上限**: 100個
- **推奨比率**: 全体の7%
- **focus**: データフロー・API連携・設定読み込み

### Performance Tests
- **目的**: 性能要件の確認
- **上限**: 50個  
- **推奨比率**: 全体の3%
- **focus**: 実行時間・メモリ使用量・スケーラビリティ

### System/E2E Tests
- **目的**: システム全体の動作確認
- **上限**: 30個
- **推奨比率**: 全体の2%
- **focus**: ユーザーシナリオ・環境依存動作

---

## ⚙️ 自動品質チェック

### PR時の自動検証
```yaml
# CI実行時に自動チェック
✅ テスト総数上限 (1500個以下)
✅ カテゴリ別上限遵守
✅ 命名規約準拠
✅ 重複テスト検出
✅ テスト密度警告
```

### Pre-commit Hook
```bash
# ローカル実行時の即座チェック  
✅ 新規テストの命名確認
✅ カテゴリ別増加量チェック
✅ 品質基準準拠確認
```

### チェック実行例
```bash
# 手動実行
python3 scripts/test_quality_checker.py

# 出力例
📊 テスト品質レポート
====================
総テスト数: 1421/1500 (94.7%)
unit/rendering: 107/130 (82.3%)
unit/config: 85/100 (85.0%)
✅ 全基準内で正常
```

---

## 🚨 品質ゲート

### テスト追加時の判断基準

#### ✅ 追加推奨
- 新機能の基本動作確認
- 重要なエラーハンドリング
- セキュリティ・データ整合性関連
- ユーザー影響の大きい機能

#### ⚠️ 慎重に検討
- 既存テストでカバー可能な機能
- 非常に稀なエッジケース
- 内部実装の詳細に依存するテスト
- 保守コストが高いテスト

#### ❌ 追加非推奨
- 同じ機能の重複テスト
- 現実的でない境界値テスト
- フレームワーク・ライブラリのテスト
- 過度に複雑で脆いテスト

---

## 📈 継続的改善プロセス

### 月次品質レビュー
```yaml
実施頻度: 毎月第1営業日
確認項目:
  - テスト品質指標の確認
  - カテゴリ別分布の妥当性検証
  - 失敗しやすいテストの特定
  - 実行時間の推移確認
```

### 四半期基準見直し
```yaml
実施頻度: 四半期末
見直し項目:
  - プロジェクト成長に応じた上限調整
  - 新ベストプラクティスの反映
  - 自動チェック機能の改善
  - ガイドライン実用性の評価
```

---

## 🛠️ 実用的な FAQ

### Q1. テスト上限に近づいた場合の対処法
**A**: 以下の順序で対処を検討
1. 既存テストの重複・不要分を削除
2. パラメータ化による統合
3. カテゴリ別配分の見直し
4. 必要に応じて上限調整（要議論）

### Q2. 複雑な機能のテスト数が多くなる場合
**A**: 機能を小さく分割し、各部分の責務を明確化。
統合テストで全体動作を確認し、Unit Testは個別責務のみに集中。

### Q3. レガシーコードのテスト追加基準
**A**: リファクタリングと併行し、重要度・変更頻度・影響範囲を基準に優先順位付け。
全てをカバーしようとせず、クリティカルパスを重点的にテスト。

### Q4. パフォーマンステストの扱い
**A**: 継続的実行の負荷を考慮し、日次実行・週次実行等で分離。
CI時間に影響しない範囲で実行し、回帰検出を重視。

---

## 📋 チェックリスト

### テスト追加前
- [ ] 既存テストで同様の機能をカバーしていないか確認
- [ ] テスト対象の責務が明確か確認  
- [ ] カテゴリ別上限に余裕があるか確認
- [ ] 命名規約に準拠しているか確認

### テスト作成時
- [ ] テスト名が機能・条件・期待結果を明確に表現
- [ ] テストの独立性が保たれている
- [ ] 適切な粒度でテストを分割
- [ ] 必要最小限のセットアップ・クリーンアップ

### PR作成時
- [ ] 自動品質チェックをパス
- [ ] テスト追加理由が明確
- [ ] 既存テストとの重複がない
- [ ] ドキュメント更新（必要に応じて）

---

**🎯 このガイドラインにより、テスト品質を維持しながら持続可能な開発環境を構築します。**

*作成日: 2025年8月 | 対応Issue: #1120 | Version: 1.0*