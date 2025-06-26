#!/usr/bin/env python3
"""Debug marker detection"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.keyword_parser import KeywordParser

def test_marker_detection():
    """Test marker detection logic"""
    
    keyword_parser = KeywordParser()
    block_parser = BlockParser(keyword_parser)
    
    test_lines = [
        ";;;太字",
        ";;;太字;;;",
        ";;;",
        ";;;見出し1;;;",
        "not a marker"
    ]
    
    for line in test_lines:
        line_stripped = line.strip()
        is_opening = block_parser.is_opening_marker(line_stripped)
        is_closing = block_parser.is_closing_marker(line_stripped)
        
        print(f"Line: '{line}'")
        print(f"  Stripped: '{line_stripped}'")
        print(f"  Length: {len(line_stripped)}")
        print(f"  Starts with ';;;': {line_stripped.startswith(';;;')}")
        print(f"  Ends with ';;;': {line_stripped.endswith(';;;')}")
        print(f"  Length > 6: {len(line_stripped) > 6}")
        print(f"  Is opening marker: {is_opening}")
        print(f"  Is closing marker: {is_closing}")
        print()

if __name__ == "__main__":
    test_marker_detection()