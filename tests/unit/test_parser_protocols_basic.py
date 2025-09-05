"""ParserProtocols の基本テスト"""

from typing import Any, Dict
from kumihan_formatter.parsers.parser_protocols import ParserProtocols


class DummyParser:
    def parse(self, text: str) -> Dict[str, Any]:
        return {"ok": True, "text": text}


def test_is_valid_parser_true():
    parser = DummyParser()
    assert ParserProtocols.is_valid_parser(parser) is True


def test_is_valid_parser_false():
    class NoParse:
        pass

    assert ParserProtocols.is_valid_parser(NoParse()) is False

