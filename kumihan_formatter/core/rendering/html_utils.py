"""HTML utility functions for Kumihan-Formatter

This module provides utility functions for HTML processing including
escaping, formatting, and nesting logic.
"""

import re
from typing import Dict, Any, List
from html import escape


def escape_html(text: str) -> str:
    """
    Escape HTML special characters
    
    Args:
        text: Text to escape
    
    Returns:
        str: HTML-escaped text
    """
    return escape(text)


def render_attributes(attributes: Dict[str, Any]) -> str:
    """
    Render HTML attributes
    
    Args:
        attributes: Dictionary of attributes
    
    Returns:
        str: Formatted HTML attributes string
    """
    if not attributes:
        return ''
    
    attr_parts = []
    for key, value in attributes.items():
        if value is not None:
            escaped_value = escape(str(value))
            attr_parts.append(f'{key}="{escaped_value}"')
    
    return ' '.join(attr_parts)


def process_text_content(text: str) -> str:
    """
    Process text content, converting newlines to <br> tags
    
    Args:
        text: Raw text content
    
    Returns:
        str: Processed HTML with proper line breaks
    """
    if not text:
        return text
        
    # Check if text already contains HTML tags (from inline processing)
    if contains_html_tags(text):
        # Only convert newlines, don't escape HTML
        processed_text = re.sub(r'\r?\n', '<br>\n', text)
    else:
        # Escape HTML entities first, then convert newlines
        escaped_text = escape(text)
        processed_text = re.sub(r'\r?\n', '<br>\n', escaped_text)
    
    # Clean up multiple consecutive br tags
    processed_text = re.sub(r'(<br>\s*){3,}', '<br>\n<br>\n', processed_text)
    
    return processed_text


def process_block_content(text: str) -> str:
    """
    Process block content, converting list markers and newlines
    
    Args:
        text: Raw block content
    
    Returns:
        str: Processed HTML with list markers converted and line breaks
    """
    if not text:
        return text
    
    # Check if text already contains HTML tags (from inline processing)
    if contains_html_tags(text):
        # Process text with existing HTML tags
        processed_text = _convert_list_markers_with_html(text)
        processed_text = re.sub(r'\r?\n', '<br>\n', processed_text)
    else:
        # First convert list markers, then escape HTML, then convert newlines
        processed_text = _convert_list_markers(text)
        processed_text = escape(processed_text)
        processed_text = re.sub(r'\r?\n', '<br>\n', processed_text)
    
    # Clean up multiple consecutive br tags
    processed_text = re.sub(r'(<br>\s*){3,}', '<br>\n<br>\n', processed_text)
    
    return processed_text


def process_collapsible_content(text: str) -> str:
    """
    Process collapsible block content with proper list handling
    
    Args:
        text: Raw collapsible block content
    
    Returns:
        str: Processed HTML with proper list structure and line breaks
    """
    if not text:
        return text
    
    # Check if text already contains HTML tags (from inline processing)
    if contains_html_tags(text):
        # Process text with existing HTML tags
        processed_text = _convert_list_markers_with_html(text)
        processed_text = re.sub(r'\r?\n', '<br>\n', processed_text)
    else:
        # Convert lists to proper HTML structure first
        processed_text = _convert_lists_to_html(text)
        # Then convert remaining newlines to br tags, but avoid adding br after HTML tags
        processed_text = re.sub(r'(?<!>)\r?\n(?!<)', '<br>\n', processed_text)
    
    # Clean up multiple consecutive br tags
    processed_text = re.sub(r'(<br>\s*){3,}', '<br>\n<br>\n', processed_text)
    
    return processed_text


def _convert_list_markers(text: str) -> str:
    """
    Convert list markers (- and ・) in plain text
    
    Args:
        text: Plain text content
    
    Returns:
        str: Text with list markers converted
    """
    lines = text.split('\n')
    converted_lines = []
    
    for line in lines:
        # Convert line-starting list markers
        if re.match(r'^(\s*)-\s', line):
            # Replace - with ・ (middle dot)
            converted_line = re.sub(r'^(\s*)-\s', r'\1・ ', line)
            converted_lines.append(converted_line)
        else:
            converted_lines.append(line)
    
    return '\n'.join(converted_lines)


def _convert_lists_to_html(text: str) -> str:
    """
    Convert list markers to proper HTML ul/li structure
    
    Args:
        text: Plain text content
    
    Returns:
        str: Text with list markers converted to HTML
    """
    lines = text.split('\n')
    result_lines = []
    in_list = False
    
    for line in lines:
        # Check if this line is a list item
        if re.match(r'^(\s*)-\s', line):
            # If not already in a list, start one
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            
            # Extract the list item content
            item_content = re.sub(r'^(\s*)-\s', '', line)
            result_lines.append(f'<li>{escape(item_content)}</li>')
        else:
            # If we were in a list and this line is not a list item, close the list
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            
            # Add the non-list line (escaped if not empty)
            if line.strip():
                result_lines.append(escape(line))
            else:
                result_lines.append('')
    
    # Close any open list at the end
    if in_list:
        result_lines.append('</ul>')
    
    return '\n'.join(result_lines)


def _convert_list_markers_with_html(text: str) -> str:
    """
    Convert list markers in text that may contain HTML tags
    
    Args:
        text: Text content that may contain HTML
    
    Returns:
        str: Text with list markers converted
    """
    lines = text.split('\n')
    converted_lines = []
    
    for line in lines:
        # Convert line-starting list markers, being careful with HTML
        if re.match(r'^(\s*)-\s', line):
            # Replace - with ・ (middle dot)
            converted_line = re.sub(r'^(\s*)-\s', r'\1・ ', line)
            converted_lines.append(converted_line)
        else:
            converted_lines.append(line)
    
    return '\n'.join(converted_lines)


def contains_html_tags(text: str) -> bool:
    """
    Check if text contains HTML tags
    
    Args:
        text: Text to check
    
    Returns:
        bool: True if text contains HTML tags
    """
    # Simple check for common HTML tags that might be generated by inline processing
    html_tag_pattern = r'<(?:strong|em|span|div)[^>]*>.*?</(?:strong|em|span|div)>'
    return bool(re.search(html_tag_pattern, text, re.IGNORECASE | re.DOTALL))


def create_simple_tag(tag: str, content: str, attributes: Dict[str, Any] = None) -> str:
    """
    Create a simple HTML tag with content
    
    Args:
        tag: HTML tag name
        content: Tag content
        attributes: Optional attributes
    
    Returns:
        str: Complete HTML tag
    """
    attr_str = render_attributes(attributes) if attributes else ''
    
    if attr_str:
        return f'<{tag} {attr_str}>{content}</{tag}>'
    else:
        return f'<{tag}>{content}</{tag}>'


def create_self_closing_tag(tag: str, attributes: Dict[str, Any] = None) -> str:
    """
    Create a self-closing HTML tag
    
    Args:
        tag: HTML tag name
        attributes: Optional attributes
    
    Returns:
        str: Self-closing HTML tag
    """
    attr_str = render_attributes(attributes) if attributes else ''
    
    if attr_str:
        return f'<{tag} {attr_str} />'
    else:
        return f'<{tag} />'


# Nesting order for compound elements (outer to inner)
NESTING_ORDER = [
    'details',  # 折りたたみ, ネタバレ
    'div',      # 枠線, ハイライト  
    'h1', 'h2', 'h3', 'h4', 'h5',  # 見出し
    'strong',   # 太字
    'em'        # イタリック
]


def get_tag_priority(tag: str) -> int:
    """
    Get the nesting priority for a tag
    
    Args:
        tag: HTML tag name
    
    Returns:
        int: Priority number (lower means outer)
    """
    try:
        return NESTING_ORDER.index(tag)
    except ValueError:
        return 999  # Unknown tags go last


def sort_keywords_by_nesting_order(keywords: List[str]) -> List[str]:
    """
    Sort keywords by their nesting order
    
    Args:
        keywords: List of keywords to sort
    
    Returns:
        List[str]: Keywords sorted by nesting priority
    """
    # Map keywords to their HTML tags
    keyword_to_tag = {
        '折りたたみ': 'details',
        'ネタバレ': 'details',
        '枠線': 'div',
        'ハイライト': 'div',
        '見出し1': 'h1',
        '見出し2': 'h2', 
        '見出し3': 'h3',
        '見出し4': 'h4',
        '見出し5': 'h5',
        '太字': 'strong',
        'イタリック': 'em'
    }
    
    def get_keyword_priority(keyword: str) -> int:
        tag = keyword_to_tag.get(keyword, 'span')
        return get_tag_priority(tag)
    
    return sorted(keywords, key=get_keyword_priority)