"""サンプル生成機能のテスト"""

import shutil
from pathlib import Path
import pytest
from kumihan_formatter.cli import generate_sample
from kumihan_formatter.sample_content import SHOWCASE_SAMPLE, SAMPLE_IMAGES


class TestSampleGeneration:
    """サンプル生成機能のテストクラス"""
    
    def test_generate_sample_creates_files(self, tmp_path):
        """サンプル生成で必要なファイルが作成されることを確認"""
        output_dir = tmp_path / "test_sample"
        
        # サンプルを生成
        result = generate_sample(str(output_dir))
        
        # ディレクトリが作成されたことを確認
        assert output_dir.exists()
        assert output_dir.is_dir()
        
        # 必要なファイルが存在することを確認
        assert (output_dir / "showcase.txt").exists()
        assert (output_dir / "showcase.html").exists()
        assert (output_dir / "images").exists()
        
        # 画像ファイルが作成されたことを確認
        for image_name in SAMPLE_IMAGES.keys():
            assert (output_dir / "images" / image_name).exists()
    
    def test_showcase_content_is_valid(self):
        """ショーケースサンプルの内容が有効であることを確認"""
        # 必要な要素が含まれていることを確認（目次はトグル機能があるため不要）
        assert ";;;見出し1" in SHOWCASE_SAMPLE
        assert ";;;太字" in SHOWCASE_SAMPLE
        assert ";;;枠線" in SHOWCASE_SAMPLE
        assert ";;;ハイライト" in SHOWCASE_SAMPLE
        assert ".png;;;" in SHOWCASE_SAMPLE
        assert ".jpg;;;" in SHOWCASE_SAMPLE
        
        # キーワード付きリストが含まれていることを確認
        assert "- ;;;太字;;;" in SHOWCASE_SAMPLE
        assert "- ;;;枠線;;;" in SHOWCASE_SAMPLE
        assert "- ;;;ハイライト color=" in SHOWCASE_SAMPLE
    
    def test_sample_images_are_valid(self):
        """サンプル画像データが有効であることを確認"""
        assert len(SAMPLE_IMAGES) == 4
        
        expected_images = ["scenario_map.png", "character.jpg", "item_icon.png", "flowchart.png"]
        for image_name in expected_images:
            assert image_name in SAMPLE_IMAGES
            # Base64データが存在することを確認
            assert len(SAMPLE_IMAGES[image_name]) > 0
    
    def test_generated_html_is_valid(self, tmp_path):
        """生成されたHTMLが有効であることを確認"""
        output_dir = tmp_path / "test_sample"
        
        # サンプルを生成
        generate_sample(str(output_dir))
        
        # HTMLファイルを読み込む
        html_path = output_dir / "showcase.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # 必要な要素が含まれていることを確認
        assert "<!DOCTYPE html>" in html_content
        assert '<aside class="toc-sidebar' in html_content  # 目次
        assert '<div class="floating-toggle"' in html_content  # トグル機能
        assert '<img src="images/' in html_content  # 画像
        assert '<h1' in html_content  # 見出し
        assert '<strong>' in html_content  # 太字
        assert '<div class="box">' in html_content  # 枠線
        assert '<div class="highlight"' in html_content  # ハイライト
    
    def test_cleanup_after_test(self, tmp_path):
        """テスト後のクリーンアップ"""
        output_dir = tmp_path / "test_sample"
        
        # サンプルを生成
        generate_sample(str(output_dir))
        
        # クリーンアップ
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        # ディレクトリが削除されたことを確認
        assert not output_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])