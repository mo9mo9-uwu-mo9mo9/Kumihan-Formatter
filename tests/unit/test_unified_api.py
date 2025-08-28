"""
KumihanFormatter (unified_api) テスト
"""

import pytest
from pathlib import Path
from kumihan_formatter import KumihanFormatter


class TestKumihanFormatter:
    """KumihanFormatter 統合テストクラス"""
    
    def test_initialization(self):
        """初期化テスト"""
        formatter = KumihanFormatter()
        assert formatter is not None
        assert hasattr(formatter, 'parser')
        assert hasattr(formatter, 'renderer')
    
    def test_parse_text(self, formatter, sample_text):
        """テキスト解析テスト"""
        result = formatter.parse_text(sample_text)
        
        assert result["status"] == "success"
        assert "total_elements" in result
        assert result["total_elements"] > 0
        assert "elements" in result
    
    def test_validate_syntax_valid(self, formatter):
        """有効な構文の検証テスト"""
        valid_text = "# 重要 #これは有効な構文です##"
        result = formatter.validate_syntax(valid_text)
        
        assert result["status"] == "valid"
        assert result["total_errors"] == 0
        assert result["errors"] == []
    
    def test_validate_syntax_invalid(self, formatter):
        """無効な構文の検証テスト"""
        invalid_text = "#  #内容が空##"
        result = formatter.validate_syntax(invalid_text)
        
        assert result["status"] == "invalid"
        assert result["total_errors"] > 0
        assert len(result["errors"]) > 0
    
    def test_parse_file(self, formatter, temp_file):
        """ファイル解析テスト"""
        result = formatter.parse_file(temp_file)
        
        assert result["status"] == "success"
        assert "file_path" in result
        assert str(temp_file) == result["file_path"]
        assert result["total_elements"] > 0
    
    def test_convert_file(self, formatter, temp_file, temp_dir):
        """ファイル変換テスト"""
        output_file = temp_dir / "output.html"
        
        result = formatter.convert(temp_file, output_file)
        
        assert result["status"] == "success"
        assert result["input_file"] == str(temp_file)
        assert result["output_file"] == str(output_file)
        assert output_file.exists()
        
        # 出力ファイルの内容確認
        html_content = output_file.read_text(encoding='utf-8')
        assert "<!DOCTYPE html>" in html_content
        assert "一時ファイルテスト" in html_content
    
    def test_convert_auto_output(self, formatter, temp_file):
        """自動出力ファイル名生成テスト"""
        result = formatter.convert(temp_file)
        
        assert result["status"] == "success"
        
        output_path = Path(result["output_file"])
        assert output_path.suffix == ".html"
        assert output_path.exists()
        
        # クリーンアップ
        output_path.unlink()
    
    def test_convert_nonexistent_file(self, formatter):
        """存在しないファイルの変換テスト"""
        nonexistent = "/path/to/nonexistent/file.txt"
        result = formatter.convert(nonexistent)
        
        assert result["status"] == "error"
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_get_available_templates(self, formatter):
        """利用可能テンプレート取得テスト"""
        templates = formatter.get_available_templates()
        
        assert isinstance(templates, list)
        assert "default" in templates
        assert "minimal" in templates
    
    def test_get_system_info(self, formatter):
        """システム情報取得テスト"""
        info = formatter.get_system_info()
        
        assert "version" in info
        assert "architecture" in info
        assert "components" in info
        assert "status" in info
        
        assert info["status"] == "functional"
        assert "SimpleKumihanParser" in info["components"]["parser"]
        assert "SimpleHTMLRenderer" in info["components"]["renderer"]
    
    def test_context_manager(self, temp_file, temp_dir):
        """コンテキストマネージャーテスト"""
        output_file = temp_dir / "context_output.html"
        
        with KumihanFormatter() as formatter:
            result = formatter.convert(temp_file, output_file)
            assert result["status"] == "success"
        
        assert output_file.exists()
    
    def test_empty_text_parsing(self, formatter):
        """空のテキスト解析テスト"""
        result = formatter.parse_text("")
        
        assert result["status"] == "success"
        assert result["total_elements"] == 0
    
    def test_multiple_kumihan_blocks(self, formatter):
        """複数のKumihanブロック処理テスト"""
        text = """# 重要 #最初のブロック##

通常の段落

# 注意 #2番目のブロック##"""
        
        result = formatter.parse_text(text)
        
        assert result["status"] == "success"
        assert result["total_elements"] >= 3  # 2つのブロック + 1つの段落
        
        elements = result["elements"]
        kumihan_blocks = [e for e in elements if e["type"] == "kumihan_block"]
        assert len(kumihan_blocks) == 2
    
    def test_error_handling_in_parse(self, formatter):
        """解析エラーハンドリングテスト"""
        # 正常ケース - エラーは発生しないはず
        result = formatter.parse_text("正常なテキスト")
        assert result["status"] == "success"