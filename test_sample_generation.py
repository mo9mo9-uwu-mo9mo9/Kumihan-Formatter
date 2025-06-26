#!/usr/bin/env python3
"""Test sample generation to reproduce RecursionError"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_minimal_sample_generation():
    """Test minimal sample generation without full dependencies"""
    
    print("=== Minimal Sample Generation Test ===")
    
    try:
        from kumihan_formatter.parser import Parser
        from kumihan_formatter.renderer import Renderer
        
        # Use a smaller sample to isolate the issue
        sample_text = """;;;見出し1
第1章：テストドキュメント
;;;

これは段落です。

;;;太字+イタリック
複合スタイル
;;;

;;;見出し2
第2章：リスト
;;;

- 項目1
- 項目2"""
        
        print("Testing parser...")
        parser = Parser()
        ast = parser.parse(sample_text)
        print(f"Parser completed: {len(ast)} nodes")
        
        print("Testing renderer...")
        renderer = Renderer()
        html = renderer.render(ast, title="test")
        print(f"Renderer completed: {len(html)} characters")
        
        print("✅ Sample generation completed successfully")
        return True
        
    except RecursionError as e:
        print(f"❌ RecursionError in sample generation: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Other error in sample generation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_sample_content():
    """Test with full SHOWCASE_SAMPLE content"""
    
    print("\n=== Full Sample Content Test ===")
    
    try:
        from kumihan_formatter.sample_content import SHOWCASE_SAMPLE
        from kumihan_formatter.parser import Parser
        from kumihan_formatter.renderer import Renderer
        
        print(f"Sample content length: {len(SHOWCASE_SAMPLE)} characters")
        print("Testing full sample parsing...")
        
        parser = Parser()
        ast = parser.parse(SHOWCASE_SAMPLE)
        print(f"Parsing completed: {len(ast)} nodes")
        
        print("Testing full sample rendering...")
        renderer = Renderer()
        html = renderer.render(ast, title="showcase")
        print(f"Rendering completed: {len(html)} characters")
        
        print("✅ Full sample generation completed successfully")
        return True
        
    except RecursionError as e:
        print(f"❌ RecursionError in full sample: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Other error in full sample: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_minimal_sample_generation()
    success2 = test_full_sample_content()
    sys.exit(0 if (success1 and success2) else 1)