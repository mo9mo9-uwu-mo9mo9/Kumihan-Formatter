"""
Integration tests for convert functionality
"""
import pytest
from pathlib import Path

from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer
from kumihan_formatter.config import Config


class TestConvertIntegration:
    """変換処理の統合テスト"""

    @pytest.fixture
    def parser(self):
        """Parserインスタンス"""
        return Parser()

    @pytest.fixture
    def renderer(self):
        """Rendererインスタンス"""
        return Renderer()

    @pytest.fixture
    def config(self):
        """Configインスタンス"""
        return Config()

    @pytest.fixture
    def complex_content(self):
        """複雑なコンテンツ"""
        return """■タイトル: 探索者の試練
■作者: 神話作家

●導入
深い霧に包まれた港町アーカム。
1920年代のニューイングランドを舞台に、探索者たちの新たな冒険が始まる。

▼NPC1: ヘンリー・アームステッジ博士
年齢: 68歳
職業: ミスカトニック大学図書館長
能力値: INT 18, EDU 21

大学の秘密文書庫の管理者。
古代の知識に精通している。

◆部屋1: ミスカトニック大学図書館
薄暗い照明の下、無数の本が並ぶ。
奥には立ち入り禁止の特別保管庫がある。

★アイテム1: ネクロノミコン（羅語版）
危険度: 極高
SAN値減少: 1d10/2d10
呪文: 旧き印、ヨグ＝ソトースへの嘆願

▲スキル1: 図書館調査
難易度: 通常
成功時: 必要な情報を発見
失敗時: 誤った情報を掴む

◎呪文1: 旧き印
消費MP: 5
詠唱時間: 1ラウンド
効果: 下級の神話生物を退ける
"""

    @pytest.mark.integration
    def test_full_conversion_pipeline(self, parser, renderer, complex_content, temp_dir):
        """パース→レンダリング→ファイル出力の完全なパイプラインテスト"""
        # パース
        document = parser.parse(complex_content)
        assert document is not None
        assert len(document.blocks) > 0
        
        # レンダリング
        config = {
            "title": "探索者の試練",
            "author": "神話作家",
            "output_dir": str(temp_dir)
        }
        html = renderer.render(document, config)
        assert html is not None
        assert len(html) > 0
        
        # HTMLの内容確認
        assert "探索者の試練" in html
        assert "ヘンリー・アームステッジ博士" in html
        assert "ミスカトニック大学図書館" in html
        assert "ネクロノミコン" in html

    @pytest.mark.integration
    def test_error_handling_pipeline(self, parser, renderer):
        """エラーを含むコンテンツの処理テスト"""
        error_content = """■タイトル: エラーテスト

●導入
正常なセクション

▼NPC1  # コロンが欠落
エラーのあるNPCブロック

◆部屋1: 正常な部屋
この部屋は正常です
"""
        
        # パースは成功するが、一部のブロックは正しく解析されない可能性
        document = parser.parse(error_content)
        assert document is not None
        
        # レンダリングも成功する
        html = renderer.render(document)
        assert html is not None
        assert "エラーテスト" in html
        assert "正常な部屋" in html

    @pytest.mark.integration
    def test_special_characters_handling(self, parser, renderer):
        """特殊文字を含むコンテンツの処理テスト"""
        special_content = """■タイトル: <特殊文字> & "テスト"
■作者: 'テスト' & <作者>

●導入
HTMLタグを含む: <b>太字</b>
特殊記号: ♠♥♦♣
Unicode: 🎲🗡️🛡️

▼NPC1: "引用符"を含む名前
説明に<script>alert('test')</script>を含む
"""
        
        document = parser.parse(special_content)
        html = renderer.render(document)
        
        # 特殊文字が適切に処理されていることを確認
        assert document is not None
        assert html is not None
        
        # スクリプトタグが無害化されていることを確認
        assert "<script>alert(" not in html or "&lt;script&gt;" in html

    @pytest.mark.integration
    def test_large_document_handling(self, parser, renderer):
        """大きなドキュメントの処理テスト"""
        # 大量のブロックを含むコンテンツを生成
        large_content = "■タイトル: 大規模シナリオ\n\n"
        
        for i in range(50):
            large_content += f"""
●セクション{i}
セクション{i}の内容です。

▼NPC{i}: テストNPC{i}
NPC{i}の説明

◆部屋{i}: テスト部屋{i}
部屋{i}の説明

★アイテム{i}: テストアイテム{i}
アイテム{i}の説明
"""
        
        # パフォーマンスを測定
        import time
        
        start_time = time.time()
        document = parser.parse(large_content)
        parse_time = time.time() - start_time
        
        start_time = time.time()
        html = renderer.render(document)
        render_time = time.time() - start_time
        
        # 処理が成功し、妥当な時間内に完了することを確認
        assert document is not None
        assert html is not None
        assert parse_time < 5.0  # 5秒以内
        assert render_time < 5.0  # 5秒以内
        
        # 全てのセクションが含まれていることを確認
        assert "セクション49" in html

    @pytest.mark.integration
    def test_config_integration(self, parser, renderer, config, temp_dir):
        """設定ファイルを使用した統合テスト"""
        # 設定ファイルを作成
        config_file = temp_dir / "config.yaml"
        config_file.write_text("""
title: 設定テスト
author: 設定作者
template: base.html.j2
output_dir: custom_output
""", encoding="utf-8")
        
        # 設定を読み込み
        config.load(str(config_file))
        
        # コンテンツをパース
        content = "●テストセクション\nテスト内容"
        document = parser.parse(content)
        
        # 設定を使用してレンダリング
        html = renderer.render(document, config.to_dict())
        
        assert html is not None
        assert "テストセクション" in html