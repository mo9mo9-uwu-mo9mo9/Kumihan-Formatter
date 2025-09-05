"""MainParser / SpecializedParser の軽量スモークテスト"""

from kumihan_formatter.parsers.main_parser import MainParser
from kumihan_formatter.parsers.specialized_parser import SpecializedParser


def test_main_parser_auto_and_simple_paths():
    p = MainParser({"default_parser": "auto", "fallback_parser": "simple"})
    # auto: 短いテキストでも実行できること（例外にならない）
    r1 = p.parse("# 見出し #内容##")
    assert r1 is not None
    # simpleフォールバック経路（異常系でもNoneではない）
    r2 = p.parse("##")
    assert r2 is not None


def test_specialized_parser_patterns():
    sp = SpecializedParser({})
    # マーカー形式
    m = sp.parse_marker_content("太字#強調##")
    assert m is not None
    # 新フォーマット（ヒットしない場合のエラー含め、ノード返却）
    nf = sp.parse_new_format_content("{{x:1}} text")
    assert nf is not None
    # ルビ（ヒットしないケースもノード返却）
    rb = sp.parse_ruby_content("|基|き| テキスト")
    assert rb is not None
