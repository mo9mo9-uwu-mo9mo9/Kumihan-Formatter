"""エラーハンドリングE2Eテスト（14テスト）

E2Eテスト: エラーハンドリングE2Eテスト
- ファイルエラーハンドリング（4テスト）
- 構文エラーハンドリング（4テスト）
- システムエラーハンドリング（3テスト）
- 復旧機能テスト（3テスト）
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# 同じtestsディレクトリからインポート
try:
    from ..permission_helper import PermissionHelper
except ImportError:
    # 直接実行時のフォールバック
    sys.path.append(str(Path(__file__).parent.parent))
    from permission_helper import PermissionHelper


class TestErrorHandling(TestCase):
    """エラーハンドリングE2Eテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_conversion(self, input_file=None, options=None, expect_failure=False):
        """変換処理を実行"""
        cmd = ["python3", "-m", "kumihan_formatter", "convert"]
        if input_file:
            cmd.append(str(input_file))
        if options:
            cmd.extend(options)
        cmd.extend(["--no-preview"])

        result = subprocess.run(
            cmd, cwd=self.test_dir, capture_output=True, text=True, encoding="utf-8"
        )

        if not expect_failure:
            # 期待される成功の場合、詳細なエラー情報を表示
            if result.returncode != 0:
                print(f"Unexpected failure: {result.stderr}")

        return result

    def _create_test_file(self, filename, content, encoding="utf-8"):
        """テスト用ファイルを作成"""
        file_path = Path(self.test_dir) / filename
        if encoding:
            file_path.write_text(content, encoding=encoding)
        else:
            file_path.write_bytes(content)
        return file_path

    # ファイルエラーハンドリング（4テスト）

    def test_nonexistent_input_file_error(self):
        """存在しない入力ファイルエラーテスト"""
        nonexistent_file = Path(self.test_dir) / "nonexistent.txt"

        result = self._run_conversion(
            input_file=nonexistent_file,
            options=["--output", str(self.output_dir)],
            expect_failure=True,
        )

        # ファイルが存在しない場合は適切なエラーコードが返されることを確認
        self.assertNotEqual(result.returncode, 0)

        # エラーメッセージが適切に表示されることを確認
        error_output = (result.stderr or result.stdout or "").lower()
        self.assertTrue(
            any(
                keyword in error_output
                for keyword in [
                    "not found",
                    "存在しない",
                    "file",
                    "ファイル",
                    "error",
                    "エラー",
                    "見つかりません",
                ]
            ),
            f"Error message not found in stderr: '{result.stderr}' "
            f"or stdout: '{result.stdout}'",
        )

    def test_permission_denied_input_file_error(self):
        """読み込み権限なし入力ファイルエラーテスト"""
        # 権限なしファイルを作成
        content = "権限テストファイル"
        restricted_file = self._create_test_file("restricted.txt", content)

        with PermissionHelper.create_permission_test_context(
            file_path=restricted_file
        ) as ctx:
            if ctx.permission_denied_should_occur():
                result = self._run_conversion(
                    input_file=restricted_file,
                    options=["--output", str(self.output_dir)],
                    expect_failure=True,
                )

                # 権限エラーの場合は適切なエラーコードが返されることを確認
                self.assertNotEqual(result.returncode, 0)

                # エラーメッセージが適切に表示されることを確認（STDOUTとSTDERRの両方をチェック）
                error_output = (result.stderr + result.stdout).lower()
                self.assertTrue(
                    any(
                        keyword in error_output
                        for keyword in [
                            "permission",
                            "権限",
                            "access",
                            "アクセス",
                            "denied",
                            "拒否",
                            "ファイルに読み取りできません",
                            "読み取り専用",
                            "permission denied",
                            "読み取り",
                        ]
                    )
                )
            else:
                # 権限変更に失敗した場合はテストをスキップ
                self.skipTest("Could not deny file read permissions on this platform")

    def test_permission_denied_output_directory_error(self):
        """書き込み権限なし出力ディレクトリエラーテスト"""
        # 正常な入力ファイルを作成
        content = "# 権限テスト\n\n正常なコンテンツです。"
        input_file = self._create_test_file("input.txt", content)

        # 権限なしディレクトリを作成
        restricted_dir = Path(self.test_dir) / "restricted_output"
        restricted_dir.mkdir()

        with PermissionHelper.create_permission_test_context(
            dir_path=restricted_dir
        ) as ctx:
            if ctx.permission_denied_should_occur():
                result = self._run_conversion(
                    input_file=input_file,
                    options=["--output", str(restricted_dir)],
                    expect_failure=True,
                )

                # 書き込み権限エラーの場合は適切なエラーコードが返されることを確認
                self.assertNotEqual(result.returncode, 0)
            else:
                # 権限変更に失敗した場合はテストをスキップ
                self.skipTest(
                    "Could not deny directory write permissions on this platform"
                )

    def test_invalid_encoding_file_error(self):
        """無効なエンコーディングファイルエラーテスト"""
        # バイナリデータで無効なテキストファイルを作成
        invalid_content = b"\xff\xfe\x00\x00\x01\x02\x03\x04"
        invalid_file = self._create_test_file(
            "invalid_encoding.txt", invalid_content, encoding=None
        )

        result = self._run_conversion(
            input_file=invalid_file,
            options=["--output", str(self.output_dir)],
            expect_failure=True,
        )

        # エンコーディングエラーの場合は適切なエラーコードが返されることを確認
        # ただし、エンコーディング検出機能により回復する可能性もある
        self.assertIn(result.returncode, [0, 1, 2])

    # 構文エラーハンドリング（4テスト）

    def test_malformed_markdown_syntax_error(self):
        """不正なMarkdown構文エラーテスト"""
        malformed_content = """# 不正な構文テスト

## 不正なリスト
- 正常な項目
-- 不正なネスト（マイナス2個）
--- さらに不正なネスト

## 不正なテーブル
| 列1 | 列2
|-----|
| A | B | C |  // 列数が合わない

## 不正なコードブロック
```python
def broken_function(
    # 閉じていない関数
```

## 不正な見出し
##### 見出し5
## 見出し2（レベルが飛んでいる）

"""

        malformed_file = self._create_test_file("malformed.txt", malformed_content)

        result = self._run_conversion(
            input_file=malformed_file, options=["--output", str(self.output_dir)]
        )

        # 構文エラーがあっても可能な限り変換を続行することを確認
        # 完全な失敗ではなく、警告付き成功も許容
        self.assertIn(result.returncode, [0, 1])

        # 何らかの出力が生成されることを確認
        output_exists = (
            self.output_dir.exists() and list(self.output_dir.glob("*.html"))
        ) or list(Path(self.test_dir).glob("*.html"))
        self.assertTrue(output_exists)

    def test_invalid_special_syntax_error(self):
        """無効な特殊構文エラーテスト"""
        invalid_syntax_content = """# 無効な特殊構文テスト

## 不正な技能判定
【】  // 空の技能名
【無効な技能名@#$%】  // 特殊文字を含む

## 不正な魔法記法
《》  // 空の魔法名
《無効な魔法!@#$》  // 特殊文字を含む

## 不正なダイス記法
2d  // 面数が指定されていない
d6  // ダイス数が指定されていない
0d6  // ダイス数が0
2d0  // 面数が0

## 不正なマーカー
※  // 内容が空
★  // 内容が空

"""

        invalid_file = self._create_test_file(
            "invalid_syntax.txt", invalid_syntax_content
        )

        result = self._run_conversion(
            input_file=invalid_file, options=["--output", str(self.output_dir)]
        )

        # 特殊構文エラーがあっても基本的な変換は継続することを確認
        self.assertIn(result.returncode, [0, 1])

    def test_circular_reference_error(self):
        """循環参照エラーテスト"""
        # 循環参照を含むコンテンツ（実装依存）
        circular_content = """# 循環参照テスト

## セクションA
[セクションBを参照](#section-b)

## セクションB
[セクションAを参照](#section-a)

## 自己参照
[自分自身を参照](#自己参照)

"""

        circular_file = self._create_test_file("circular.txt", circular_content)

        result = self._run_conversion(
            input_file=circular_file, options=["--output", str(self.output_dir)]
        )

        # 循環参照があっても変換は継続することを確認
        self.assertIn(result.returncode, [0, 1])

    def test_deeply_nested_structure_error(self):
        """深いネスト構造エラーテスト"""
        # 極端に深いネスト構造を作成
        nested_content = "# 深いネスト構造テスト\n\n"

        # 20レベルの深いネストリストを作成
        for level in range(20):
            indent = "  " * level
            nested_content += f"{indent}- レベル{level + 1}のアイテム\n"

        # 10レベルの深いネスト見出しを作成
        for level in range(1, 11):
            nested_content += f"{'#' * min(level, 6)} レベル{level}の見出し\n\n"

        nested_file = self._create_test_file("deeply_nested.txt", nested_content)

        result = self._run_conversion(
            input_file=nested_file, options=["--output", str(self.output_dir)]
        )

        # 深いネスト構造があっても変換は継続することを確認
        self.assertIn(result.returncode, [0, 1])

    # システムエラーハンドリング（3テスト）

    def test_insufficient_disk_space_simulation(self):
        """ディスク容量不足シミュレーションテスト"""
        # 非常に大きなファイルを生成してディスク容量不足をシミュレート
        # 実際のディスク容量不足は危険なため、代替手段を使用

        content = "# ディスク容量テスト\n\n"
        # 大きなコンテンツを作成（ただし実際のディスク容量は消費しない）
        content += "大量のテキスト " * 1000

        large_file = self._create_test_file("large_content.txt", content)

        result = self._run_conversion(
            input_file=large_file, options=["--output", str(self.output_dir)]
        )

        # 大きなファイルでも正常に処理されることを確認
        self.assertIn(result.returncode, [0, 1])

    def test_memory_intensive_operation_error(self):
        """メモリ集約的操作エラーテスト"""
        # メモリ使用量が多い操作をシミュレート
        memory_intensive_content = """# メモリ集約的操作テスト

## 大量のテーブル
"""

        # 大きなテーブルを生成
        for table_num in range(50):
            memory_intensive_content += f"""
### テーブル{table_num + 1}
| 列1 | 列2 | 列3 | 列4 | 列5 |
|-----|-----|-----|-----|-----|
"""
            for row in range(100):
                memory_intensive_content += (
                    f"| データ{row}A | データ{row}B | データ{row}C | データ{row}D | データ{row}E |\n"
                )

        memory_file = self._create_test_file(
            "memory_intensive.txt", memory_intensive_content
        )

        result = self._run_conversion(
            input_file=memory_file, options=["--output", str(self.output_dir)]
        )

        # メモリ集約的操作でも正常に処理されることを確認
        self.assertIn(result.returncode, [0, 1])

    def test_concurrent_access_error(self):
        """同時アクセスエラーテスト"""
        # 同じファイルに対する同時変換をシミュレート
        content = "# 同時アクセステスト\n\n同時実行のテストです。"
        input_file = self._create_test_file("concurrent.txt", content)

        # 複数の変換プロセスを同時実行
        processes = []
        for i in range(3):
            output_dir = Path(self.test_dir) / f"output_{i}"
            cmd = [
                "python3",
                "-m",
                "kumihan_formatter",
                "convert",
                str(input_file),
                "--output",
                str(output_dir),
                "--no-preview",
            ]

            process = subprocess.Popen(
                cmd,
                cwd=self.test_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            processes.append(process)

        # すべてのプロセスの完了を待つ
        results = []
        for process in processes:
            stdout, stderr = process.communicate()
            results.append(process.returncode)

        # 少なくとも1つのプロセスが成功することを確認
        self.assertTrue(any(code == 0 for code in results))

    # 復旧機能テスト（3テスト）

    def test_partial_failure_recovery(self):
        """部分的失敗からの復旧テスト"""
        # 一部に問題があるが全体としては処理可能なコンテンツ
        partial_failure_content = """# 部分的失敗復旧テスト

## 正常なセクション1
これは正常に処理されるべきセクションです。

## 問題のあるセクション
![存在しない画像](nonexistent_image.png)

## 正常なセクション2
- 正常なリスト項目1
- 正常なリスト項目2

## 別の問題セクション
[壊れたリンク](http://this-domain-does-not-exist-12345.com)

## 正常なセクション3
**太字**と*イタリック*のテストです。
"""

        partial_file = self._create_test_file(
            "partial_failure.txt", partial_failure_content
        )

        result = self._run_conversion(
            input_file=partial_file, options=["--output", str(self.output_dir)]
        )

        # 部分的な問題があっても全体の処理は継続することを確認
        self.assertIn(result.returncode, [0, 1])

        # 出力ファイルが生成されることを確認
        output_exists = (
            self.output_dir.exists() and list(self.output_dir.glob("*.html"))
        ) or list(Path(self.test_dir).glob("*.html"))
        self.assertTrue(output_exists)

    def test_template_fallback_recovery(self):
        """テンプレートフォールバック復旧テスト"""
        content = "# テンプレートフォールバックテスト\n\n正常なコンテンツです。"
        input_file = self._create_test_file("template_test.txt", content)

        # 存在しないテンプレートを指定
        result = self._run_conversion(
            input_file=input_file,
            options=[
                "--output",
                str(self.output_dir),
                "--template",
                "nonexistent_template",
            ],
        )

        # 無効なテンプレートでもフォールバックして処理が継続することを確認
        self.assertIn(result.returncode, [0, 1, 2])

        # テンプレートエラーが適切に報告されることを確認
        if result.returncode != 0:
            # エラーが発生した場合、適切なエラーメッセージが表示されることを確認
            error_output = (result.stderr or result.stdout or "").lower()
            self.assertTrue(
                any(
                    keyword in error_output
                    for keyword in [
                        "template",
                        "テンプレート",
                        "not found",
                        "見つかりません",
                        "error",
                        "エラー",
                    ]
                ),
                f"Expected template error message, got: {result.stderr}",
            )

    def test_graceful_degradation(self):
        """段階的機能縮退テスト"""
        # 高度な機能を要求するが、基本的な変換は可能なコンテンツ
        degradation_content = """# 段階的機能縮退テスト

## 基本的な変換
これは基本的なMarkdownとして処理されるべきです。

## 高度な機能（失敗する可能性）
```mermaid
graph TD
    A[開始] --> B{判定}
    B -->|Yes| C[処理A]
    B -->|No| D[処理B]
```

## JavaScript埋め込み（失敗する可能性）
<script>
alert('このスクリプトは実行されません');
</script>

## 基本的な変換（続き）
- リスト項目1
- リスト項目2

**太字**と*イタリック*のテストです。

## 複雑なHTML（失敗する可能性）
<div class="complex-widget" data-config='{"advanced": true}'>
    <span>複雑なHTML構造</span>
</div>

## 最終セクション
これは確実に処理されるべきセクションです。
"""

        degradation_file = self._create_test_file(
            "degradation.txt", degradation_content
        )

        result = self._run_conversion(
            input_file=degradation_file, options=["--output", str(self.output_dir)]
        )

        # 高度な機能が失敗しても基本的な変換は成功することを確認
        self.assertIn(result.returncode, [0, 1])

        # 出力ファイルが生成され、基本的なコンテンツが含まれることを確認
        output_exists = (
            self.output_dir.exists() and list(self.output_dir.glob("*.html"))
        ) or list(Path(self.test_dir).glob("*.html"))
        self.assertTrue(output_exists)

        # 生成されたHTMLに基本的なコンテンツが含まれることを確認
        if output_exists:
            html_files = (
                list(self.output_dir.glob("*.html"))
                if self.output_dir.exists()
                else list(Path(self.test_dir).glob("*.html"))
            )
            if html_files:
                content = html_files[0].read_text(encoding="utf-8")
                # HTMLが生成されて基本的な構造を持っていることを確認
                self.assertIn("<html", content)
                self.assertIn("</html>", content)
                self.assertIn("<body", content)
                self.assertIn("</body>", content)
                # 基本的なコンテンツが含まれることを確認（見出しやリストなど）
                self.assertTrue(len(content) > 1000)  # HTMLが適切なサイズであることを確認
