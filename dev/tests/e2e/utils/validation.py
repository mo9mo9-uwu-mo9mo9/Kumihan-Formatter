"""
出力検証関連のユーティリティ関数
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import html


class HTMLValidator:
    """HTML出力の妥当性を検証するクラス"""
    
    def __init__(self, html_content: str):
        self.html_content = html_content
        # より確実なパーサーを使用
        try:
            self.soup = BeautifulSoup(html_content, 'lxml')
            parser_used = 'lxml'
        except:
            self.soup = BeautifulSoup(html_content, 'html.parser')
            parser_used = 'html.parser'
        print(f"DEBUG: Using parser: {parser_used}")
    
    def validate_basic_structure(self) -> Dict[str, bool]:
        """基本的なHTML構造を検証"""
        results = {}
        
        # DOCTYPE宣言
        results['has_doctype'] = self.html_content.strip().startswith('<!DOCTYPE html>')
        
        # html要素
        results['has_html_element'] = self.soup.find('html') is not None
        
        # head要素
        head = self.soup.find('head')
        results['has_head_element'] = head is not None
        
        if head:
            # title要素
            results['has_title'] = head.find('title') is not None
            
            # charset指定
            charset_meta = head.find('meta', attrs={'charset': True}) or \
                          head.find('meta', attrs={'http-equiv': 'Content-Type'})
            results['has_charset'] = charset_meta is not None
            
            # viewport指定
            viewport_meta = head.find('meta', attrs={'name': 'viewport'})
            results['has_viewport'] = viewport_meta is not None
        else:
            results['has_title'] = False
            results['has_charset'] = False
            results['has_viewport'] = False
        
        # body要素
        results['has_body_element'] = self.soup.find('body') is not None
        
        return results
    
    def validate_css_embedding(self) -> Dict[str, bool]:
        """CSSの埋め込みを検証"""
        results = {}
        
        # style要素の存在
        style_elements = self.soup.find_all('style')
        results['has_embedded_css'] = len(style_elements) > 0
        
        # 基本的なスタイル定義の確認
        if style_elements:
            css_content = '\n'.join([style.get_text() for style in style_elements])
            
            results['has_body_styles'] = 'body' in css_content
            results['has_heading_styles'] = any(f'h{i}' in css_content for i in range(1, 7))
            results['has_highlight_styles'] = '.highlight' in css_content
            results['has_box_styles'] = '.box' in css_content
            results['has_print_styles'] = '@media print' in css_content
        else:
            results['has_body_styles'] = False
            results['has_heading_styles'] = False
            results['has_highlight_styles'] = False
            results['has_box_styles'] = False
            results['has_print_styles'] = False
        
        return results
    
    def validate_content_structure(self) -> Dict[str, Any]:
        """コンテンツ構造を検証"""
        results = {}
        
        body = self.soup.find('body')
        if not body:
            return {'error': 'body element not found'}
        
        # デバッグ: HTML内容の一部を出力
        html_sample = str(self.soup)[:1000] if self.soup else "No soup"
        print(f"DEBUG: HTML sample: {html_sample}")
        
        # 見出し要素 - より堅牢な検出
        headings = body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        print(f"DEBUG: Found headings: {[str(h) for h in headings]}")
        
        # フォールバック: 正規表現でも検索
        import re
        if len(headings) == 0:
            heading_pattern = r'<h[1-6][^>]*>.*?</h[1-6]>'
            regex_headings = re.findall(heading_pattern, str(body), re.DOTALL)
            print(f"DEBUG: Regex fallback found: {len(regex_headings)} headings")
            if len(regex_headings) > 0:
                results['heading_count'] = len(regex_headings)
                results['has_h1'] = any('<h1' in h for h in regex_headings)
            else:
                results['heading_count'] = len(headings)
                results['has_h1'] = len(body.find_all('h1')) > 0
        else:
            results['heading_count'] = len(headings)
            results['has_h1'] = len(body.find_all('h1')) > 0
        
        # 段落要素
        paragraphs = body.find_all('p')
        results['paragraph_count'] = len(paragraphs)
        
        # リスト要素
        lists = body.find_all(['ul', 'ol'])
        results['list_count'] = len(lists)
        
        # 特殊ブロック要素
        results['highlight_block_count'] = len(body.find_all(class_='highlight'))
        results['box_block_count'] = len(body.find_all(class_='box'))
        
        # details要素（折りたたみ）
        details = body.find_all('details')
        results['details_count'] = len(details)
        
        # 画像要素
        images = body.find_all('img')
        results['image_count'] = len(images)
        
        return results
    
    def validate_syntax_compliance(self) -> Dict[str, Any]:
        """記法の正しい変換を検証"""
        results = {}
        
        body = self.soup.find('body')
        if not body:
            return {'error': 'body element not found'}
        
        # 太字要素
        strong_elements = body.find_all('strong')
        results['strong_count'] = len(strong_elements)
        
        # イタリック要素
        em_elements = body.find_all('em')
        results['em_count'] = len(em_elements)
        
        # エラーマーカーの残存チェック
        text_content = body.get_text()
        error_markers = re.findall(r'\[ERROR:[^\]]+\]', text_content)
        results['error_marker_count'] = len(error_markers)
        results['error_markers'] = error_markers
        
        # 未変換マーカーの残存チェック
        unconverted_markers = re.findall(r';;;[^;]*;;;', text_content)
        results['unconverted_marker_count'] = len(unconverted_markers)
        results['unconverted_markers'] = unconverted_markers
        
        return results
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """全体的な検証結果のサマリーを取得"""
        summary = {}
        
        # 各検証結果を統合
        summary['basic_structure'] = self.validate_basic_structure()
        summary['css_embedding'] = self.validate_css_embedding()
        summary['content_structure'] = self.validate_content_structure()
        summary['syntax_compliance'] = self.validate_syntax_compliance()
        
        # 全体的な成功判定
        basic_ok = all(summary['basic_structure'].values())
        css_ok = summary['css_embedding']['has_embedded_css']
        content_ok = summary['content_structure'].get('heading_count', 0) > 0
        syntax_ok = summary['syntax_compliance'].get('error_marker_count', 1) == 0
        
        summary['overall_success'] = basic_ok and css_ok and content_ok and syntax_ok
        
        return summary


def validate_html_file(html_file: Path) -> Dict[str, Any]:
    """HTMLファイルを検証"""
    if not html_file.exists():
        return {'error': f'HTML file not found: {html_file}'}
    
    try:
        html_content = html_file.read_text(encoding='utf-8')
        validator = HTMLValidator(html_content)
        return validator.get_validation_summary()
        
    except Exception as e:
        return {'error': f'Failed to validate HTML file: {e}'}


def compare_output_files(expected_files: List[str], actual_files: List[Path]) -> Dict[str, Any]:
    """期待されるファイルと実際の出力ファイルを比較"""
    results = {}
    
    actual_names = [f.name for f in actual_files]
    
    results['expected_files'] = expected_files
    results['actual_files'] = actual_names
    results['missing_files'] = [f for f in expected_files if f not in actual_names]
    results['unexpected_files'] = [f for f in actual_names if f not in expected_files]
    results['files_match'] = len(results['missing_files']) == 0 and len(results['unexpected_files']) == 0
    
    return results


def check_file_sizes(output_files: List[Path]) -> Dict[str, Any]:
    """出力ファイルのサイズを確認"""
    results = {}
    
    for file_path in output_files:
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            results[file_path.name] = {
                'size_bytes': size_bytes,
                'size_kb': round(size_bytes / 1024, 2),
                'is_empty': size_bytes == 0,
                'is_reasonable_size': 1024 < size_bytes < 10_000_000  # 1KB-10MB
            }
        else:
            results[file_path.name] = {'error': 'File not found'}
    
    return results


def extract_performance_metrics(execution_result) -> Dict[str, Any]:
    """実行結果からパフォーマンス指標を抽出"""
    metrics = {}
    
    metrics['execution_time'] = execution_result.execution_time
    metrics['return_code'] = execution_result.returncode
    metrics['output_file_count'] = len(execution_result.output_files)
    
    # 実行時間の評価
    metrics['performance_rating'] = 'excellent' if execution_result.execution_time < 1.0 else \
                                   'good' if execution_result.execution_time < 5.0 else \
                                   'acceptable' if execution_result.execution_time < 30.0 else 'poor'
    
    return metrics