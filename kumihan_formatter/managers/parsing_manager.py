"""
ParsingManager - 統合パーサー管理システム

統合対象: 41個のParserファイルを統合管理
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..core.parsing.main_parser import MainParser
from ..core.parsing.specialized.block_parser import UnifiedBlockParser  
from ..core.parsing.specialized.keyword_parser import UnifiedKeywordParser
from ..core.parsing.specialized.list_parser import UnifiedListParser
from ..core.parsing.specialized.content_parser import UnifiedContentParser
from ..core.parsing.specialized.markdown_parser import UnifiedMarkdownParser
from ..core.utilities.logger import get_logger


class ParsingManager:
    """統合パーサー管理システム - 全解析機能を統括"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 主要パーサー統合
        self.main_parser = MainParser()
        self.block_parser = UnifiedBlockParser()
        self.keyword_parser = UnifiedKeywordParser()
        self.list_parser = UnifiedListParser()
        self.content_parser = UnifiedContentParser()
        self.markdown_parser = UnifiedMarkdownParser()
        
        self.logger.info("ParsingManager initialized - unified parsing system")
    
    def parse(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """統合解析エントリーポイント"""
        try:
            if parser_type == "auto":
                return self.main_parser.parse(text)
            elif parser_type == "block":
                return self.block_parser.parse(text)
            elif parser_type == "keyword":
                return self.keyword_parser.parse(text)
            elif parser_type == "list":
                return self.list_parser.parse(text)
            elif parser_type == "content":
                return self.content_parser.parse(text)
            elif parser_type == "markdown":
                return self.markdown_parser.parse(text)
            else:
                self.logger.warning(f"Unknown parser type: {parser_type}, using main parser")
                return self.main_parser.parse(text)
        except Exception as e:
            self.logger.error(f"Parsing error with {parser_type}: {e}")
            raise
    
    def parse_file(self, file_path: Union[str, Path], parser_type: str = "auto") -> Dict[str, Any]:
        """ファイル解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse(content, parser_type)
        except Exception as e:
            self.logger.error(f"File parsing error for {file_path}: {e}")
            raise
    
    def get_available_parsers(self) -> List[str]:
        """利用可能パーサー一覧"""
        return ["auto", "block", "keyword", "list", "content", "markdown"]
    
    def validate_syntax(self, text: str) -> Dict[str, Any]:
        """構文検証"""
        return self.main_parser.validate_syntax(text)
    
    def get_parser_statistics(self) -> Dict[str, Any]:
        """パーサー統計情報"""
        return {
            "main_parser": self.main_parser.get_statistics(),
            "available_parsers": self.get_available_parsers(),
            "total_parsers": len(self.get_available_parsers())
        }