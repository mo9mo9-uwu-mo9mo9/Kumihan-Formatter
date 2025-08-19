# Kumihan-Formatter 貢献ガイド

> **オープンソース貢献への包括的ガイド**  
> **Status**: Active Development - Phase 4対応版  
> **最終更新**: 2025-08-19

---

## 📋 目次

- [概要](#概要)
- [貢献の種類](#貢献の種類)
- [開発環境のセットアップ](#開発環境のセットアップ)
- [コーディング規約](#コーディング規約)
- [開発ワークフロー](#開発ワークフロー)
- [テスト手順](#テスト手順)
- [プルリクエスト手順](#プルリクエスト手順)
- [レビュープロセス](#レビュープロセス)
- [Phase 4 開発指針](#phase-4-開発指針)
- [Claude-Gemini協業ガイド](#claude-gemini協業ガイド)
- [よくある質問](#よくある質問)

---

## 概要

Kumihan-Formatterは、独自の記法システム（Kumihan記法）を用いた日本語テキストフォーマッターです。本プロジェクトへの貢献を歓迎し、あらゆるレベルの開発者が参加できる環境を提供しています。

### プロジェクト特徴

- **技術スタック**: Python 3.12+, Black, isort, mypy (strict)
- **記法システム**: Kumihan独自ブロック記法 (`# 装飾名 #内容##`)
- **品質重視**: 3層品質検証システム（構文→品質→人的レビュー）
- **日本語メイン**: コメント・ドキュメント・レビューは日本語
- **Claude-Gemini協業**: AI協業による効率的開発体制

---

## 貢献の種類

### コードコントリビューション

#### 🟢 新機能開発
- **対象**: 記法拡張、レンダリング機能追加、パフォーマンス向上
- **要件**: Issue作成 → 設計議論 → 実装 → テスト → PR
- **例**: 新しいKumihan記法要素の追加、HTML出力オプション拡張

#### 🔵 バグ修正
- **対象**: 記法解析エラー、レンダリング不具合、パフォーマンス問題
- **要件**: 再現手順確認 → 原因分析 → 修正 → テスト → PR
- **例**: 特定記法の解析失敗、HTML出力の文字化け修正

#### 🟡 パフォーマンス改善
- **対象**: 処理速度向上、メモリ使用量最適化
- **要件**: ベンチマーク測定 → ボトルネック分析 → 最適化 → 性能検証
- **例**: 大容量ファイル処理の高速化、並列処理導入

#### 🟠 セキュリティ強化（Phase 4対応）
- **対象**: 脆弱性対応、セキュアコーディング、監査機能
- **要件**: セキュリティレビュー → 実装 → 脆弱性テスト → 承認
- **例**: XSS対策強化、入力値検証改善、ログ監査機能

### ドキュメント貢献

#### 📖 技術文書
- **対象**: API文書、アーキテクチャ文書、設計仕様書
- **要件**: 技術理解 → 文書作成 → レビュー → 更新
- **例**: 新機能のAPI文書作成、システム設計図更新

#### 📚 ユーザーガイド
- **対象**: 使用手順、チュートリアル、サンプルコード
- **要件**: ユーザー視点 → 手順作成 → 動作確認 → 公開
- **例**: 初心者向けチュートリアル、記法使用例集

#### 🔧 API文書
- **対象**: コード文書、docstring、サンプルコード
- **要件**: コード理解 → 文書化 → 例示作成 → テスト
- **例**: 関数・クラスのdocstring追加、使用例の充実

### その他貢献

#### 🐛 Issue報告
- **対象**: バグ報告、機能要求、改善提案
- **要件**: 現象確認 → 環境情報収集 → Issue作成 → 議論参加
- **例**: 記法解析エラーの報告、新機能の提案

#### 🌐 翻訳
- **対象**: 英語文書、国際化対応
- **要件**: 言語能力 → 翻訳作業 → レビュー → 更新
- **例**: README英語版作成、エラーメッセージ多言語化

#### 👥 コミュニティ
- **対象**: 質問回答、議論参加、新規貢献者支援
- **要件**: プロジェクト理解 → 積極的参加 → 知識共有
- **例**: Issueでの技術議論、新規コントリビューターのメンタリング

---

## 開発環境のセットアップ

### 基本環境要件

#### システム要件
```bash
# Python 3.12以上（必須）
python3 --version  # Python 3.12.x 確認

# Git（最新版推奨）
git --version

# 推奨エディタ
# - VS Code with Python extension
# - PyCharm
# - Any editor with Python support
```

#### プロジェクト取得・設定
```bash
# 1. リポジトリのフォーク（GitHub上で実行）
# https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter をフォーク

# 2. ローカルクローン
git clone https://github.com/YOUR_USERNAME/Kumihan-Formatter.git
cd Kumihan-Formatter

# 3. アップストリーム設定
git remote add upstream https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git

# 4. 開発環境セットアップ
pip install -e ".[dev]"

# 5. pre-commitフック設定
pre-commit install

# 6. 動作確認
make test
make lint
```

### 開発ツール設定

#### VS Code設定例
```json
{
    "python.defaultInterpreter": "python3",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.provider": "isort",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true
}
```

#### 必須拡張機能
- Python (Microsoft)
- Python Docstring Generator
- GitLens
- Todo Tree
- Error Lens

### Phase 4 セキュリティ開発環境

#### セキュリティ開発ツール
```bash
# セキュリティ検査ツール
pip install bandit safety

# 脆弱性チェック
bandit -r kumihan_formatter/
safety check

# セキュリティテスト環境
pip install pytest-security
```

#### ローカル監視システム
```bash
# ログ監視設定
tail -f tmp/logs/security.log

# パフォーマンス監視
python3 tools/monitor_performance.py
```

---

## コーディング規約

### Python コーディングスタンダード

#### 基本スタイル
- **フォーマット**: Black (line-length=88, 自動適用)
- **インポート**: isort設定準拠（自動適用）
- **型注釈**: mypy strict mode必須
- **エンコーディング**: UTF-8統一
- **Python版**: 3.12以上使用

#### コード品質チェック
```bash
# 必須実行コマンド
make lint      # Black, isort, flake8, mypy
make test      # pytest全テスト
make typecheck # 型チェック

# 個別実行
black .        # コードフォーマット
isort .        # インポート整理
flake8         # コード品質
mypy .         # 型チェック
```

#### 型注釈規約
```python
# ✅ 推奨例
from typing import List, Dict, Optional, Union
from pathlib import Path

def process_file(
    file_path: Path,
    options: Dict[str, str],
    output_format: Optional[str] = None
) -> List[str]:
    """ファイル処理関数
    
    Args:
        file_path: 処理対象ファイルパス
        options: 処理オプション辞書
        output_format: 出力形式（オプション）
    
    Returns:
        処理結果のリスト
    
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: 無効なオプション指定の場合
    """
    # 実装...
```

### プロジェクト固有規約

#### ファイル出力管理（絶対遵守）
```python
# ✅ 正しい実装: tmp/配下への出力
from pathlib import Path

def save_output(content: str, filename: str) -> None:
    """出力ファイルをtmp/配下に保存"""
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    output_path = tmp_dir / filename
    with output_path.open("w", encoding="utf-8") as f:
        f.write(content)

# ❌ 違反例: プロジェクトルート直下出力
def bad_save(content: str) -> None:
    with open("output.txt", "w") as f:  # 絶対禁止
        f.write(content)
```

#### ログ使用
```python
# ✅ 必須: 統一ロガー使用
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

def some_function():
    logger.info("処理開始")
    try:
        # 処理...
        logger.debug("詳細処理情報")
    except Exception as e:
        logger.error(f"エラー発生: {e}")
        raise
```

#### エラーハンドリング
```python
# ✅ 推奨: 具体的な例外処理
def safe_operation() -> bool:
    try:
        result = risky_operation()
        return True
    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {e}")
        return False
    except ValueError as e:
        logger.error(f"値エラー: {e}")
        return False
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        raise
```

### Phase 4 セキュリティコーディング

#### セキュアコーディングパターン
```python
import html
from pathlib import Path
from typing import Any

def secure_html_output(content: str) -> str:
    """XSS対策を施したHTML出力"""
    # HTMLエスケープ処理
    escaped_content = html.escape(content, quote=True)
    
    # ログ記録（監査用）
    logger.info(f"HTML出力処理: {len(content)}文字")
    
    return escaped_content

def validate_input(data: Any) -> bool:
    """入力値検証"""
    if not isinstance(data, str):
        logger.warning(f"無効な入力タイプ: {type(data)}")
        return False
    
    if len(data) > 10000:  # サイズ制限
        logger.warning(f"入力サイズ過大: {len(data)}文字")
        return False
    
    return True
```

---

## 開発ワークフロー

### ブランチ管理

#### ブランチ命名規則
```bash
# 必須形式
{type}/issue-{番号}-{英語概要}

# 例
feat/issue-123-add-security-validation
fix/issue-456-memory-leak-renderer
docs/issue-789-update-contribution-guide
test/issue-012-integration-test-suite
```

#### ブランチタイプ
- **feat**: 新機能追加
- **fix**: バグ修正
- **docs**: ドキュメント更新
- **style**: コードスタイル修正
- **refactor**: リファクタリング
- **test**: テスト追加・修正
- **chore**: その他の変更

#### 開発フロー
```bash
# 1. 最新のmainブランチに同期
git checkout main
git pull upstream main

# 2. 新しいブランチ作成
git checkout -b feat/issue-123-new-feature

# 3. 開発・コミット
git add .
git commit -m "feat: 新機能実装

- 機能Aの実装
- テストケース追加
- ドキュメント更新

Closes #123"

# 4. プッシュ
git push origin feat/issue-123-new-feature

# 5. プルリクエスト作成
gh pr create --title "新機能: 機能A実装" --body "詳細説明..."
```

### Issue・PR管理

#### Issue作成
```bash
# バグ報告
gh issue create \
  --title "バグ: 記法解析エラー" \
  --body "## 現象
記法XXXが正しく解析されない

## 再現手順
1. XXXファイルを開く
2. YYYコマンド実行
3. エラー発生

## 期待する動作
正常に解析される

## 環境
- OS: macOS 14
- Python: 3.12.1" \
  --label "bug"

# 機能要求
gh issue create \
  --title "機能要求: 新記法サポート" \
  --body "## 概要
新しい記法XXXをサポートしたい

## 詳細
...

## 用途
..." \
  --label "enhancement"
```

### コミットメッセージ

#### 推奨形式
```
{type}: {概要}

{詳細説明}

{追加情報}
```

#### コミット例
```bash
git commit -m "feat: HTML出力にセキュリティ機能追加

- XSS対策としてHTMLエスケープ処理実装
- CSP（Content Security Policy）ヘッダー対応
- 入力値検証の強化

Phase 4セキュリティ要件に対応
Closes #922"
```

---

## テスト手順

### テスト実行

#### 基本テスト
```bash
# 全テスト実行
make test

# カバレッジ付きテスト
pytest --cov=kumihan_formatter --cov-report=html

# 特定のテストのみ
pytest tests/unit/test_parser.py::TestParser::test_basic_parsing

# 並列実行（高速化）
pytest -n auto
```

#### テストカテゴリー別実行
```bash
# 単体テスト
pytest tests/unit/

# 統合テスト
pytest tests/integration/

# パフォーマンステスト
pytest tests/performance/

# 手動テスト用データ確認
ls tests/manual/
```

### テスト作成指針

#### 単体テスト例
```python
import pytest
from kumihan_formatter.core.parser import KumihanParser

class TestKumihanParser:
    """Kumihanパーサーテストクラス"""
    
    def setup_method(self):
        """テスト前準備"""
        self.parser = KumihanParser()
    
    def test_basic_parsing(self):
        """基本的な記法解析テスト"""
        # Given
        input_text = "#太字# 強調文字 ##"
        
        # When
        result = self.parser.parse(input_text)
        
        # Then
        assert result is not None
        assert result.type == "bold"
        assert result.content == "強調文字"
    
    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # Given
        invalid_input = "#未対応記法# 内容 ##"
        
        # When & Then
        with pytest.raises(ValueError, match="未対応の記法"):
            self.parser.parse(invalid_input)
    
    @pytest.mark.parametrize("input_text,expected", [
        ("#太字# テスト ##", "bold"),
        ("#斜体# テスト ##", "italic"),
        ("#下線# テスト ##", "underline"),
    ])
    def test_multiple_notations(self, input_text: str, expected: str):
        """複数記法のパラメータ化テスト"""
        result = self.parser.parse(input_text)
        assert result.type == expected
```

#### セキュリティテスト（Phase 4対応）
```python
import pytest
from kumihan_formatter.core.rendering.security import SecurityRenderer

class TestSecurityRenderer:
    """セキュリティレンダリングテスト"""
    
    def test_xss_prevention(self):
        """XSS対策テスト"""
        # Given
        malicious_input = "<script>alert('xss')</script>"
        renderer = SecurityRenderer()
        
        # When
        result = renderer.render_safe(malicious_input)
        
        # Then
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_large_input_handling(self):
        """大容量入力処理テスト"""
        # Given
        large_input = "A" * 100000
        renderer = SecurityRenderer()
        
        # When & Then
        # メモリリークがないことを確認
        result = renderer.render_safe(large_input)
        assert len(result) <= len(large_input) * 2  # エスケープによる増加を考慮
```

### パフォーマンステスト
```python
import time
import pytest
from kumihan_formatter.core.parser import KumihanParser

class TestPerformance:
    """パフォーマンステスト"""
    
    @pytest.mark.performance
    def test_large_file_processing(self):
        """大容量ファイル処理性能テスト"""
        # Given
        large_content = "#太字# 内容 ##\n" * 10000
        parser = KumihanParser()
        
        # When
        start_time = time.time()
        result = parser.parse(large_content)
        end_time = time.time()
        
        # Then
        processing_time = end_time - start_time
        assert processing_time < 5.0  # 5秒以内で完了
        assert len(result) == 10000  # 全項目処理
```

---

## プルリクエスト手順

### PR作成前チェックリスト

#### 必須項目
- [ ] ブランチ名が英語で命名規則に従っている
- [ ] `make lint` が通る（コード品質）
- [ ] `make test` が通る（全テスト）
- [ ] 型チェック（mypy）が通る
- [ ] ファイルが適切な場所に配置されている（tmp/配下等）
- [ ] 関連するIssueが存在する
- [ ] CHANGELOG.mdを更新した（機能追加/変更の場合）

#### Phase 4追加項目
- [ ] セキュリティテストが通る
- [ ] パフォーマンステストが通る
- [ ] ログ出力が適切に設定されている
- [ ] 脆弱性チェック（bandit）が通る

#### プルリクエスト作成
```bash
# GitHub CLI使用
gh pr create \
  --title "feat: 新しいセキュリティ機能実装" \
  --body "$(cat <<EOF
## 概要
XSS対策とCSP対応を実装しました。

## 変更内容
- [ ] HTMLエスケープ処理の実装
- [ ] CSPヘッダー対応
- [ ] 入力値検証強化
- [ ] セキュリティテスト追加

## 関連Issue
Closes #922

## テスト
- [ ] 単体テストを追加/更新
- [ ] セキュリティテストで動作確認
- [ ] パフォーマンス影響確認

## Phase 4対応
- [x] セキュリティ要件満足
- [x] 監査ログ出力対応
- [x] 脆弱性テスト実行

## レビューポイント
- セキュリティ実装の妥当性
- パフォーマンスへの影響
- テストカバレッジの充実度
EOF
)"
```

### PR説明テンプレート
```markdown
## 概要
変更の概要を簡潔に記載

## 変更内容
- [ ] 変更点1
- [ ] 変更点2
- [ ] 変更点3

## 関連Issue
Closes #XXX
Related to #YYY

## テスト
- [ ] 単体テストを追加/更新
- [ ] 統合テストで動作確認
- [ ] 手動テストで確認

## スクリーンショット・ログ
（該当する場合）

## Phase 4関連（セキュリティ機能の場合）
- [ ] セキュリティ要件対応
- [ ] 脆弱性テスト実行
- [ ] 監査ログ実装

## レビューポイント
- 実装方式の妥当性
- パフォーマンスへの影響
- セキュリティ観点での確認

## 備考
その他の注意事項
```

---

## レビュープロセス

### レビュー基準

#### コード品質観点
1. **機能性**: 要求仕様を満たしているか
2. **可読性**: コードが理解しやすいか
3. **保守性**: 将来の変更に対応しやすいか
4. **効率性**: パフォーマンスに問題はないか
5. **安全性**: セキュリティリスクはないか

#### Phase 4セキュリティ観点
1. **入力検証**: 全ての入力値が適切に検証されているか
2. **出力エスケープ**: XSS等の脆弱性対策が実装されているか
3. **エラーハンドリング**: セキュリティ情報の漏洩がないか
4. **ログ出力**: 監査に必要な情報が記録されているか
5. **アクセス制御**: 適切な権限管理が行われているか

### レビューコメント例

#### 建設的なレビュー
```markdown
# ✅ 良い例
この実装は要求を満たしていますが、以下の点で改善できそうです：

1. **パフォーマンス**: 
   - L25で配列のコピーが発生していますが、generator使用で最適化できませんか？
   
2. **エラーハンドリング**:
   - `ValueError`の代わりにより具体的な`InvalidNotationError`を定義すると良いでしょう
   
3. **テストカバレッジ**:
   - エッジケース（空文字列入力）のテストがあると安心です

## 提案コード
\```python
# generator使用例
def optimized_process(items):
    for item in items:
        yield process_item(item)
\```

レビューありがとうございました！
```

#### 修正が必要な場合
```markdown
# 🔄 修正要求
以下の重要な問題があるため、修正をお願いします：

1. **セキュリティ問題**（重要）:
   - L45でHTMLエスケープされていません → XSS脆弱性の可能性
   
2. **品質問題**:
   - `make lint`でflake8エラーが発生しています
   - 型注釈が不足しています（L12, L34）
   
3. **テスト**:
   - 新機能に対するテストケースが不足しています

修正後に再レビューします。ご質問があれば遠慮なくどうぞ！
```

### 日本語レビュー必須規則

#### 基本原則
- **全てのレビューコメントは日本語で記載**
- 技術用語は適切な日本語化または併記
- 建設的で丁寧な表現を心がける

#### 良い日本語レビュー例
```markdown
# ✅ 推奨
「このメソッドでメモリリークの可能性があります。
try-finallyブロックでリソース解放を確実にしませんか？」

# ❌ 非推奨
「Potential memory leak in this method」
```

---

## Phase 4 開発指針

### セキュリティ機能開発

#### セキュリティ要件
1. **入力検証**: 全入力の妥当性確認
2. **出力エスケープ**: XSS対策の確実な実装
3. **エラーハンドリング**: 情報漏洩の防止
4. **監査ログ**: セキュリティイベントの記録
5. **アクセス制御**: 適切な権限管理

#### 実装パターン
```python
# セキュリティ実装例
from kumihan_formatter.core.security import SecurityValidator, AuditLogger

class SecureRenderer:
    def __init__(self):
        self.validator = SecurityValidator()
        self.audit_logger = AuditLogger()
    
    def render_safe(self, content: str) -> str:
        # 1. 入力検証
        if not self.validator.validate_input(content):
            self.audit_logger.log_security_event(
                "invalid_input", 
                {"content_length": len(content)}
            )
            raise SecurityError("無効な入力です")
        
        # 2. 処理実行
        result = self._process_content(content)
        
        # 3. 出力エスケープ
        safe_result = self.validator.escape_output(result)
        
        # 4. 監査ログ
        self.audit_logger.log_security_event(
            "safe_render", 
            {"input_length": len(content), "output_length": len(safe_result)}
        )
        
        return safe_result
```

### パフォーマンス最適化

#### 最適化対象
- **メモリ使用量**: 大容量ファイル処理の効率化
- **処理速度**: パースパフォーマンスの向上
- **並列処理**: CPUコア活用の最適化
- **キャッシュ**: 処理結果の効率的キャッシュ

#### 監視・測定
```python
# パフォーマンス測定例
import time
import tracemalloc
from kumihan_formatter.core.utilities.performance import PerformanceMonitor

def measure_performance(func):
    def wrapper(*args, **kwargs):
        # メモリ監視開始
        tracemalloc.start()
        start_time = time.time()
        
        # 関数実行
        result = func(*args, **kwargs)
        
        # 測定結果
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # ログ記録
        PerformanceMonitor.log_metrics({
            "function": func.__name__,
            "execution_time": end_time - start_time,
            "memory_peak": peak / 1024 / 1024,  # MB
            "memory_current": current / 1024 / 1024  # MB
        })
        
        return result
    return wrapper
```

---

## Claude-Gemini協業ガイド

### 協業システム概要

#### 責任分担
- **Claude**: 要件分析・設計・品質レビュー・最終責任
- **Gemini**: 実装作業・コード修正・Task tool実行

#### Token節約戦略（90%削減目標）
- **モデル選択**: gemini-2.5-flash使用
- **効率実行**: Task toolによる1回完了
- **品質維持**: Claude最終レビューで品質保証

### 協業フロー

#### 基本フロー
1. **ユーザー要求** → Claude要件分析
2. **Claude指示書作成** → Gemini実装タスク作成
3. **Gemini実装** → Task tool実行
4. **Claude品質レビュー** → 最終品質チェック
5. **完成・統合** → プロジェクト反映

#### タスク難易度判定

##### 🟢 SIMPLE（Gemini推奨）
- **対象**: 設定ファイル、テンプレート、ドキュメント
- **成功率**: 90%以上
- **例**: YAML設定、Markdown文書、HTMLテンプレート

##### 🟡 MODERATE（分割検討）
- **対象**: ビジネスロジック、API統合、テスト実装
- **戦略**: 2ファイル以下に分割してGemini適用
- **例**: データ処理ロジック、REST API クライアント

##### 🔴 COMPLEX（Claude必須）
- **対象**: メモリ管理、セキュリティ、並行処理、最適化
- **理由**: 高度な技術知識・判断が必要
- **例**: マルチスレッド処理、暗号化機能、メモリ最適化

### 協業実行方法

#### Gemini協業起動キーワード
```markdown
# 自動起動キーワード
- "Geminiと協業"
- "Gemini協業"
- "一緒に"
- "🤖 Gemini協業"
```

#### 指示書テンプレート
```markdown
## 🤖 Gemini協業タスク: [タスク名]

### 実装仕様
以下のファイルを実装してください：

**ファイル**: `/path/to/target/file.py`

### 要件
1. **機能要件**: 具体的な機能説明
2. **技術要件**: 使用技術・ライブラリ
3. **品質要件**: テスト・検証基準

### 実装パターン
\```python
# 期待するコード構造例
class ExampleClass:
    def example_method(self) -> str:
        return "example"
\```

### 品質基準
- Python 3.12+ 対応
- Type hints 必須
- docstring 記述
- エラーハンドリング実装
```

---

## よくある質問

### 🔧 技術関連

#### Q: Python環境の設定がうまくいきません
A: 以下を確認してください：
```bash
# Python バージョン確認
python3 --version  # 3.12以上必要

# 仮想環境作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -e ".[dev]"
```

#### Q: テストが失敗します
A: 段階的に確認してください：
```bash
# 1. 環境確認
python3 --version
pip list | grep pytest

# 2. 個別テスト実行
pytest tests/unit/test_parser.py -v

# 3. ログ確認
pytest --log-cli-level=DEBUG

# 4. キャッシュクリア
pytest --cache-clear
```

#### Q: 型チェック（mypy）エラーが解決できません
A: 段階的に対応してください：
```python
# 1. 基本的な型注釈追加
def function_name(param: str) -> int:
    return len(param)

# 2. Optional型の使用
from typing import Optional
def may_return_none() -> Optional[str]:
    return None

# 3. 複雑な型の場合
from typing import List, Dict, Union
def complex_function(items: List[str]) -> Dict[str, Union[int, str]]:
    return {"count": len(items), "first": items[0] if items else ""}
```

### 📋 プロセス関連

#### Q: どのIssueから始めればよいですか？
A: 経験レベル別の推奨：

**初心者向け**
- ラベル「good first issue」
- ドキュメント修正
- 簡単なバグ修正

**中級者向け**
- 新機能実装
- テスト追加
- リファクタリング

**上級者向け**
- アーキテクチャ改善
- パフォーマンス最適化
- セキュリティ強化（Phase 4）

#### Q: ブランチ名の付け方がわかりません
A: 以下のパターンを使用してください：
```bash
# 機能追加
feat/issue-123-add-new-notation

# バグ修正  
fix/issue-456-parser-memory-leak

# ドキュメント
docs/issue-789-update-readme

# テスト
test/issue-012-integration-coverage

# Phase 4関連
feat/issue-922-security-validation
```

#### Q: PRのレビューで指摘を受けました。どう対応すれば？
A: 建設的に対応してください：

1. **指摘を理解する**
   - 不明な点は質問で確認
   - 提案の背景を理解

2. **修正を実行する**
   ```bash
   # 修正実行
   git add .
   git commit -m "fix: レビュー指摘対応 - XSS対策強化"
   git push origin feature-branch
   ```

3. **コミュニケーション**
   - 修正完了をコメント
   - 追加質問があれば記載

### 🤖 Claude-Gemini協業関連

#### Q: Gemini協業はいつ使うべきですか？
A: 以下の条件で活用してください：

**使用推奨**
- 1000 token以上の節約が見込める
- 設定ファイル・ドキュメント作成
- 定型的なコード実装
- テンプレート作成

**使用非推奨**
- セキュリティ関連コード
- 複雑なアルゴリズム
- メモリ管理が重要な処理

#### Q: Gemini実行で品質が気になります
A: 3層品質検証で安心してください：

1. **Layer 1**: 構文検証（自動）
2. **Layer 2**: 品質検証（`make lint`, `make test`）
3. **Layer 3**: Claude最終承認（人的レビュー）

### 🔒 Phase 4セキュリティ関連

#### Q: セキュリティ機能開発の注意点は？
A: 以下を重視してください：

1. **セキュアコーディング**
   - 入力検証の実装
   - 出力エスケープの確実な適用
   - エラー情報漏洩の防止

2. **テスト充実**
   - セキュリティテストの追加
   - 脆弱性テストの実行
   - エッジケースの確認

3. **監査対応**
   - ログ出力の実装
   - セキュリティイベント記録
   - トレーサビリティ確保

#### Q: パフォーマンステストの基準は？
A: 以下を目標としてください：

```python
# 処理速度基準
- 小容量（1KB）: 10ms以内
- 中容量（100KB）: 1s以内  
- 大容量（10MB）: 10s以内

# メモリ使用量
- 入力サイズの3倍以内
- ピーク使用量100MB以内
- メモリリーク無し
```

### 🌐 コミュニティ関連

#### Q: 日本語でのコミュニケーションの理由は？
A: プロジェクトの方針です：

- **理解促進**: メンバー全員の技術理解向上
- **品質向上**: 詳細な技術議論の実現
- **知識共有**: 日本語での技術文書蓄積

#### Q: 英語での貢献は可能ですか？
A: コードは問題ありませんが、以下は日本語でお願いします：

- Issue・PR説明
- コードレビュー
- ドキュメント作成
- 技術議論

---

## 📚 関連リソース

### プロジェクト文書
- **[CONTRIBUTING.md](../../CONTRIBUTING.md)** - 基本的な貢献ガイド
- **[CLAUDE.md](../../CLAUDE.md)** - Claude Code プロジェクト設定
- **[README.md](../../README.md)** - プロジェクト概要
- **[CHANGELOG.md](../../CHANGELOG.md)** - 変更履歴

### 技術文書
- **[アーキテクチャ文書](../dev/architecture.md)** - システム設計仕様
- **[コーディング規約](../dev/coding-standards.md)** - 開発規約詳細
- **[記法仕様](../specs/notation.md)** - Kumihan記法仕様

### 開発ツール
- **[Makefile](../../Makefile)** - 開発コマンド集約
- **[pyproject.toml](../../pyproject.toml)** - Python プロジェクト設定
- **[.pre-commit-config.yaml](../../.pre-commit-config.yaml)** - コード品質自動チェック

### 外部リソース
- **[Python Style Guide (PEP 8)](https://pep8-ja.readthedocs.io/ja/latest/)**
- **[Type Hints (PEP 484)](https://docs.python.org/ja/3/library/typing.html)**
- **[pytest Documentation](https://docs.pytest.org/en/stable/)**
- **[Black Documentation](https://black.readthedocs.io/en/stable/)**

---

## 🎯 最後に

Kumihan-Formatterプロジェクトへの貢献を検討していただき、ありがとうございます。あなたの参加により、プロジェクトがより良いものになることを期待しています。

### 参加方法
1. **Issueを確認** - 興味のある課題を探す
2. **環境構築** - 開発環境をセットアップ
3. **小さな貢献から** - ドキュメント修正やテスト追加から開始
4. **コミュニティ参加** - Issue・PRでの議論に参加

### サポート
- **技術的な質問**: Issue での質問歓迎
- **貢献方法の相談**: PRでの相談・議論参加
- **新機能提案**: Enhancement Issue での提案

**みなさまの貢献をお待ちしています！** 🚀

---

*📝 Generated with [Claude Code](https://claude.ai/code) for Kumihan-Formatter*
*🤖 Gemini協業による効率的ドキュメント生成*

*Co-Authored-By: Claude <noreply@anthropic.com>*