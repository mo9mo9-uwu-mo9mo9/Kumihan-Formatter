"""
.distignore機能のテスト
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from kumihan_formatter.core.file_ops import FileOperations


class TestDistignore:
    """配布除外機能のテストクラス"""
    
    def test_load_distignore_patterns(self, tmp_path):
        """除外パターンの読み込みテスト"""
        # .distignoreファイルを作成
        distignore_content = """# コメント行
dev/
*.pyc
__pycache__/
.git/

# 空行とコメント
*.log
test_*/
"""
        distignore_path = tmp_path / ".distignore"
        distignore_path.write_text(distignore_content)
        
        # 現在のディレクトリを一時的に変更
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            file_ops = FileOperations()
            patterns = file_ops.load_distignore_patterns()
            
            # 期待されるパターンのみが読み込まれていることを確認
            expected_patterns = ["dev/", "*.pyc", "__pycache__/", ".git/", "*.log", "test_*/"]
            assert patterns == expected_patterns
            
        finally:
            os.chdir(original_cwd)
    
    def test_should_exclude_directory_patterns(self, tmp_path):
        """ディレクトリパターンの除外テスト"""
        patterns = ["dev/", "__pycache__/", "test_*/"]
        base_path = tmp_path
        
        # テスト用のパスを作成
        test_cases = [
            (base_path / "dev", True),  # devディレクトリ自体
            (base_path / "dev" / "test.py", True),  # dev配下のファイル
            (base_path / "dev" / "tools" / "script.py", True),  # dev配下の深いファイル
            (base_path / "__pycache__" / "module.pyc", True),  # __pycache__配下
            (base_path / "test_module", True),  # test_で始まるディレクトリ
            (base_path / "test_data" / "file.txt", True),  # test_で始まるディレクトリ配下
            (base_path / "src" / "main.py", False),  # 除外対象外
            (base_path / "development.txt", False),  # devを含むが除外対象外
        ]
        
        for path, expected in test_cases:
            # ディレクトリの場合は作成
            if expected and "." not in path.name:
                path.mkdir(parents=True, exist_ok=True)
            
            file_ops = FileOperations()
            result = file_ops.should_exclude(path, patterns, base_path)
            assert result == expected, f"Path {path} should {'be excluded' if expected else 'not be excluded'}"
    
    def test_should_exclude_file_patterns(self, tmp_path):
        """ファイルパターンの除外テスト"""
        patterns = ["*.pyc", "*.log", ".DS_Store", "CLAUDE.md"]
        base_path = tmp_path
        
        test_cases = [
            (base_path / "module.pyc", True),  # .pycファイル
            (base_path / "src" / "cache.pyc", True),  # 深い階層の.pyc
            (base_path / "error.log", True),  # .logファイル
            (base_path / ".DS_Store", True),  # 完全一致
            (base_path / "docs" / ".DS_Store", True),  # 深い階層での完全一致
            (base_path / "CLAUDE.md", True),  # CLAUDE.md
            (base_path / "README.md", False),  # 除外対象外
            (base_path / "main.py", False),  # 除外対象外
        ]
        
        for path, expected in test_cases:
            file_ops = FileOperations()
            result = file_ops.should_exclude(path, patterns, base_path)
            assert result == expected, f"Path {path} should {'be excluded' if expected else 'not be excluded'}"
    
    def test_should_exclude_complex_patterns(self, tmp_path):
        """複雑なパターンの除外テスト"""
        patterns = [
            "build/",
            "dist/",
            "*.egg-info/",
            ".venv/",
            "venv/",
            "*.tmp",
            "*_preview/",
            ".github/",
        ]
        base_path = tmp_path
        
        test_cases = [
            (base_path / "build" / "lib" / "module.py", True),
            (base_path / "dist" / "package.zip", True),
            (base_path / "kumihan_formatter.egg-info" / "PKG-INFO", True),
            (base_path / ".venv" / "bin" / "python", True),
            (base_path / "venv" / "lib" / "site-packages", True),
            (base_path / "temp.tmp", True),
            (base_path / "data" / "cache.tmp", True),
            (base_path / "output_preview" / "index.html", True),
            (base_path / ".github" / "workflows" / "test.yml", True),
            (base_path / "src" / "builder.py", False),  # buildを含むが除外対象外
            (base_path / "vendor" / "lib.js", False),  # venvを含むが除外対象外
        ]
        
        for path, expected in test_cases:
            file_ops = FileOperations()
            result = file_ops.should_exclude(path, patterns, base_path)
            assert result == expected, f"Path {path} should {'be excluded' if expected else 'not be excluded'}"
    
    def test_empty_distignore(self):
        """空の除外パターンでのテスト"""
        patterns = []
        base_path = Path("/test")
        
        # 全てのファイルが含まれるべき
        test_paths = [
            base_path / "file.py",
            base_path / "dev" / "test.py",
            base_path / ".git" / "config",
            base_path / "__pycache__" / "module.pyc",
        ]
        
        for path in test_paths:
            file_ops = FileOperations()
        assert not file_ops.should_exclude(path, patterns, base_path), f"Path {path} should not be excluded with empty patterns"