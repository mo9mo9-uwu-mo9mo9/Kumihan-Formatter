"""
Unit tests for the Parser module
"""
import pytest
from pathlib import Path

from kumihan_formatter.parser import Parser
from kumihan_formatter.core.ast_nodes import Node


class TestParser:
    """Parserクラスのテスト"""

    @pytest.fixture
    def parser(self):
        """Parserインスタンスを生成"""
        return Parser()

    def test_parse_title_block(self, parser):
        """タイトルブロックのパースをテスト"""
        content = "■タイトル: テストシナリオ"
        nodes = parser.parse(content)
        
        assert isinstance(nodes, list)
        assert len(nodes) == 1
        assert all(isinstance(node, Node) for node in nodes)
        assert nodes[0].type == "p"
        assert "タイトル: テストシナリオ" in nodes[0].content

    def test_parse_section(self, parser):
        """セクションのパースをテスト"""
        content = "●導入\nこれはテストセクションです。"
        nodes = parser.parse(content)
        
        assert len(nodes) == 1
        assert nodes[0].type == "p"
        assert "導入" in nodes[0].content
        assert "これはテストセクションです。" in nodes[0].content

    def test_parse_npc_block(self, parser):
        """NPCブロックのパースをテスト"""
        content = "▼NPC1: 山田太郎\n年齢: 30歳\n職業: 探偵"
        nodes = parser.parse(content)
        
        assert len(nodes) == 1
        assert nodes[0].type == "p"
        assert "NPC1" in nodes[0].content
        assert "山田太郎" in nodes[0].content
        assert "年齢: 30歳" in nodes[0].content

    def test_parse_room_block(self, parser):
        """部屋ブロックのパースをテスト"""
        content = "◆部屋1: 探偵事務所\n薄暗い部屋"
        nodes = parser.parse(content)
        
        assert len(nodes) == 1
        assert nodes[0].type == "p"
        assert "部屋1" in nodes[0].content
        assert "探偵事務所" in nodes[0].content
        assert "薄暗い部屋" in nodes[0].content

    def test_parse_item_block(self, parser):
        """アイテムブロックのパースをテスト"""
        content = "★アイテム1: 古い手帳\n重要な情報が書かれている"
        nodes = parser.parse(content)
        
        assert len(nodes) == 1
        assert nodes[0].type == "p"
        assert "アイテム1" in nodes[0].content
        assert "古い手帳" in nodes[0].content
        assert "重要な情報" in nodes[0].content

    def test_parse_empty_content(self, parser):
        """空のコンテンツのパースをテスト"""
        nodes = parser.parse("")
        assert isinstance(nodes, list)
        assert len(nodes) == 0

    def test_parse_mixed_content(self, parser, sample_text):
        """複合的なコンテンツのパースをテスト"""
        nodes = parser.parse(sample_text)
        
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        
        # ノードタイプの確認（実際には全てpタイプ）
        node_types = [node.type for node in nodes]
        assert "p" in node_types
        
        # コンテンツの確認
        all_content = ' '.join([node.content for node in nodes])
        assert "テストシナリオ" in all_content
        assert "テストNPC" in all_content
        assert "テスト部屋" in all_content

    @pytest.mark.parametrize("invalid_content", [
        None,
        123,
        [],
        {},
    ])
    def test_parse_invalid_input(self, parser, invalid_content):
        """不正な入力に対するエラーハンドリングをテスト"""
        with pytest.raises((TypeError, AttributeError)):
            parser.parse(invalid_content)