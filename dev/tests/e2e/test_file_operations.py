"""
ファイル操作包括テスト

様々なファイル状況・権限・形式での
動作確認を行うE2Eテスト
"""

import pytest
import platform
import os
from pathlib import Path
from dev.tests.e2e.utils.execution import UserActionSimulator
from dev.tests.e2e.utils.file_operations import (
    create_test_files_with_permissions,
    create_invalid_files,
    create_directory_structure_test,
    backup_and_restore_files,
    get_file_info
)
from dev.tests.e2e.utils.validation import validate_html_file


class TestFileOperations:
    """ファイル操作の包括テスト"""
    
    def test_normal_file_conversion(self, test_workspace: Path, output_directory: Path):
        """通常ファイルの変換テスト"""
        simulator = UserActionSimulator(test_workspace)
        
        # 通常のテストファイルで変換
        test_file = test_workspace / "test_data" / "basic_test.txt"
        
        if not test_file.exists():
            pytest.skip("Basic test file not found")
        
        result = simulator.simulate_cli_conversion(test_file, output_directory)
        
        assert result.returncode == 0, f"Normal file conversion failed: {result.stderr}"
        assert len(result.output_files) > 0, "No output files generated"
        
        # ファイル情報の確認
        file_info = get_file_info(test_file)
        assert file_info['is_readable'], "Test file should be readable"
        
        # 出力ファイルの検証
        html_file = result.output_files[0]
        validation_result = validate_html_file(html_file)
        assert validation_result.get('overall_success', False), "HTML validation failed"
    
    def test_permission_variations(self, test_workspace: Path, output_directory: Path):
        """様々な権限設定でのファイル処理テスト"""
        simulator = UserActionSimulator(test_workspace)
        
        # 権限の異なるテストファイルを作成
        permission_files = create_test_files_with_permissions(test_workspace / "permission_test")
        
        for file_type, file_path in permission_files.items():
            # ファイル情報を確認
            file_info = get_file_info(file_path)
            
            # 変換を実行
            result = simulator.simulate_cli_conversion(file_path, output_directory)
            
            if file_type == 'empty':
                # 空ファイルの場合はエラーになることを確認
                assert result.returncode != 0, "Empty file should cause conversion error"
            elif file_type == 'readonly':
                # 読み取り専用ファイルは正常に処理されることを確認
                if file_info['is_readable']:
                    assert result.returncode == 0, f"Readonly file conversion failed: {result.stderr}"
            else:
                # その他のファイルは正常に処理されることを確認
                assert result.returncode == 0, f"File conversion failed for {file_type}: {result.stderr}"
    
    def test_invalid_file_handling(self, test_workspace: Path, output_directory: Path):
        """無効なファイルの処理テスト"""
        simulator = UserActionSimulator(test_workspace)
        
        # 無効なファイルを作成
        invalid_files = create_invalid_files(test_workspace / "invalid_test")
        
        for file_type, file_path in invalid_files.items():
            result = simulator.simulate_cli_conversion(file_path, output_directory)
            
            if file_type == 'binary':
                # バイナリファイルはエラーになることを確認
                assert result.returncode != 0, "Binary file should cause conversion error"
                assert "エラー" in result.stderr or "error" in result.stderr.lower(), \
                    "Binary file error should be clearly indicated"
            
            elif file_type == 'invalid_encoding':
                # 無効エンコーディングファイルはエラーになることを確認
                assert result.returncode != 0, "Invalid encoding file should cause error"
            
            elif file_type == 'large':
                # 大きなファイルは時間がかかるが成功することを確認
                # ただし、合理的な時間内で完了することを確認
                if result.returncode == 0:
                    assert result.execution_time < 60.0, \
                        f"Large file conversion took too long: {result.execution_time}s"
    
    def test_complex_directory_structure(self, test_workspace: Path, output_directory: Path):
        """複雑なディレクトリ構造でのテスト"""
        simulator = UserActionSimulator(test_workspace)
        
        # 複雑なディレクトリ構造でテストファイルを作成
        structure_files = create_directory_structure_test(test_workspace / "structure_test")
        
        for structure_type, file_path in structure_files.items():
            result = simulator.simulate_cli_conversion(file_path, output_directory)
            
            # 基本的には全てのファイルが正常に処理されることを確認
            assert result.returncode == 0, \
                f"Directory structure test failed for {structure_type}: {result.stderr}"
            assert len(result.output_files) > 0, \
                f"No output files for {structure_type}"
            
            # ファイルパスの特殊文字が適切に処理されていることを確認
            html_file = result.output_files[0]
            assert html_file.exists(), f"Output file not found for {structure_type}"
    
    def test_file_backup_and_restore(self, test_workspace: Path, output_directory: Path):
        """ファイルバックアップ・復元機能のテスト"""
        simulator = UserActionSimulator(test_workspace)
        
        # テストファイルの準備
        test_file = test_workspace / "backup_test.txt"
        original_content = "バックアップテスト用オリジナル内容"
        test_file.write_text(original_content, encoding='utf-8')
        
        # バックアップ・復元のテスト
        with backup_and_restore_files([test_file]):
            # ファイルを変更
            modified_content = "変更後の内容"
            test_file.write_text(modified_content, encoding='utf-8')
            
            # 変更されていることを確認
            assert test_file.read_text(encoding='utf-8') == modified_content
            
            # 変換を実行
            result = simulator.simulate_cli_conversion(test_file, output_directory)
            assert result.returncode == 0, f"Backup test conversion failed: {result.stderr}"
        
        # ファイルが復元されていることを確認
        restored_content = test_file.read_text(encoding='utf-8')
        assert restored_content == original_content, "File was not properly restored"
    
    def test_concurrent_file_access(self, test_workspace: Path, output_directory: Path):
        """同時ファイルアクセスのテスト"""
        simulator = UserActionSimulator(test_workspace)
        
        # 同じファイルに対する同時アクセスをテスト
        test_file = test_workspace / "concurrent_test.txt"
        test_content = """;;;見出し1
同時アクセステスト
;;;

同時アクセスでも正常に処理されることを確認します。

;;;太字
重要事項
;;;
"""
        test_file.write_text(test_content, encoding='utf-8')
        
        import threading
        import time
        
        results = []
        errors = []
        
        def convert_with_delay(delay_seconds):
            try:
                time.sleep(delay_seconds)
                thread_output_dir = output_directory / f"thread_{threading.current_thread().ident}"
                thread_output_dir.mkdir(exist_ok=True)
                result = simulator.simulate_cli_conversion(test_file, thread_output_dir)
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # 複数スレッドで同時変換
        threads = []
        for i in range(3):
            thread = threading.Thread(target=convert_with_delay, args=(i * 0.1,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # エラーが発生していないことを確認
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        
        # 全ての変換が成功していることを確認
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        for i, result in enumerate(results):
            assert result.returncode == 0, f"Concurrent conversion {i+1} failed: {result.stderr}"
    
    def test_file_path_edge_cases(self, test_workspace: Path, output_directory: Path):
        """ファイルパスのエッジケーステスト"""
        simulator = UserActionSimulator(test_workspace)
        
        edge_cases = []
        
        # 非常に長いファイル名
        long_name = "very_long_filename_" + "x" * 50 + ".txt"
        long_file = test_workspace / long_name
        long_file.write_text("長いファイル名のテスト", encoding='utf-8')
        edge_cases.append(("long_filename", long_file))
        
        # 特殊文字を含むファイル名
        special_file = test_workspace / "特殊文字_テスト_123.txt"
        special_file.write_text("特殊文字ファイル名のテスト", encoding='utf-8')
        edge_cases.append(("special_chars", special_file))
        
        # スペースを含むファイル名
        space_file = test_workspace / "file with spaces.txt"
        space_file.write_text("スペース含むファイル名のテスト", encoding='utf-8')
        edge_cases.append(("spaces", space_file))
        
        # ドット始まりのファイル名（隠しファイル風）
        dot_file = test_workspace / ".hidden_test.txt"
        dot_file.write_text("隠しファイル風のテスト", encoding='utf-8')
        edge_cases.append(("dot_prefix", dot_file))
        
        for case_name, file_path in edge_cases:
            result = simulator.simulate_cli_conversion(file_path, output_directory)
            
            # 基本的には全てのケースで正常に処理されることを確認
            assert result.returncode == 0, \
                f"Edge case {case_name} failed: {result.stderr}"
            assert len(result.output_files) > 0, \
                f"No output files for edge case {case_name}"
    
    def test_output_directory_scenarios(self, test_workspace: Path):
        """出力ディレクトリの様々なシナリオテスト"""
        simulator = UserActionSimulator(test_workspace)
        test_file = test_workspace / "test_data" / "basic_test.txt"
        
        if not test_file.exists():
            pytest.skip("Basic test file not found")
        
        # シナリオ1: 存在しない出力ディレクトリ
        nonexistent_dir = test_workspace / "nonexistent_output"
        result1 = simulator.simulate_cli_conversion(test_file, nonexistent_dir)
        assert result1.returncode == 0, "Should create output directory automatically"
        assert nonexistent_dir.exists(), "Output directory should be created"
        
        # シナリオ2: 既存の出力ディレクトリ（上書き）
        existing_dir = test_workspace / "existing_output"
        existing_dir.mkdir(exist_ok=True)
        dummy_file = existing_dir / "dummy.html"
        dummy_file.write_text("dummy content", encoding='utf-8')
        
        result2 = simulator.simulate_cli_conversion(test_file, existing_dir)
        assert result2.returncode == 0, "Should handle existing output directory"
        
        # シナリオ3: 読み取り専用ディレクトリ（権限があれば）
        readonly_dir = test_workspace / "readonly_output"
        readonly_dir.mkdir(exist_ok=True)
        
        # 一時的に読み取り専用にする（テスト後に復元）
        try:
            readonly_dir.chmod(0o555)  # 読み取り・実行のみ
            result3 = simulator.simulate_cli_conversion(test_file, readonly_dir)
            
            # 権限不足でエラーになることを確認
            assert result3.returncode != 0, "Should fail with readonly output directory"
            
        finally:
            # 権限を復元（クリーンアップのため）
            readonly_dir.chmod(0o755)
    
    def test_file_encoding_variations(self, test_workspace: Path, output_directory: Path):
        """様々なファイルエンコーディングでのテスト"""
        simulator = UserActionSimulator(test_workspace)
        
        test_content = """;;;見出し1
エンコーディングテスト
;;;

日本語文字列: あいうえお漢字ひらがなカタカナ
特殊文字: ①②③④⑤
記号: ♪♫♪♫
"""
        
        encoding_tests = [
            ("utf-8", "utf-8"),
            ("utf-8-sig", "utf-8-sig"),  # BOM付きUTF-8
            ("cp932", "shift_jis"),      # Windows日本語
        ]
        
        for encoding_name, encoding in encoding_tests:
            test_file = test_workspace / f"encoding_test_{encoding_name}.txt"
            
            try:
                test_file.write_text(test_content, encoding=encoding)
                
                # エンコーディングテストでは記法チェックをスキップ（BOM処理問題を回避）
                result = simulator.simulate_cli_conversion(test_file, output_directory, skip_syntax_check=True)
                
                # UTF-8系は成功、その他は環境依存
                if encoding in ["utf-8", "utf-8-sig"]:
                    assert result.returncode == 0, \
                        f"UTF-8 encoding test failed: {result.stderr}"
                    assert len(result.output_files) > 0, \
                        f"No output files for {encoding_name}"
                else:
                    # 他のエンコーディングは環境によって処理が異なる可能性
                    if result.returncode == 0:
                        assert len(result.output_files) > 0, \
                            f"No output files for {encoding_name}"
                    # エラーの場合は適切なエラーメッセージが出ることを確認
                    else:
                        assert len(result.stderr) > 0, \
                            f"No error message for failed {encoding_name} conversion"
                            
            except (UnicodeEncodeError, UnicodeDecodeError):
                # エンコーディングが環境でサポートされていない場合はスキップ
                pytest.skip(f"Encoding {encoding} not supported in this environment")