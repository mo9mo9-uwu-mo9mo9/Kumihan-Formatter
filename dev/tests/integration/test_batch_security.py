"""
バッチファイルのセキュリティテストケース
Issue #95: パスインジェクション脆弱性対策の検証
"""

import pytest
import subprocess
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestBatchFileSecurity:
    """バッチファイルのセキュリティテスト"""
    
    @classmethod
    def setup_class(cls):
        """テスト準備"""
        # テスト用の安全なファイルを作成
        cls.temp_dir = tempfile.mkdtemp()
        cls.safe_file = Path(cls.temp_dir) / "test.txt"
        cls.safe_file.write_text("テストコンテンツ")
        
    @classmethod
    def teardown_class(cls):
        """テスト後処理"""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def get_batch_file(self):
        """OS別のバッチファイルパスを取得"""
        if sys.platform == "darwin":  # macOS
            return PROJECT_ROOT / "MAC" / "変換ツール.command"
        elif sys.platform == "win32":  # Windows
            return PROJECT_ROOT / "WINDOWS" / "変換ツール.bat"
        else:
            pytest.skip(f"Unsupported platform: {sys.platform}")
    
    def test_command_injection_semicolon(self):
        """セミコロンによるコマンドインジェクション攻撃のテスト"""
        batch_file = self.get_batch_file()
        malicious_input = 'test.txt; echo "HACKED" > /tmp/hacked.txt'
        
        # バッチファイルに悪意のある入力を渡す
        result = subprocess.run(
            [str(batch_file)],
            input=f"{malicious_input}\n",
            capture_output=True,
            text=True,
            shell=False
        )
        
        # セキュリティエラーが表示されることを確認
        assert "セキュリティエラー" in result.stdout or "無効な文字" in result.stdout
        assert result.returncode != 0
        
        # 攻撃が成功していないことを確認
        if sys.platform != "win32":
            assert not Path("/tmp/hacked.txt").exists()
    
    def test_command_injection_ampersand(self):
        """アンパサンドによるコマンドインジェクション攻撃のテスト"""
        batch_file = self.get_batch_file()
        malicious_input = 'test.txt & echo "HACKED"'
        
        result = subprocess.run(
            [str(batch_file)],
            input=f"{malicious_input}\n",
            capture_output=True,
            text=True,
            shell=False
        )
        
        assert "セキュリティエラー" in result.stdout or "無効な文字" in result.stdout
        assert result.returncode != 0
    
    def test_command_injection_pipe(self):
        """パイプによるコマンドインジェクション攻撃のテスト"""
        batch_file = self.get_batch_file()
        malicious_input = 'test.txt | cat /etc/passwd'
        
        result = subprocess.run(
            [str(batch_file)],
            input=f"{malicious_input}\n",
            capture_output=True,
            text=True,
            shell=False
        )
        
        assert "セキュリティエラー" in result.stdout or "無効な文字" in result.stdout
        assert result.returncode != 0
    
    def test_path_traversal_attack(self):
        """パストラバーサル攻撃のテスト"""
        batch_file = self.get_batch_file()
        malicious_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/tmp/../etc/passwd",
            "C:\\..\\..\\windows\\system32\\config\\sam"
        ]
        
        for malicious_input in malicious_inputs:
            result = subprocess.run(
                [str(batch_file)],
                input=f"{malicious_input}\n",
                capture_output=True,
                text=True,
                shell=False
            )
            
            assert "セキュリティエラー" in result.stdout or "相対パス" in result.stdout
            assert result.returncode != 0
    
    def test_backtick_injection(self):
        """バッククォートによるコマンド実行攻撃のテスト"""
        batch_file = self.get_batch_file()
        malicious_input = 'test.txt`rm -rf /`'
        
        result = subprocess.run(
            [str(batch_file)],
            input=f"{malicious_input}\n",
            capture_output=True,
            text=True,
            shell=False
        )
        
        assert "セキュリティエラー" in result.stdout or "無効な文字" in result.stdout
        assert result.returncode != 0
    
    def test_dollar_sign_injection(self):
        """ドル記号による変数展開攻撃のテスト"""
        batch_file = self.get_batch_file()
        malicious_inputs = [
            'test.txt$(rm -rf /)',
            'test.txt${PATH}',
            'test.txt$USER'
        ]
        
        for malicious_input in malicious_inputs:
            result = subprocess.run(
                [str(batch_file)],
                input=f"{malicious_input}\n",
                capture_output=True,
                text=True,
                shell=False
            )
            
            assert "セキュリティエラー" in result.stdout or "無効な文字" in result.stdout
            assert result.returncode != 0
    
    def test_safe_input_acceptance(self):
        """正常なファイルパスが受け入れられることのテスト"""
        batch_file = self.get_batch_file()
        
        # 安全な入力パターン
        safe_inputs = [
            str(self.safe_file),
            f'"{str(self.safe_file)}"',  # クォート付き
        ]
        
        for safe_input in safe_inputs:
            result = subprocess.run(
                [str(batch_file)],
                input=f"{safe_input}\nN\n",  # ソーストグル機能は使用しない
                capture_output=True,
                text=True,
                shell=False,
                timeout=10
            )
            
            # セキュリティエラーが出ないことを確認
            assert "セキュリティエラー" not in result.stdout
            
            # ファイルが見つからないか、正常に処理が開始されることを確認
            # (実際の変換処理は依存関係の問題で失敗する可能性がある)
            assert ("ファイルが見つかりません" in result.stdout or 
                   "変換を開始" in result.stdout or
                   "Kumihan-Formatter" in result.stdout)
    
    def test_special_characters_rejection(self):
        """特殊文字を含むパスの拒否テスト"""
        batch_file = self.get_batch_file()
        
        # 危険な特殊文字を含むパス
        dangerous_chars = [
            'file;name.txt',
            'file&name.txt',
            'file|name.txt',
            'file<name.txt',
            'file>name.txt',
            'file`name.txt',
            'file$name.txt',
            'file(name).txt',
            'file{name}.txt',
            'file[name].txt',
            'file\\;name.txt',
            'file!name.txt'
        ]
        
        for dangerous_input in dangerous_chars:
            result = subprocess.run(
                [str(batch_file)],
                input=f"{dangerous_input}\n",
                capture_output=True,
                text=True,
                shell=False
            )
            
            assert "セキュリティエラー" in result.stdout or "無効な文字" in result.stdout
            assert result.returncode != 0


if __name__ == "__main__":
    # 直接実行用
    pytest.main([__file__, "-v"])