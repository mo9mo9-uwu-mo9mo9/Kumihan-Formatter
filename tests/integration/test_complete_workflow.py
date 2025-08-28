"""
完全なワークフロー統合テスト
パーサー → レンダラー → 出力の完全な流れをテスト
"""

import pytest
from pathlib import Path
from kumihan_formatter import KumihanFormatter


class TestCompleteWorkflow:
    """完全ワークフロー統合テスト"""
    
    def test_end_to_end_conversion(self, temp_dir):
        """エンドツーエンドの変換テスト"""
        # 入力ファイル作成
        input_file = temp_dir / "test_document.kumihan"
        input_file.write_text("""# 重要 #Kumihan-Formatter 統合テスト##

## テスト文書

この文書は統合テストの一部です。

# 情報 #以下の機能をテストしています##

### 機能一覧

- **パーサー機能**: Kumihan記法の解析
- **レンダラー機能**: HTMLへの変換  
- **ファイル入出力**: ファイル読み書き

1. 第一段階: テキスト解析
2. 第二段階: HTML生成
3. 第三段階: ファイル出力

# 注意 #テスト環境でのみ実行してください##

テスト完了。
""", encoding='utf-8')
        
        # 出力ファイル
        output_file = temp_dir / "test_output.html"
        
        # 変換実行
        formatter = KumihanFormatter()
        result = formatter.convert(input_file, output_file)
        
        # 変換結果検証
        assert result["status"] == "success"
        assert result["elements_count"] >= 10
        
        # 出力ファイル検証
        assert output_file.exists()
        html_content = output_file.read_text(encoding='utf-8')
        
        # HTML構造検証
        assert "<!DOCTYPE html>" in html_content
        assert "<html lang=\"ja\">" in html_content
        assert "<meta charset=\"UTF-8\">" in html_content
        
        # コンテンツ検証
        assert "統合テスト" in html_content
        assert "テスト文書" in html_content
        assert "パーサー機能" in html_content
        assert "レンダラー機能" in html_content
        
        # Kumihanブロック検証
        assert "kumihan-block important" in html_content
        assert "kumihan-block info" in html_content
        assert "kumihan-block warning" in html_content
        
        # CSS スタイル検証
        assert "<style>" in html_content
        assert ".kumihan-block" in html_content
        
        # レスポンシブ対応検証
        assert "viewport" in html_content
    
    def test_multiple_file_processing(self, temp_dir):
        """複数ファイル処理テスト"""
        formatter = KumihanFormatter()
        
        # 複数の入力ファイル作成
        files = []
        for i in range(3):
            input_file = temp_dir / f"doc_{i}.kumihan"
            input_file.write_text(f"""# テスト {i+1} #文書{i+1}の内容##

## セクション {i+1}

これは{i+1}番目の文書です。
""", encoding='utf-8')
            files.append(input_file)
        
        # 各ファイルを変換
        results = []
        for input_file in files:
            output_file = temp_dir / f"{input_file.stem}.html"
            result = formatter.convert(input_file, output_file)
            results.append((result, output_file))
        
        # 全ての変換が成功していることを確認
        for result, output_file in results:
            assert result["status"] == "success"
            assert output_file.exists()
            
            html_content = output_file.read_text(encoding='utf-8')
            assert "<!DOCTYPE html>" in html_content
    
    def test_large_document_processing(self, temp_dir):
        """大きな文書の処理テスト"""
        # 大きな文書作成
        large_content = []
        large_content.append("# 概要 #大規模文書テスト##\n")
        
        for section in range(10):
            large_content.append(f"## セクション {section + 1}\n")
            large_content.append(f"セクション{section + 1}の内容です。\n\n")
            
            for subsection in range(5):
                large_content.append(f"### サブセクション {section + 1}-{subsection + 1}\n")
                large_content.append(f"サブセクション{section + 1}-{subsection + 1}の詳細な内容です。\n")
                
                # リストアイテム追加
                for item in range(3):
                    large_content.append(f"- アイテム {item + 1}\n")
                
                large_content.append("\n")
        
        large_content.append("# 結論 #文書の終了##\n")
        large_content.append("これで文書は完了です。")
        
        input_file = temp_dir / "large_document.kumihan"
        input_file.write_text("".join(large_content), encoding='utf-8')
        
        # 変換実行
        formatter = KumihanFormatter()
        output_file = temp_dir / "large_output.html"
        result = formatter.convert(input_file, output_file)
        
        # 結果検証
        assert result["status"] == "success"
        assert result["elements_count"] > 50  # 大量の要素
        
        # HTML生成確認
        assert output_file.exists()
        html_content = output_file.read_text(encoding='utf-8')
        
        # 構造検証
        assert html_content.count("<h2") == 10  # 10個のセクション
        assert html_content.count("<h3") == 50  # 50個のサブセクション
        assert "大規模文書テスト" in html_content
    
    def test_error_recovery(self, temp_dir):
        """エラー回復テスト"""
        # 部分的に破損した文書
        input_file = temp_dir / "partial_error.kumihan"
        input_file.write_text("""# 正常 #正常なブロック##

正常な段落

#  #空の装飾名##

# 正常2 #もう一つの正常なブロック##
""", encoding='utf-8')
        
        formatter = KumihanFormatter()
        
        # 解析テスト（エラーがあっても他の部分は処理される）
        parse_result = formatter.parse_file(input_file)
        assert parse_result["status"] == "success"
        assert parse_result["total_elements"] > 0
        
        # 構文検証でエラーが検出される
        validation = formatter.validate_syntax(input_file.read_text(encoding='utf-8'))
        assert validation["status"] == "invalid"
        assert validation["total_errors"] > 0
    
    def test_cli_integration(self, temp_dir):
        """CLI統合テスト"""
        # 入力ファイル作成
        input_file = temp_dir / "cli_test.kumihan"
        input_file.write_text("# CLI #CLI経由のテスト##\n\nCLIからの変換テストです。", encoding='utf-8')
        
        output_file = temp_dir / "cli_output.html"
        
        # CLIモジュール経由での変換テスト
        from kumihan_formatter.simple_cli import convert_command
        import argparse
        
        # 引数を模擬
        args = argparse.Namespace()
        args.input = str(input_file)
        args.output = str(output_file)
        
        # CLI関数実行
        exit_code = convert_command(args)
        
        # 結果検証
        assert exit_code == 0
        assert output_file.exists()
        
        html_content = output_file.read_text(encoding='utf-8')
        assert "CLI経由のテスト" in html_content
        assert "CLI\u304b\u3089\u306e\u5909\u63db\u30c6\u30b9\u30c8\u3067\u3059\u3002" in html_content