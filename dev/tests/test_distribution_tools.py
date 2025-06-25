"""
配布物ツールのテスト
"""

import pytest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象をインポート
import sys
sys.path.append(str(Path(__file__).parent.parent / "tools"))

try:
    from distribution_validator import (
        check_required_files, 
        check_forbidden_files, 
        check_user_scenarios,
        REQUIRED_FILES,
        FORBIDDEN_PATTERNS
    )
except ImportError:
    pytest.skip("distribution_validator module not available", allow_module_level=True)


class TestDistributionValidator:
    """配布物検証ツールのテストクラス"""
    
    def test_check_required_files_all_present(self):
        """必要ファイルが全て存在する場合のテスト"""
        file_paths = set(REQUIRED_FILES)
        found, missing = check_required_files(file_paths)
        
        assert len(missing) == 0, f"Missing files should be empty, but got: {missing}"
        assert len(found) == len(REQUIRED_FILES), f"All required files should be found"
    
    def test_check_required_files_some_missing(self):
        """一部のファイルが不足している場合のテスト"""
        file_paths = set(list(REQUIRED_FILES)[:5])  # 最初の5個だけ
        found, missing = check_required_files(file_paths)
        
        assert len(missing) > 0, "Some files should be missing"
        assert len(found) == 5, "Should find exactly 5 files"
    
    def test_check_forbidden_files_clean(self):
        """禁止ファイルが含まれていない場合のテスト"""
        clean_files = {
            "README.html",
            "kumihan_formatter/cli.py", 
            "examples/sample.txt",
            "WINDOWS/変換ツール.bat"
        }
        forbidden = check_forbidden_files(clean_files)
        
        assert len(forbidden) == 0, f"No forbidden files should be found, but got: {forbidden}"
    
    def test_check_forbidden_files_with_dev_files(self):
        """開発用ファイルが含まれている場合のテスト"""
        files_with_dev = {
            "README.html",
            "dev/tools/test.py",  # 禁止
            "__pycache__/module.pyc",  # 禁止
            ".git/config",  # 禁止
            "docs/analysis/report.html",  # 禁止
            "CLAUDE.md"  # 禁止
        }
        forbidden = check_forbidden_files(files_with_dev)
        
        assert len(forbidden) > 0, "Should find forbidden files"
        assert any("dev/" in f for f in forbidden), "Should detect dev/ files"
        assert any("__pycache__" in f for f in forbidden), "Should detect cache files"
    
    def test_check_user_scenarios_complete(self):
        """全てのユーザーシナリオが満たされる場合のテスト"""
        complete_files = set(REQUIRED_FILES) | {
            "examples/01-quickstart.txt",
            "examples/02-basic.txt", 
            "SPEC.html",
            "docs/QUICKSTART.html",
            "docs/SYNTAX_REFERENCE.html",
            "examples/"
        }
        
        results = check_user_scenarios(complete_files)
        
        # 初心者シナリオは満たされるべき
        assert results["初心者"]["usable"], "初心者シナリオが使用可能であるべき"
        assert len(results["初心者"]["missing_files"]) == 0, "初心者に必要なファイルが不足"
    
    def test_japanese_filename_handling(self):
        """日本語ファイル名の処理テスト"""
        files_with_japanese = {
            "MAC/初回セットアップ.command",
            "MAC/変換ツール.command", 
            "MAC/サンプル実行.command",
            "WINDOWS/初回セットアップ.bat"
        }
        
        found, missing = check_required_files(files_with_japanese)
        
        # 日本語ファイル名も正しく検出されるべき
        mac_commands = [f for f in found if "MAC/" in f and ".command" in f]
        assert len(mac_commands) >= 3, f"Should find MAC command files, got: {mac_commands}"


class TestDistributionValidatorEdgeCases:
    """エッジケースのテスト"""
    
    def test_empty_file_set(self):
        """空のファイルセットでの処理テスト"""
        empty_files = set()
        
        found, missing = check_required_files(empty_files)
        forbidden = check_forbidden_files(empty_files)
        scenarios = check_user_scenarios(empty_files)
        
        assert len(found) == 0, "No files should be found"
        assert len(missing) == len(REQUIRED_FILES), "All files should be missing"
        assert len(forbidden) == 0, "No forbidden files in empty set"
        
        # 全てのシナリオが使用不可になるべき
        for scenario_name, result in scenarios.items():
            assert not result["usable"], f"Scenario {scenario_name} should not be usable with empty files"
    
    def test_large_file_set(self):
        """大量のファイルでの処理テスト"""
        large_file_set = set()
        
        # 必要ファイルを含める
        large_file_set.update(REQUIRED_FILES)
        
        # 大量のダミーファイルを追加
        for i in range(1000):
            large_file_set.add(f"dummy/file_{i:04d}.txt")
        
        found, missing = check_required_files(large_file_set)
        forbidden = check_forbidden_files(large_file_set)
        
        assert len(missing) == 0, "Should find all required files even in large set"
        assert len(forbidden) == 0, "Should not find forbidden files in dummy files"


@pytest.fixture
def temp_zip_file():
    """テスト用の一時ZIPファイルを作成"""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        zip_path = Path(tmp_file.name)
    
    # 基本的なZIPファイルを作成
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.writestr("README.html", "<html><body>Test</body></html>")
        zipf.writestr("kumihan_formatter/cli.py", "# Test Python file")
        zipf.writestr("examples/sample.txt", "Sample content")
    
    yield zip_path
    
    # クリーンアップ
    if zip_path.exists():
        zip_path.unlink()


class TestDistributionValidatorIntegration:
    """統合テスト"""
    
    def test_extract_and_analyze_zip_basic(self, temp_zip_file):
        """基本的なZIP解析テスト"""
        from distribution_validator import extract_and_analyze_zip
        
        file_paths, analysis = extract_and_analyze_zip(temp_zip_file)
        
        assert len(file_paths) == 3, f"Should find 3 files, got: {file_paths}"
        assert analysis["total_files"] == 3, "Analysis should count 3 files"
        assert analysis["total_size"] > 0, "Total size should be positive"
        
        # HTMLファイルが検出されるか
        assert "README.html" in file_paths, "Should find README.html"
        assert ".html" in analysis["file_types"], "Should detect HTML file type"
    
    def test_invalid_zip_handling(self):
        """不正なZIPファイルの処理テスト"""
        from distribution_validator import extract_and_analyze_zip
        
        # 存在しないファイル
        with pytest.raises(FileNotFoundError):
            extract_and_analyze_zip(Path("nonexistent.zip"))
        
        # 不正なZIPファイル（テキストファイル）
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            tmp_file.write(b"This is not a ZIP file")
            invalid_zip_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(ValueError, match="不正なZIPファイル"):
                extract_and_analyze_zip(invalid_zip_path)
        finally:
            invalid_zip_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])