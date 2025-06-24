"""
Markdown変換機能

ZIP配布版向けのMarkdownファイルをHTMLに変換し、
適切なナビゲーションとリンク統合を行う機能
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import shutil

from .parser import parse
from .renderer import render
from .config import load_config

@dataclass
class MarkdownFile:
    """Markdownファイル情報"""
    source_path: Path
    relative_path: Path
    html_path: Path
    title: str
    nav_info: Optional[Dict] = None

@dataclass
class NavigationInfo:
    """ナビゲーション情報"""
    index_path: str
    prev_file: Optional[MarkdownFile] = None
    next_file: Optional[MarkdownFile] = None
    breadcrumb: List[Tuple[str, str]] = None  # (name, url)のリスト

class MarkdownConverter:
    """Markdown変換クラス"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.markdown_files: List[MarkdownFile] = []
        self.config = load_config()
    
    def discover_markdown_files(self, source_dir: Path) -> List[MarkdownFile]:
        """Markdownファイルを検出してリストを作成"""
        markdown_files = []
        
        for md_path in source_dir.rglob("*.md"):
            # 相対パスを計算
            relative_path = md_path.relative_to(source_dir)
            
            # HTML出力パスを決定
            html_path = self.output_dir / relative_path.with_suffix('.html')
            
            # タイトルを抽出（ファイルの最初の見出しまたはファイル名）
            title = self._extract_title(md_path)
            
            markdown_files.append(MarkdownFile(
                source_path=md_path,
                relative_path=relative_path,
                html_path=html_path,
                title=title
            ))
        
        # ファイルをソート（READMEを最初に、その後はアルファベット順）
        markdown_files.sort(key=lambda f: (
            0 if f.relative_path.name.lower() == 'readme.md' else 1,
            str(f.relative_path)
        ))
        
        return markdown_files
    
    def _extract_title(self, md_path: Path) -> str:
        """Markdownファイルからタイトルを抽出"""
        try:
            content = md_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
                elif line.startswith('## '):
                    return line[3:].strip()
            
            # 見出しが見つからない場合はファイル名を使用
            return md_path.stem.replace('_', ' ').replace('-', ' ').title()
        
        except Exception:
            return md_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def convert_markdown_links(self, content: str, current_file: MarkdownFile) -> str:
        """Markdownリンクを適切なHTMLリンクに変換"""
        
        def replace_link(match):
            link_text = match.group(1)
            link_url = match.group(2)
            
            # 外部リンクはそのまま
            if link_url.startswith(('http://', 'https://', 'mailto:')):
                return f'[{link_text}]({link_url})'
            
            # アンカーリンクはそのまま
            if link_url.startswith('#'):
                return f'[{link_text}]({link_url})'
            
            # .mdファイルへのリンクを.htmlに変換
            if link_url.endswith('.md'):
                html_url = link_url[:-3] + '.html'
                return f'[{link_text}]({html_url})'
            
            # ディレクトリリンクを処理
            if not link_url.endswith('/') and not '.' in link_url.split('/')[-1]:
                # ディレクトリの場合はindex.htmlを追加
                return f'[{link_text}]({link_url}/index.html)'
            
            return f'[{link_text}]({link_url})'
        
        # Markdownリンクパターンをマッチして変換
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        return re.sub(link_pattern, replace_link, content)
    
    def generate_navigation(self, current_file: MarkdownFile, 
                          all_files: List[MarkdownFile]) -> NavigationInfo:
        """ナビゲーション情報を生成"""
        current_index = all_files.index(current_file)
        
        # 前後のファイルを決定
        prev_file = all_files[current_index - 1] if current_index > 0 else None
        next_file = all_files[current_index + 1] if current_index < len(all_files) - 1 else None
        
        # パンくずリストを生成
        breadcrumb = []
        if current_file.relative_path.parent != Path('.'):
            # ディレクトリ階層をパンくずに追加
            parts = current_file.relative_path.parts[:-1]  # ファイル名を除く
            for i, part in enumerate(parts):
                path = '/'.join(parts[:i+1]) + '/index.html'
                breadcrumb.append((part, path))
        
        # ルートインデックスを追加
        breadcrumb.insert(0, ('📚 ドキュメント', 'index.html'))
        
        return NavigationInfo(
            index_path='index.html',
            prev_file=prev_file,
            next_file=next_file,
            breadcrumb=breadcrumb
        )
    
    def generate_navigation_html(self, nav_info: NavigationInfo) -> str:
        """ナビゲーションHTMLを生成"""
        nav_html = ['<nav class="kumihan-nav">']
        
        # パンくずリスト
        if nav_info.breadcrumb:
            nav_html.append('<div class="breadcrumb">')
            breadcrumb_items = []
            for name, url in nav_info.breadcrumb:
                breadcrumb_items.append(f'<a href="{url}">{name}</a>')
            nav_html.append(' / '.join(breadcrumb_items))
            nav_html.append('</div>')
        
        # 前後ナビゲーション
        nav_html.append('<div class="page-nav">')
        
        # 戻るボタン
        if nav_info.prev_file:
            prev_url = nav_info.prev_file.html_path.relative_to(self.output_dir)
            nav_html.append(f'<a href="{prev_url}" class="nav-prev">◀ {nav_info.prev_file.title}</a>')
        else:
            nav_html.append('<span class="nav-prev nav-disabled">◀ 前のページ</span>')
        
        # 一覧リンク
        nav_html.append(f'<a href="{nav_info.index_path}" class="nav-index">📚 一覧</a>')
        
        # 進むボタン
        if nav_info.next_file:
            next_url = nav_info.next_file.html_path.relative_to(self.output_dir)
            nav_html.append(f'<a href="{next_url}" class="nav-next">{nav_info.next_file.title} ▶</a>')
        else:
            nav_html.append('<span class="nav-next nav-disabled">次のページ ▶</span>')
        
        nav_html.append('</div>')
        nav_html.append('</nav>')
        
        return '\n'.join(nav_html)
    
    def generate_index_page(self, markdown_files: List[MarkdownFile], 
                          index_path: Path, title: str = "ドキュメント一覧") -> None:
        """インデックスページを生成"""
        
        # ディレクトリ別にファイルを分類
        directories = {}
        root_files = []
        
        for md_file in markdown_files:
            if md_file.relative_path.parent == Path('.'):
                root_files.append(md_file)
            else:
                dir_name = str(md_file.relative_path.parent)
                if dir_name not in directories:
                    directories[dir_name] = []
                directories[dir_name].append(md_file)
        
        # インデックスHTMLコンテンツを生成
        content_lines = [f'# {title}']
        content_lines.append('')
        content_lines.append('このドキュメント集では、以下の情報をご確認いただけます。')
        content_lines.append('')
        
        # ルートファイル
        if root_files:
            content_lines.append('## 📄 メインドキュメント')
            content_lines.append('')
            for md_file in root_files:
                html_url = md_file.html_path.relative_to(index_path.parent)
                content_lines.append(f'- [{md_file.title}]({html_url})')
            content_lines.append('')
        
        # ディレクトリ別ファイル
        for dir_name, files in directories.items():
            dir_title = dir_name.replace('_', ' ').replace('-', ' ').title()
            content_lines.append(f'## 📁 {dir_title}')
            content_lines.append('')
            for md_file in files:
                html_url = md_file.html_path.relative_to(index_path.parent)
                content_lines.append(f'- [{md_file.title}]({html_url})')
            content_lines.append('')
        
        # フッター情報
        content_lines.extend([
            '---',
            '',
            '💡 **使い方**: 各リンクをクリックして詳細をご確認ください。',
            '🔧 **Kumihan-Formatter** で生成されたドキュメントです。'
        ])
        
        # Kumihan記法でHTMLに変換
        kumihan_content = '\n'.join(content_lines)
        ast = parse(kumihan_content)
        html_content = render(ast, self.config, title=title)
        
        # インデックスファイルを書き込み
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(html_content, encoding='utf-8')
    
    def convert_file(self, md_file: MarkdownFile, all_files: List[MarkdownFile]) -> None:
        """単一のMarkdownファイルをHTMLに変換"""
        
        # ナビゲーション情報を生成
        nav_info = self.generate_navigation(md_file, all_files)
        
        # Markdownコンテンツを読み込み
        content = md_file.source_path.read_text(encoding='utf-8')
        
        # Markdownリンクを変換
        content = self.convert_markdown_links(content, md_file)
        
        # Kumihan記法でパース
        ast = parse(content)
        
        # ナビゲーションHTMLを生成
        nav_html = self.generate_navigation_html(nav_info)
        
        # HTMLを生成（ナビゲーション付き）
        html_content = render(ast, self.config, title=md_file.title, navigation_html=nav_html)
        
        # HTMLファイルを出力
        md_file.html_path.parent.mkdir(parents=True, exist_ok=True)
        md_file.html_path.write_text(html_content, encoding='utf-8')
    
    def convert_all(self, source_dir: Path) -> List[MarkdownFile]:
        """全Markdownファイルを変換"""
        
        # Markdownファイルを検出
        markdown_files = self.discover_markdown_files(source_dir)
        
        if not markdown_files:
            return []
        
        # 各Markdownファイルを変換
        for md_file in markdown_files:
            self.convert_file(md_file, markdown_files)
        
        # ルートインデックスページを生成
        root_index = self.output_dir / 'index.html'
        self.generate_index_page(markdown_files, root_index)
        
        # ディレクトリ別インデックスページを生成
        directories = set()
        for md_file in markdown_files:
            if md_file.relative_path.parent != Path('.'):
                directories.add(md_file.relative_path.parent)
        
        for directory in directories:
            dir_files = [f for f in markdown_files 
                        if f.relative_path.parent == directory]
            dir_index = self.output_dir / directory / 'index.html'
            dir_title = str(directory).replace('_', ' ').replace('-', ' ').title()
            self.generate_index_page(dir_files, dir_index, f"{dir_title} - ドキュメント")
        
        return markdown_files

def convert_markdown_to_html(source_dir: Path, output_dir: Path) -> List[MarkdownFile]:
    """
    指定されたディレクトリの全Markdownファイルを
    ナビゲーション付きHTMLに変換する
    
    Args:
        source_dir: ソースディレクトリ
        output_dir: 出力ディレクトリ
    
    Returns:
        変換されたMarkdownファイルのリスト
    """
    converter = MarkdownConverter(output_dir)
    return converter.convert_all(source_dir)