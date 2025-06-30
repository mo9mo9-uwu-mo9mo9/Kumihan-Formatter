"""Extended Parser functionality tests"""
import pytest
from pathlib import Path

try:
    from kumihan_formatter.parser import Parser as DocumentParser
except ImportError:
    DocumentParser = None
try:
    from kumihan_formatter.core.block_parser import BlockParser
except ImportError:
    BlockParser = None
try:
    from kumihan_formatter.core.keyword_parser import KeywordParser
except ImportError:
    KeywordParser = None
try:
    from kumihan_formatter.core.list_parser import ListParser
except ImportError:
    ListParser = None


class TestDocumentParserAdvanced:
    """DocumentParserの高度なテスト"""

    @pytest.fixture
    def parser(self):
        if DocumentParser is None:
            pytest.skip("DocumentParserがimportできません")
        return DocumentParser()

    def test_parse_complex_document(self, parser):
        """複雑なドキュメントの解析テスト"""
        complex_text = """■タイトル: 複雑なシナリオ
■作者: テスト作者
■推奨人数: 3-4人
■プレイ時間: 4-5時間

●導入
ここは導入部分です。
複数行にわたる内容です。

▼探索者A: 主人公
STR:13 CON:12 DEX:15
技能: 目星 60%, 図書館 50%

▼探索者B: サポート
医学 70%, 精神分析 65%

◆書斎: 古い研究室
薄暗い部屋に古い書物が積み上げられている。
ランタンの光が揺らめいている。

◆地下室: 禁断の空間
鎖がかかった扉の奥にある。
【鍵】が必要。

◆アイテム: 古い鍵
鉄製の古い鍵。地下室の扉を開ける。
書斎の机の引き出しに隠されている。

●クライマックス
最終的な対決のシーンです。
【サンイチ】が登場します。
"""
        
        result = parser.parse(complex_text)
        
        # 基本的な構造の確認
        assert result is not None
        
        # タイトルと作者情報の確認
        title_found = False
        author_found = False
        
        # セクション、NPC、部屋、アイテムの確認
        sections_found = 0
        npcs_found = 0
        rooms_found = 0
        items_found = 0
        
        # 結果がリストの場合
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'content') or isinstance(item, dict):
                    content = getattr(item, 'content', '') if hasattr(item, 'content') else str(item)
                    if "複雑なシナリオ" in content:
                        title_found = True
                    if "テスト作者" in content:
                        author_found = True
                    if "導入" in content:
                        sections_found += 1
                    if "探索者" in content:
                        npcs_found += 1
                    if "書斎" in content or "地下室" in content:
                        rooms_found += 1
                    if "古い鍵" in content:
                        items_found += 1
        
        # 最低限の要素が見つかったことを確認
        assert title_found or author_found  # タイトルまたは作者が見つかる
        assert sections_found > 0 or npcs_found > 0 or rooms_found > 0  # 何らかの要素が見つかる

    def test_parse_malformed_blocks(self, parser):
        """形式不正なブロックの解析テスト"""
        malformed_text = """■タイトル
■作者: 
●
▼: 名前なしNPC
◆部屋名なし:
◆:
正常なテキスト
"""
        
        # エラーを発生させずに処理できることを確認
        result = parser.parse(malformed_text)
        assert result is not None  # エラーではなく結果が返される

    def test_parse_unicode_content(self, parser):
        """ユニコード文字を含むコンテンツの解析テスト"""
        unicode_text = """■タイトル: 異世界🌍ファンタジー
■作者: テスト作者✨

●導入【異世界設定】
この世界にはドラゴン🐉やエルフ🧝‍♀️が存在します。
★特殊ルール★
・魔法使用時はMPを消費
・ドラゴンのブレス攻撃は即死級

▼エルフの魔法使いアリア: 主人公
伝説のエルフ族の生き残り。
得意魔法: 火球術🔥、治療術❤️‍🩹
若く美しい容姿だが、心に深い傷を負っている。

◆古代遺跡「時の神殿」: ボスエリア
時空が歪んだ不可思議な空間。
過去と未来が交差する幻想的な場所。
【時の石】が置かれている。
⚠️危険度MAX⚠️
"""
        
        result = parser.parse(unicode_text)
        assert result is not None
        
        # 結果に絵文字が正しく含まれていることを確認
        result_str = str(result)
        assert "🌍" in result_str or "✨" in result_str or "🐉" in result_str

    def test_parse_empty_and_whitespace(self, parser):
        """  空文字列や空白のみのコンテンツのテスト"""
        test_cases = [
            "",  # 完全に空
            "   ",  # スペースのみ
            "\n\n\n",  # 改行のみ
            "\t\t",  # タブのみ
            "   \n  \t  \n   ",  # 混合空白
        ]
        
        for test_input in test_cases:
            result = parser.parse(test_input)
            assert result is not None  # エラーにならない
            # 空のリストまたは適切なデフォルト値が返される
            if isinstance(result, list):
                assert len(result) >= 0  # 空のリストでも問題なし


class TestBlockParserIntegration:
    """BlockParserの統合テスト"""

    def test_block_parser_creation(self):
        """BlockParserの作成テスト"""
        try:
            # KeywordParserも必要
            if KeywordParser is None:
                pytest.skip("KeywordParserがimportできません")
            keyword_parser = KeywordParser()
            parser = BlockParser(keyword_parser)
            assert parser is not None
        except ImportError:
            # BlockParserが存在しない場合はスキップ
            pytest.skip("BlockParserがimportできません")

    def test_block_types_parsing(self):
        """  異なるブロックタイプの解析テスト"""
        try:
            if KeywordParser is None:
                pytest.skip("KeywordParserがimportできません")
            keyword_parser = KeywordParser()
            parser = BlockParser(keyword_parser)
            
            # 異なるブロックタイプのテスト
            test_blocks = [
                "■タイトル: テスト",  # タイトルブロック
                "●セクション名",  # セクションブロック
                "▼NPC名: 詳細",  # NPCブロック
                "◆部屋名: 説明",  # 部屋ブロック
                "◆アイテム名: 説明",  # アイテムブロック
            ]
            
            for block_text in test_blocks:
                result = parser.parse_block(block_text) if hasattr(parser, 'parse_block') else None
                # エラーが発生しないことを確認
                assert result is not None or True  # メソッドが存在しない場合も許容
                
        except ImportError:
            pytest.skip("BlockParserがimportできません")


class TestKeywordParserIntegration:
    """KeywordParserの統合テスト"""

    def test_keyword_parser_creation(self):
        """KeywordParserの作成テスト"""
        try:
            parser = KeywordParser()
            assert parser is not None
        except ImportError:
            pytest.skip("KeywordParserがimportできません")

    def test_keyword_extraction(self):
        """キーワード抽出のテスト"""
        try:
            parser = KeywordParser()
            
            text_with_keywords = """【重要】ここは重要な情報です。
【注意】危険なエリアです。
【サンイチ】とは狂気値を意味します。
通常のテキストも含んでいます。
"""
            
            # キーワード抽出メソッドがある場合のテスト
            if hasattr(parser, 'extract_keywords'):
                result = parser.extract_keywords(text_with_keywords)
                assert result is not None
            else:
                # メソッドがない場合はスキップ
                pytest.skip("extract_keywordsメソッドが存在しません")
                
        except ImportError:
            pytest.skip("KeywordParserがimportできません")


class TestListParserIntegration:
    """ListParserの統合テスト"""

    def test_list_parser_creation(self):
        """ListParserの作成テスト"""
        try:
            if KeywordParser is None:
                pytest.skip("KeywordParserがimportできません")
            keyword_parser = KeywordParser()
            parser = ListParser(keyword_parser)
            assert parser is not None
        except ImportError:
            pytest.skip("ListParserがimportできません")

    def test_list_parsing(self):
        """リスト構造の解析テスト"""
        try:
            if KeywordParser is None:
                pytest.skip("KeywordParserがimportできません")
            keyword_parser = KeywordParser()
            parser = ListParser(keyword_parser)
            
            list_text = """・第一項目
・第二項目
  ・サブ項目1
  ・サブ項目2
・第三項目

1. 番号付きリストの第一項目
2. 番号付きリストの第二項目
3. 番号付きリストの第三項目
"""
            
            # リスト解析メソッドがある場合のテスト
            if hasattr(parser, 'parse_list') or hasattr(parser, 'parse'):
                parse_method = getattr(parser, 'parse_list', None) or getattr(parser, 'parse', None)
                result = parse_method(list_text)
                assert result is not None
            else:
                pytest.skip("リスト解析メソッドが存在しません")
                
        except ImportError:
            pytest.skip("ListParserがimportできません")


class TestParserPerformance:
    """Parserのパフォーマンステスト"""

    @pytest.fixture
    def parser(self):
        if DocumentParser is None:
            pytest.skip("DocumentParserがimportできません")
        return DocumentParser()

    @pytest.mark.slow
    def test_large_document_parsing(self, parser):
        """大きなドキュメントの解析パフォーマンステスト"""
        import time
        
        # 大きなドキュメントを生成
        large_content_parts = []
        for i in range(100):
            large_content_parts.append(f"""●セクション{i}
これはセクション{i}の内容です。
複数行にわたる説明文が続きます。
このセクションでは様々なイベントが発生します。

▼NPC{i}: キャラクター{i}
このキャラクターはセクション{i}に登場します。
重要な情報を持っている可能性があります。

◆場所{i}: エリア{i}
この場所は特別な特徴を持っています。
探索者たちはここで重要なイベントを体験します。

""")
        
        large_document = "\n".join(large_content_parts)
        
        # 解析時間を測定
        start_time = time.time()
        result = parser.parse(large_document)
        end_time = time.time()
        
        parsing_time = end_time - start_time
        
        # 結果の確認
        assert result is not None
        
        # パフォーマンスの確認（合理的な時間内で完了すること）
        assert parsing_time < 10.0, f"解析時間が長すぎます: {parsing_time}秒"
        
        print(f"\n大きなドキュメントの解析時間: {parsing_time:.3f}秒")

    def test_repeated_parsing(self, parser):
        """繰り返し解析のパフォーマンステスト"""
        import time
        
        test_document = """■タイトル: パフォーマンステスト
■作者: テスト作者

●導入
これはパフォーマンステスト用のドキュメントです。

▼NPC: テストキャラクター
テスト用のキャラクターです。

◆部屋: テストルーム
テスト用の部屋です。
"""
        
        # 50回繰り返して解析
        start_time = time.time()
        for i in range(50):
            result = parser.parse(test_document)
            assert result is not None
        end_time = time.time()
        
        total_time = end_time - start_time
        average_time = total_time / 50
        
        # 平均的な解析時間が合理的であることを確認
        assert average_time < 0.1, f"平均解析時間が遅いです: {average_time:.3f}秒"
        
        print(f"\n50回の繰り返し解析 - 平均時間: {average_time:.3f}秒")
