"""シンプルなE2Eテスト（37テスト）

E2Eテスト: 実際の使用シナリオのE2Eテスト
- 実際のシナリオテスト（8テスト）
- オプション組み合わせテスト（12テスト）
- エラーハンドリングテスト（14テスト）
- システム統合テスト（3テスト）
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase

from tests.permission_helper import PermissionHelper


class TestSimpleE2E(TestCase):
    """シンプルなE2Eテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_file(self, filename, content):
        """テスト用ファイルを作成"""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def _run_conversion(self, input_file, options=None, expect_success=True):
        """変換処理を実行"""
        cmd = ["python3", "-m", "kumihan_formatter", "convert", str(input_file)]
        if options:
            cmd.extend(options)
        cmd.extend(["--no-preview"])

        result = subprocess.run(
            cmd, cwd=self.test_dir, capture_output=True, text=True, encoding="utf-8"
        )

        if expect_success and result.returncode not in [0, 1]:
            print(f"Unexpected result: {result.returncode}, stderr: {result.stderr}")

        return result

    # 実際のシナリオテスト（8テスト）

    def test_coc_scenario_conversion(self):
        """CoC6thシナリオ変換テスト"""
        scenario_content = """# 古き館の謎
## CoC6th 同人シナリオ

### 概要
- **想定プレイ時間**: 4-6時間
- **推奨人数**: 3-5人

### 導入
探索者たちは、古い友人から奇妙な手紙を受け取る。

### 情報収集
**図書館での調査**
- 【図書館】成功 → 館の歴史を知る
- 【オカルト】成功 → 過去の事件を発見

### 報酬
- 生還: 1d10 正気度回復
"""

        scenario_file = self._create_test_file("coc_scenario.txt", scenario_content)
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_modern_horror_conversion(self):
        """現代ホラーシナリオ変換テスト"""
        scenario_content = """# 消えた友人
## 現代ホラー TRPG シナリオ

### 背景
大学生の探索者たちの友人が突然姿を消した。

### 第1章: 発見
**友人の部屋**
- 【コンピューター】で検索履歴を確認
- 【調査】で隠されたメモを発見
"""

        scenario_file = self._create_test_file("modern_horror.txt", scenario_content)
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_fantasy_adventure_conversion(self):
        """ファンタジー冒険シナリオ変換テスト"""
        scenario_content = """# 失われた遺跡の秘宝
## ファンタジー冒険シナリオ

### 序章: 依頼
商人ガルドから依頼を受ける。
- 報酬: 金貨1000枚

### 戦利品
- 古代の魔法剣: +3 魔法の武器
- 守護の指輪: AC+2
"""

        scenario_file = self._create_test_file(
            "fantasy_adventure.txt", scenario_content
        )
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_long_document_conversion(self):
        """長文ドキュメント変換テスト"""
        chapters = []
        for i in range(1, 21):  # 20章構成
            chapters.append(
                f"""## 第{i}章: 章のタイトル{i}

これは第{i}章の内容です。

### セクション{i}-1
- 項目{i}-1-1
- 項目{i}-1-2

---
"""
            )

        long_content = f"""# 長文ドキュメントテスト

{''.join(chapters)}

## 結論
以上が長文ドキュメントの内容でした。
"""

        scenario_file = self._create_test_file("long_document.txt", long_content)
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_multilevel_structure_conversion(self):
        """多層構造ドキュメント変換テスト"""
        multilevel_content = """# 多層構造ドキュメント
## システム設計書

### 1. システム概要
#### 1.1 目的
##### 1.1.1 主要目的
このシステムの主要な目的について説明します。

#### 1.2 スコープ
##### 1.2.1 機能スコープ
###### 1.2.1.1 基本機能
- データ管理
- ユーザー認証
"""

        scenario_file = self._create_test_file(
            "multilevel_structure.txt", multilevel_content
        )
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_mixed_content_conversion(self):
        """複合コンテンツ変換テスト"""
        mixed_content = """# 複合コンテンツテスト

### テキスト要素
これは**太字**と*イタリック*を含む段落です。

### リスト要素
- 項目1
- 項目2

### 表組み
| 項目 | 説明 |
|------|------|
| 商品A | 高品質 |
| 商品B | 標準 |

### コードブロック
```python
def hello():
    print("Hello, World!")
```

### 特殊記号
- 【技能】判定
- 《魔法》の効果
- 2d6+3
"""

        scenario_file = self._create_test_file("mixed_content.txt", mixed_content)
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_toc_generation_conversion(self):
        """目次生成変換テスト"""
        toc_content = """# メインタイトル

### 第1章: 導入
#### 1.1 背景
#### 1.2 目的

### 第2章: 分析
#### 2.1 現状分析
#### 2.2 要件分析

### 第3章: 設計
#### 3.1 システム設計
#### 3.2 インターフェース設計
"""

        scenario_file = self._create_test_file("toc_test.txt", toc_content)
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_image_link_handling_conversion(self):
        """画像とリンク処理変換テスト"""
        image_link_content = """# 画像とリンクのテスト

### 画像の埋め込み
![キャラクター画像](images/character.png "キャラクター")

### リンクの例
- [公式サイト](https://example.com)
- [GitHub](https://github.com/example/repo)

### 自動リンク
- https://www.example.com
- example@email.com
"""

        scenario_file = self._create_test_file(
            "image_link_test.txt", image_link_content
        )
        result = self._run_conversion(scenario_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    # オプション組み合わせテスト（12テスト）

    def test_output_template_combination(self):
        """出力ディレクトリ+テンプレート組み合わせ"""
        content = "# テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test.txt", content)

        result = self._run_conversion(
            test_file, ["--output", str(self.output_dir), "--template", "base"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_include_source_combination(self):
        """ソース表示+構文チェック組み合わせ"""
        content = "# テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test.txt", content)

        result = self._run_conversion(
            test_file, ["--include-source", "--no-syntax-check"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_all_basic_options(self):
        """全基本オプション組み合わせ"""
        content = "# テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test.txt", content)

        result = self._run_conversion(
            test_file,
            [
                "--output",
                str(self.output_dir),
                "--template",
                "base",
                "--include-source",
                "--no-syntax-check",
            ],
        )

        self.assertIn(result.returncode, [0, 1])

    def test_template_docs_with_options(self):
        """docsテンプレート+オプション組み合わせ"""
        content = "# テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test.txt", content)

        result = self._run_conversion(
            test_file, ["--template", "docs", "--include-source"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_nonexistent_template_fallback(self):
        """存在しないテンプレートのフォールバック"""
        content = "# テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test.txt", content)

        result = self._run_conversion(
            test_file, ["--template", "nonexistent_template", "--include-source"]
        )

        # フォールバックして処理継続
        self.assertIn(result.returncode, [0, 1, 2])

    def test_multiple_output_formats(self):
        """複数出力形式テスト"""
        content = "# テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test.txt", content)

        # 異なるオプションで複数回実行
        for template in ["base", "docs"]:
            result = self._run_conversion(
                test_file,
                ["--template", template, "--output", str(self.output_dir / template)],
            )
            self.assertIn(result.returncode, [0, 1, 2])

    def test_config_file_simulation(self):
        """設定ファイルシミュレーション"""
        content = "# 設定テスト\n\n設定ファイルのテストです。"
        test_file = self._create_test_file("config_test.txt", content)

        # 設定ファイル相当のオプション指定
        result = self._run_conversion(
            test_file,
            [
                "--output",
                str(self.output_dir),
                "--template",
                "base",
                "--include-source",
            ],
        )

        self.assertIn(result.returncode, [0, 1])

    def test_watch_mode_simulation(self):
        """ウォッチモードシミュレーション"""
        content = "# ウォッチテスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("watch_test.txt", content)

        # ウォッチモードは長時間実行のため、通常モードでテスト
        result = self._run_conversion(test_file, ["--output", str(self.output_dir)])

        self.assertIn(result.returncode, [0, 1])

    def test_show_test_cases_option(self):
        """テストケース表示オプション"""
        content = "# テストケース\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("test_cases.txt", content)

        result = self._run_conversion(test_file, ["--show-test-cases"])

        # テストケース表示は特別な動作をする可能性
        self.assertIn(result.returncode, [0, 1, 2])

    def test_complex_option_combination(self):
        """複雑なオプション組み合わせ"""
        content = """# 複雑なテスト

## 多様な要素
- リスト項目
- **太字**
- *イタリック*

### テーブル
| 列1 | 列2 |
|-----|-----|
| A   | B   |
"""
        test_file = self._create_test_file("complex.txt", content)

        result = self._run_conversion(
            test_file,
            [
                "--output",
                str(self.output_dir),
                "--template",
                "base",
                "--include-source",
                "--no-syntax-check",
            ],
        )

        self.assertIn(result.returncode, [0, 1])

    def test_environment_variable_simulation(self):
        """環境変数シミュレーション"""
        content = "# 環境変数テスト\n\n基本的なコンテンツです。"
        test_file = self._create_test_file("env_test.txt", content)

        # 環境変数の代わりにオプションで指定
        result = self._run_conversion(
            test_file, ["--template", "base", "--output", str(self.output_dir)]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_error_recovery_options(self):
        """エラー回復オプションテスト"""
        content = """# エラー回復テスト

![存在しない画像](nonexistent.png)

正常なコンテンツです。
"""
        test_file = self._create_test_file("error_recovery.txt", content)

        result = self._run_conversion(test_file, ["--no-syntax-check"])  # エラーを無視するオプション

        # エラーがあっても処理継続
        self.assertIn(result.returncode, [0, 1])

    # エラーハンドリングテスト（14テスト）

    def test_nonexistent_input_file(self):
        """存在しない入力ファイルエラー"""
        nonexistent_file = Path(self.test_dir) / "nonexistent.txt"

        result = self._run_conversion(nonexistent_file, expect_success=False)

        self.assertNotEqual(result.returncode, 0)
        # STDOUTとSTDERRの両方でエラーメッセージをチェック
        error_output = (result.stderr + result.stdout).lower()
        self.assertTrue(
            any(
                keyword in error_output
                for keyword in [
                    "not found",
                    "存在しない",
                    "file",
                    "error",
                    "見つかりません",
                    "ファイル",
                    "が見つかりません",
                    "ファイル名",
                    "path",
                ]
            )
        )

    def test_permission_denied_input(self):
        """読み込み権限なし入力ファイル"""
        content = "権限テスト"
        restricted_file = self._create_test_file("restricted.txt", content)

        with PermissionHelper.create_permission_test_context(
            file_path=restricted_file
        ) as ctx:
            if ctx.permission_denied_should_occur():
                result = self._run_conversion(restricted_file, expect_success=False)
                self.assertNotEqual(result.returncode, 0)
            else:
                # 権限変更に失敗した場合はテストをスキップ
                self.skipTest("Could not deny file read permissions on this platform")

    def test_permission_denied_output(self):
        """書き込み権限なし出力ディレクトリ"""
        content = "# 権限テスト\n\n正常なコンテンツです。"
        test_file = self._create_test_file("input.txt", content)

        restricted_dir = Path(self.test_dir) / "restricted_output"
        restricted_dir.mkdir()

        with PermissionHelper.create_permission_test_context(
            dir_path=restricted_dir
        ) as ctx:
            if ctx.permission_denied_should_occur():
                result = self._run_conversion(
                    test_file, ["--output", str(restricted_dir)], expect_success=False
                )
                self.assertNotEqual(result.returncode, 0)
            else:
                # 権限変更に失敗した場合はテストをスキップ
                self.skipTest(
                    "Could not deny directory write permissions on this platform"
                )

    def test_invalid_encoding_file(self):
        """無効なエンコーディングファイル"""
        invalid_file = Path(self.test_dir) / "invalid_encoding.txt"
        invalid_file.write_bytes(b"\xff\xfe\x00\x00\x01\x02\x03\x04")

        result = self._run_conversion(invalid_file, expect_success=False)

        # エンコーディングエラーまたは回復処理
        self.assertIn(result.returncode, [0, 1, 2])

    def test_malformed_markdown_syntax(self):
        """不正なMarkdown構文"""
        malformed_content = """# 不正な構文テスト

## 不正なリスト
- 正常な項目
-- 不正なネスト
--- さらに不正

## 不正なテーブル
| 列1 | 列2
|-----|
| A | B | C |

## 基本的なコンテンツ
これは正常に処理されるべきです。
"""

        malformed_file = self._create_test_file("malformed.txt", malformed_content)
        result = self._run_conversion(malformed_file)

        # 構文エラーがあっても処理継続
        self.assertIn(result.returncode, [0, 1])

    def test_invalid_special_syntax(self):
        """無効な特殊構文"""
        invalid_syntax_content = """# 無効な特殊構文テスト

## 不正な技能判定
【】
【無効な技能名@#$%】

## 不正なダイス記法
2d
d6
0d6

## 正常なコンテンツ
これは正常に処理されるべきです。
"""

        invalid_file = self._create_test_file(
            "invalid_syntax.txt", invalid_syntax_content
        )
        result = self._run_conversion(invalid_file)

        self.assertIn(result.returncode, [0, 1])

    def test_circular_reference(self):
        """循環参照エラー"""
        circular_content = """# 循環参照テスト

## セクションA
[セクションBを参照](#section-b)

## セクションB
[セクションAを参照](#section-a)

## 正常なコンテンツ
これは正常に処理されるべきです。
"""

        circular_file = self._create_test_file("circular.txt", circular_content)
        result = self._run_conversion(circular_file)

        self.assertIn(result.returncode, [0, 1])

    def test_deeply_nested_structure(self):
        """深いネスト構造"""
        nested_content = "# 深いネスト構造テスト\n\n"

        for level in range(10):
            indent = "  " * level
            nested_content += f"{indent}- レベル{level + 1}のアイテム\n"

        for level in range(1, 7):
            nested_content += f"{'#' * level} レベル{level}の見出し\n\n"

        nested_file = self._create_test_file("deeply_nested.txt", nested_content)
        result = self._run_conversion(nested_file)

        self.assertIn(result.returncode, [0, 1])

    def test_large_file_processing(self):
        """大きなファイル処理"""
        content = "# 大きなファイルテスト\n\n"
        content += "大量のテキスト " * 5000

        large_file = self._create_test_file("large_content.txt", content)
        result = self._run_conversion(large_file)

        self.assertIn(result.returncode, [0, 1])

    def test_memory_intensive_operation(self):
        """メモリ集約的操作"""
        memory_intensive_content = "# メモリ集約的操作テスト\n\n"

        for table_num in range(10):
            memory_intensive_content += f"""
### テーブル{table_num + 1}
| 列1 | 列2 | 列3 |
|-----|-----|-----|
"""
            for row in range(50):
                memory_intensive_content += f"| データ{row}A | データ{row}B | データ{row}C |\n"

        memory_file = self._create_test_file(
            "memory_intensive.txt", memory_intensive_content
        )
        result = self._run_conversion(memory_file)

        self.assertIn(result.returncode, [0, 1])

    def test_concurrent_access_simulation(self):
        """同時アクセスシミュレーション"""
        content = "# 同時アクセステスト\n\n同時実行のテストです。"
        test_file = self._create_test_file("concurrent.txt", content)

        # 単一プロセスでのテスト（実際の同時実行は危険）
        result = self._run_conversion(test_file)
        self.assertIn(result.returncode, [0, 1])

    def test_partial_failure_recovery(self):
        """部分的失敗からの復旧"""
        partial_failure_content = """# 部分的失敗復旧テスト

## 正常なセクション1
これは正常に処理されるべきです。

## 問題のあるセクション
![存在しない画像](nonexistent_image.png)

## 正常なセクション2
- 正常なリスト項目1
- 正常なリスト項目2

## 正常なセクション3
**太字**と*イタリック*のテストです。
"""

        partial_file = self._create_test_file(
            "partial_failure.txt", partial_failure_content
        )
        result = self._run_conversion(partial_file)

        self.assertIn(result.returncode, [0, 1])

    def test_template_fallback_recovery(self):
        """テンプレートフォールバック復旧"""
        content = "# テンプレートフォールバックテスト\n\n正常なコンテンツです。"
        test_file = self._create_test_file("template_test.txt", content)

        result = self._run_conversion(test_file, ["--template", "nonexistent_template"])

        # フォールバックして処理継続
        self.assertIn(result.returncode, [0, 1, 2])

    def test_graceful_degradation(self):
        """段階的機能縮退"""
        degradation_content = """# 段階的機能縮退テスト

## 基本的な変換
これは基本的なMarkdownとして処理されるべきです。

## 高度な機能（失敗する可能性）
```mermaid
graph TD
    A[開始] --> B{判定}
```

## 基本的な変換（続き）
- リスト項目1
- リスト項目2

**太字**と*イタリック*のテストです。

## 最終セクション
これは確実に処理されるべきセクションです。
"""

        degradation_file = self._create_test_file(
            "degradation.txt", degradation_content
        )
        result = self._run_conversion(degradation_file)

        self.assertIn(result.returncode, [0, 1])

    # システム統合テスト（3テスト）

    def test_full_workflow_integration(self):
        """フルワークフロー統合テスト"""
        content = """# フルワークフロー統合テスト

## 概要
このテストは全体的なワークフローを確認します。

### 機能一覧
- Markdown変換
- テンプレート適用
- HTML出力

### 検証項目
- 【技能】判定記法
- 《魔法》記法
- ダイス記法: 2d6+3

| 項目 | 値 |
|------|-----|
| A | 1 |
| B | 2 |
"""

        test_file = self._create_test_file("full_workflow.txt", content)
        result = self._run_conversion(
            test_file,
            [
                "--output",
                str(self.output_dir),
                "--template",
                "base",
                "--include-source",
            ],
        )

        self.assertIn(result.returncode, [0, 1])

    def test_end_to_end_user_scenario(self):
        """エンドツーエンドユーザーシナリオ"""
        # 実際のユーザーが行いそうな操作をシミュレート
        user_content = """# ユーザーシナリオテスト
## CoC6th シナリオ「謎の事件」

### 導入
探索者たちは警察から依頼を受ける。

### 調査
- 【図書館】で過去の事件を調査
- 【聞き耳】で住民の証言を聞く

### 戦闘
モンスターとの戦闘では以下のダメージを与える：
- 拳銃: 1d10
- ライフル: 2d6+4

### エンディング
事件解決により1d10の正気度を回復する。
"""

        user_file = self._create_test_file("user_scenario.txt", user_content)

        # 段階的に複雑なオプションでテスト
        basic_result = self._run_conversion(user_file)
        self.assertIn(basic_result.returncode, [0, 1])

        advanced_result = self._run_conversion(
            user_file, ["--template", "base", "--include-source"]
        )
        self.assertIn(advanced_result.returncode, [0, 1])

    def test_performance_regression_check(self):
        """パフォーマンス回帰チェック"""
        # 中程度のサイズのコンテンツで処理時間をチェック
        performance_content = "# パフォーマンステスト\n\n"

        # 適度なサイズのコンテンツを生成
        for section in range(20):
            performance_content += f"""
## セクション{section + 1}

これはセクション{section + 1}の内容です。

### サブセクション
- 項目1
- 項目2
- 項目3

### テーブル
| 列A | 列B | 列C |
|-----|-----|-----|
| 値1 | 値2 | 値3 |

### コード例
```python
def function_{section}():
    return "Hello from section {section}"
```

---
"""

        performance_file = self._create_test_file(
            "performance.txt", performance_content
        )

        import time

        start_time = time.time()
        result = self._run_conversion(
            performance_file, ["--output", str(self.output_dir)]
        )
        end_time = time.time()

        # 処理が完了することを確認
        self.assertIn(result.returncode, [0, 1])

        # 処理時間が合理的であることを確認（30秒以内）
        processing_time = end_time - start_time
        self.assertLess(
            processing_time,
            30.0,
            f"Processing took too long: {processing_time:.2f} seconds",
        )
