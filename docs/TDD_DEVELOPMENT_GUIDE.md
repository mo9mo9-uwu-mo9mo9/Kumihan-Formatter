# TDD-First開発システム実装マニュアル

> **Kumihan-Formatter TDD開発ガイド**  
> バージョン: 1.0.0 (2025-01-29)  
> 【根本改革】技術的負債根絶プロジェクト対応

## 🎯 TDD-First開発システムとは

Kumihan-Formatterプロジェクトでは、**テスト駆動開発（TDD）を強制**し、技術的負債を根絶するための完全統合開発システムを導入しています。

### 基本原則
1. **テストファースト**: 実装前に必ず失敗するテストを作成
2. **最小実装**: テストを通すための最小限のコードを実装
3. **継続的リファクタリング**: 品質向上を維持しながら改善
4. **品質ゲート強制**: カバレッジ90%以上必須
5. **セキュリティテスト100%**: 全セキュリティテスト必須パス

---

## 🚀 TDD開発フロー

### 1. TDDセッション開始

```bash
# Issue番号を指定してTDDセッションを開始
make tdd-start 640

# セッション状況確認
make tdd-status
```

**セッション開始時の自動処理**:
- `.tdd_session.json` ファイル作成
- Issue情報の記録
- TDDフェーズ管理開始
- 品質メトリクス初期化

### 2. テスト仕様書作成

```bash
# テスト仕様書テンプレート生成
make tdd-spec

# 生成されるファイル例
# - tests/unit/test_<feature_name>.py
# - docs/specs/<feature_name>_spec.md
```

**仕様書に含まれる要素**:
- Given-When-Then形式のテストケース
- 境界値テスト
- エラーハンドリングテスト
- セキュリティ考慮事項

### 3. Red Phase: 失敗するテストの作成

```bash
# Red Phase実行
make tdd-red
```

**Red Phaseの要件**:
- テストが確実に失敗することを確認
- テスト内容が要求仕様を正確に表現
- エッジケースを網羅
- 実行時間の記録

#### Red Phase実装例

```python
def test_convert_markdown_to_html():
    """
    Red Phase: まず失敗するテストを作成
    """
    # Given: Markdownテキスト
    markdown_text = "# タイトル\n\n本文です。"
    converter = MarkdownConverter()
    
    # When: HTML変換を実行
    result = converter.convert(markdown_text)
    
    # Then: 期待するHTML形式で出力される
    expected = "<h1>タイトル</h1>\n<p>本文です。</p>"
    assert result == expected  # 最初は失敗する
```

### 4. Green Phase: 最小実装

```bash
# Green Phase実行
make tdd-green
```

**Green Phaseの要件**:
- テストを通すための最小限の実装
- 過度な最適化は行わない
- 動作する最短のコード
- 全テストがパスすることを確認

#### Green Phase実装例

```python
class MarkdownConverter:
    """
    Green Phase: テストを通すための最小実装
    """
    def convert(self, markdown_text: str) -> str:
        # 最小実装: 固定値を返す
        if "# タイトル" in markdown_text:
            return "<h1>タイトル</h1>\n<p>本文です。</p>"
        return ""
```

### 5. Refactor Phase: 品質向上

```bash
# Refactor Phase実行
make tdd-refactor
```

**Refactor Phaseの要件**:
- テストを維持しながらコード品質向上
- パフォーマンス最適化
- 可読性・保守性向上
- セキュリティ強化

#### Refactor Phase実装例

```python
class MarkdownConverter:
    """
    Refactor Phase: 品質向上しながら機能拡張
    """
    def __init__(self):
        self._patterns = {
            r'^# (.+)$': r'<h1>\1</h1>',
            r'^## (.+)$': r'<h2>\1</h2>',
            r'^(.+)$': r'<p>\1</p>'
        }
    
    def convert(self, markdown_text: str) -> str:
        lines = markdown_text.strip().split('\n')
        html_lines = []
        
        for line in lines:
            if not line.strip():
                continue
                
            converted = self._convert_line(line)
            html_lines.append(converted)
        
        return '\n'.join(html_lines)
    
    def _convert_line(self, line: str) -> str:
        import re
        for pattern, replacement in self._patterns.items():
            if re.match(pattern, line):
                return re.sub(pattern, replacement, line)
        return f'<p>{line}</p>'
```

### 6. TDDサイクル完了

```bash
# TDDサイクル完了確認
make tdd-complete
```

**完了時の自動チェック**:
- Red → Green → Refactor履歴確認
- テストカバレッジ90%以上確認
- セキュリティテスト100%パス確認
- 品質ゲート全項目クリア確認

---

## 📊 品質基準とゲートシステム

### Critical Tier: 90%カバレッジ必須

```python
# コアシステム（Critical Tier）
CRITICAL_MODULES = [
    "kumihan_formatter.core.*",
    "kumihan_formatter.commands.*",
    "kumihan_formatter.parser",
    "kumihan_formatter.renderer",
]
```

### Important Tier: 80%カバレッジ推奨

```python
# 重要機能（Important Tier）
IMPORTANT_MODULES = [
    "kumihan_formatter.validators.*",
    "kumihan_formatter.config.*",
    "kumihan_formatter.ui.*",
]
```

### 品質ゲートチェック項目

1. **テストカバレッジ**
   - Critical Tier: ≥90%
   - Important Tier: ≥80%
   - Supportive Tier: 統合テストで代替可

2. **セキュリティテスト**
   - SQLインジェクション対策: 100%
   - XSS対策: 100%
   - CSRF対策: 100%
   - ファイルアップロードセキュリティ: 100%

3. **コード品質**
   - Black フォーマット: 100%準拠
   - isort インポート順序: 100%準拠
   - flake8 リント: エラー0件
   - mypy 型チェック: エラー0件

---

## 🔧 TDD専用ツール・コマンド

### Makefileコマンド一覧

```bash
# TDDセッション管理
make tdd-start <issue-number>    # TDDセッション開始
make tdd-status                  # セッション状況表示
make tdd-complete                # TDDサイクル完了

# TDD実行フェーズ
make tdd-spec                    # テスト仕様書生成
make tdd-red                     # Red Phase実行
make tdd-green                   # Green Phase実行
make tdd-refactor                # Refactor Phase実行

# 品質チェック
make test                        # テスト実行
make lint                        # リント・フォーマットチェック
make pre-commit                  # コミット前チェック
```

### TDD自動化スクリプト

```bash
# TDD関連スクリプト（scripts/ディレクトリ）
scripts/tdd_automation.py              # TDD自動化システム
scripts/tdd_cycle_manager.py           # TDDサイクル管理
scripts/tdd_session_manager.py         # TDDセッション管理
scripts/tdd_spec_generator.py          # TDD仕様生成
scripts/tdd_foundation.py              # TDD基盤システム
```

---

## 🛡️ セキュリティテスト統合

### 必須セキュリティテスト

1. **SQLインジェクション対策**
   ```bash
   python scripts/security_sql_injection_test.py
   ```

2. **XSS対策**
   ```bash
   python scripts/security_xss_test.py
   ```

3. **CSRF対策**
   ```bash
   python scripts/security_csrf_test.py
   ```

4. **ファイルアップロードセキュリティ**
   ```bash
   python scripts/security_file_upload_test.py
   ```

### セキュリティテスト実装パターン

```python
class SecurityTestBase:
    """セキュリティテスト基底クラス"""
    
    def test_sql_injection_protection(self):
        """SQLインジェクション対策テスト"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/**/OR/**/1=1/**/--",
        ]
        
        for malicious_input in malicious_inputs:
            result = self.target_function(malicious_input)
            # SQLインジェクションが成功していないことを確認
            self.assertNotIn("DROP", result.upper())
            self.assertNotIn("DELETE", result.upper())
    
    def test_xss_protection(self):
        """XSS対策テスト"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
        ]
        
        for payload in xss_payloads:
            result = self.render_function(payload)
            # XSSペイロードがエスケープされていることを確認
            self.assertNotIn("<script>", result)
            self.assertNotIn("javascript:", result)
```

---

## 🚦 GitHub Actions CI/CD統合

### TDD強制システム

TDD-First開発を強制するCI/CDシステムが自動実行されます：

1. **ci.yml**: 必須CI（Black/isort/flake8/pytest/mypy）
2. **tdd-enforcement.yml**: TDD強制システム
3. **quality-optional.yml**: 週次品質チェック

### マージブロック条件

以下の条件を満たさない場合、自動的にマージがブロックされます：

- ✅ TDDセッションが開始されている
- ✅ Red → Green → Refactor履歴が存在
- ✅ テストカバレッジ90%以上
- ✅ セキュリティテスト100%パス
- ✅ 全品質ゲートクリア

---

## 📋 TDD実装チェックリスト

### 開発開始前

- [ ] Issue作成・内容確認
- [ ] TDDセッション開始 (`make tdd-start <issue>`)
- [ ] テスト仕様書作成 (`make tdd-spec`)

### Red Phase

- [ ] 失敗するテスト作成
- [ ] テスト実行確認（必ず失敗）
- [ ] エッジケース網羅
- [ ] コミット（"Red: ..."）

### Green Phase  

- [ ] 最小実装でテスト成功
- [ ] 全テスト通過確認
- [ ] 過度な最適化回避
- [ ] コミット（"Green: ..."）

### Refactor Phase

- [ ] 品質向上実装
- [ ] テスト維持確認
- [ ] パフォーマンス最適化
- [ ] コミット（"Refactor: ..."）

### 完了前

- [ ] カバレッジ90%以上達成
- [ ] セキュリティテスト100%パス
- [ ] 品質ゲート全項目クリア
- [ ] TDDサイクル完了 (`make tdd-complete`)

---

## 🎓 TDD学習リソース

### 推奨学習順序

1. **TDD基礎概念理解**
   - Red-Green-Refactorサイクル
   - テストファーストの意義
   - 最小実装の重要性

2. **Kumihan-Formatter固有システム**
   - Makefileコマンド習得
   - セッション管理システム理解
   - 品質ゲートシステム理解

3. **実践的TDD開発**
   - 小さな機能でのTDD練習
   - セキュリティテスト統合
   - CI/CD連携確認

### よくある問題と解決策

#### Q: テストが複雑になりすぎる
A: Given-When-Then形式で分割し、1つのテストで1つの機能のみ検証

#### Q: カバレッジが上がらない
A: Critical Tierから優先的に実装し、段階的に向上

#### Q: Refactor Phaseで何をすべきか分からない
A: パフォーマンス・可読性・保守性・セキュリティの順で改善

---

## 🔗 関連ドキュメント

- [品質ゲート仕様](./QUALITY_GATES.md)
- [セキュリティテスト実装ガイド](./SECURITY_TESTING.md)
- [システム全体アーキテクチャ](./ARCHITECTURE.md)
- [開発ガイド](./dev/DEVELOPMENT_GUIDE.md)

---

**💡 重要**: このガイドは生きたドキュメントです。TDDシステムの改善と共に継続的に更新されます。