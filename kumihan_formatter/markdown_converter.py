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
    japanese_name: str  # 日本語表示名
    file_number: int    # ファイル番号
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
        
        # ファイル名と日本語名のマッピング
        name_mapping = {
            'readme.md': ('README', 1),
            'quickstart.md': ('クイックスタートガイド', 2),
            'spec.md': ('記法リファレンス', 3),
            'contributing.md': ('開発者ガイド', 4),
            'changelog.md': ('変更履歴', 5),
        }
        
        # 開発者向けドキュメントの除外パターン
        exclude_patterns = {
            'analysis/',
            'dev/',
            'generated/',
        }
        
        # プロジェクトルートのREADME.mdも検索
        project_root = source_dir.parent
        root_readme = project_root / "README.md"
        if root_readme.exists():
            # READMEを最優先で追加
            markdown_files.append(MarkdownFile(
                source_path=root_readme,
                relative_path=Path("README.md"),
                html_path=self.output_dir / "01_README.html",
                title=self._extract_title(root_readme),
                japanese_name="README",
                file_number=1
            ))
        
        for md_path in source_dir.rglob("*.md"):
            # 相対パスを計算
            relative_path = md_path.relative_to(source_dir)
            
            # 開発者向けドキュメントを除外
            should_exclude = False
            for exclude_pattern in exclude_patterns:
                if str(relative_path).startswith(exclude_pattern):
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            # 日本語名とファイル番号を決定
            file_key = relative_path.name.lower()
            if file_key in name_mapping:
                japanese_name, file_number = name_mapping[file_key]
            else:
                # 未知のファイルは末尾に配置
                japanese_name = self._extract_title(md_path)
                file_number = 99
            
            # HTML出力パスを決定（番号付き日本語名）
            html_filename = f"{file_number:02d}_{japanese_name}.html"
            html_path = self.output_dir / html_filename
            
            # タイトルを抽出
            title = self._extract_title(md_path)
            
            markdown_files.append(MarkdownFile(
                source_path=md_path,
                relative_path=relative_path,
                html_path=html_path,
                title=title,
                japanese_name=japanese_name,
                file_number=file_number
            ))
        
        # ファイルを番号順でソート
        markdown_files.sort(key=lambda f: f.file_number)
        
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
    
    def convert_markdown_to_kumihan(self, content: str) -> str:
        """MarkdownファイルをHTML形式に直接変換（Kumihan記法経由なし）"""
        # 既にKumihan記法で書かれているかチェック
        lines = content.split('\n')
        kumihan_block_count = 0
        in_code_block = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # コードブロックの開始・終了
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                continue
                
            # コードブロック内は除外
            if in_code_block:
                continue
                
            # Kumihan記法ブロックの検出
            if stripped_line.startswith(';;;') and any(pattern in stripped_line for pattern in ['見出し', '太字', '枠線', 'ハイライト']):
                kumihan_block_count += 1
        
        # Kumihan記法が3個以上ある場合はそのまま返す（Kumihanファイル）
        if kumihan_block_count >= 3:
            return content
        
        # Markdownを直接HTMLに変換
        return self._convert_markdown_to_html(content)
    
    def _convert_mixed_format(self, content: str) -> str:
        """Kumihan記法とMarkdown記法が混在したファイルの変換"""
        lines = content.split('\n')
        converted_lines = []
        in_code_block = False
        in_kumihan_block = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # コードブロックの処理
            if stripped_line.startswith('```'):
                if not in_code_block:
                    # コードブロック開始
                    in_code_block = True
                    # 言語指定があるかチェック
                    lang = stripped_line[3:].strip()
                    if lang:
                        converted_lines.append(f';;;コードブロック {lang}')
                    else:
                        converted_lines.append(';;;コードブロック')
                    continue
                else:
                    # コードブロック終了
                    in_code_block = False
                    converted_lines.append(';;;')
                    continue
            
            if in_code_block:
                # コードブロック内はそのまま保持（Kumihan記法を無効化）
                converted_lines.append(line)
                continue
            
            # Kumihan記法ブロックの追跡
            if stripped_line.startswith(';;;') and any(pattern in stripped_line for pattern in ['見出し', '太字', '枠線', 'ハイライト', 'コードブロック']):
                in_kumihan_block = True
                converted_lines.append(line)
                continue
            elif stripped_line == ';;;':
                in_kumihan_block = False
                converted_lines.append(line)
                continue
            elif in_kumihan_block:
                converted_lines.append(line)
                continue
            
            # Markdown見出しをKumihan記法に変換
            if re.match(r'^#{1,5}\s+', line):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                converted_lines.append(f';;;見出し{level}')
                converted_lines.append(title)
                converted_lines.append(';;;')
                continue
            
            # その他の行はそのまま
            converted_lines.append(line)
        
        return '\n'.join(converted_lines)
    
    def _convert_markdown_to_html(self, content: str) -> str:
        """MarkdownをHTMLに直接変換"""
        import markdown
        from markdown.extensions import toc, tables, fenced_code, codehilite
        
        # Markdown拡張機能を設定
        extensions = [
            'toc',
            'tables', 
            'fenced_code',
            'codehilite',
            'attr_list',
            'def_list'
        ]
        
        extension_configs = {
            'toc': {
                'title': '目次',
                'anchorlink': True,
                'permalink': True
            },
            'codehilite': {
                'use_pygments': False,
                'css_class': 'code-block'
            }
        }
        
        # MarkdownをHTMLに変換
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs
        )
        
        html_content = md.convert(content)
        
        # 生成されたHTMLを返す（Kumihanパーサーを経由しない）
        return f'__DIRECT_HTML__{html_content}__END_DIRECT_HTML__'
    
    def _render_direct_html(self, html_content: str, title: str, navigation_html: str) -> str:
        """直接HTMLをKumihanテンプレートでラップ"""
        from jinja2 import Environment, FileSystemLoader
        
        # Kumihanテンプレートを使用
        template_dir = Path(__file__).parent / 'templates'
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('base.html.j2')
        
        # HTMLコンテンツをレンダリング
        return template.render(
            title=title,
            content=html_content,
            navigation_html=navigation_html,
            config=self.config,
            css_vars={}  # 空のCSS変数を提供
        )
    
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
        """インデックスページを生成（HTMLテンプレート使用）"""
        from jinja2 import Environment, FileSystemLoader
        
        # ファイル情報を整理
        file_data_list = []
        for md_file in markdown_files:
            # HTMLのURLを相対パスとして計算（同一フォルダなのでファイル名のみ）
            html_url = md_file.html_path.name
            file_data = {
                'title': md_file.title,
                'japanese_name': md_file.japanese_name,
                'file_number': md_file.file_number,
                'html_url': html_url
            }
            file_data_list.append(file_data)
        
        # Jinja2テンプレートでHTMLを生成
        template_dir = Path(__file__).parent / 'templates'
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('docs_index.html.j2')
        
        html_content = template.render(
            title=title,
            markdown_files=file_data_list
        )
        
        # インデックスファイルを書き込み
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(html_content, encoding='utf-8')
    
    def convert_file(self, md_file: MarkdownFile, all_files: List[MarkdownFile]) -> None:
        """単一のMarkdownファイルをHTMLに変換"""
        
        # ナビゲーション情報を生成
        nav_info = self.generate_navigation(md_file, all_files)
        
        # Markdownコンテンツを読み込み
        content = md_file.source_path.read_text(encoding='utf-8')
        
        # Markdown記法を処理（Kumihan or 直接HTML）
        processed_content = self.convert_markdown_to_kumihan(content)
        
        # 直接HTML変換かどうかチェック
        if processed_content.startswith('__DIRECT_HTML__'):
            # 直接HTML変換の場合
            direct_html = processed_content.replace('__DIRECT_HTML__', '').replace('__END_DIRECT_HTML__', '')
            
            # ナビゲーションHTMLを生成
            nav_html = self.generate_navigation_html(nav_info)
            
            # Kumihanテンプレートで直接HTMLをラップ
            html_content = self._render_direct_html(direct_html, md_file.title, nav_html)
        else:
            # 従来のKumihan記法処理
            # MarkdownリンクをKumihan記法に変換
            processed_content = self.convert_markdown_links(processed_content, md_file)
            
            # Kumihan記法でパース
            ast = parse(processed_content)
            
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
        
        # ルートインデックスページを生成（全ファイルを同一フォルダに配置）
        root_index = self.output_dir / 'index.html'
        self.generate_index_page(markdown_files, root_index)
        
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