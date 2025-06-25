"""CLIエントリポイント"""

import os
import sys
import time
import webbrowser
import shutil
import base64
import fnmatch
from pathlib import Path

# macOSでのエンコーディング問題を修正
if sys.platform == 'darwin':
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import click
from rich.console import Console
from rich.progress import Progress

from .parser import parse
from .renderer import render
from .config import load_config
from .sample_content import SHOWCASE_SAMPLE, SAMPLE_IMAGES
from .markdown_converter import convert_markdown_to_html

# Windows環境でのエンコーディング問題対応
def setup_windows_encoding():
    """Windows環境でのエンコーディング設定"""
    if sys.platform == 'win32':
        # 標準出力のエンコーディングをUTF-8に設定
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except:
                pass
        
        # 環境変数でPythonのエンコーディングを強制
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Windows用コンソール設定
        try:
            import locale
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass

# Windows環境のセットアップを実行
setup_windows_encoding()

# 安全なConsole設定
try:
    console = Console(force_terminal=True, legacy_windows=True)
except:
    console = Console()


def _handle_sample_generation(output: str, sample_output: str, with_source_toggle: bool) -> bool:
    """サンプル生成モードの処理"""
    output_dir = output if output != "dist" else sample_output
    
    use_source_toggle = with_source_toggle
    if not with_source_toggle:
        console.print("\n[cyan][ヒント] 記法と結果を並べて表示する機能があります[/cyan]")
        console.print("[dim]   改行処理などの動作を実際に確認しながら記法を学習できます[/dim]")
        response = console.input("[yellow]この機能を使用しますか？ (Y/n): [/yellow]")
        use_source_toggle = response.lower() in ['y', 'yes', '']
    
    generate_sample(output_dir, use_source_toggle)
    return True


def _handle_test_generation(test_output: str, pattern_count: int, double_click_mode: bool, 
                           output: str, no_preview: bool, show_test_cases: bool, config: str) -> bool:
    """テストファイル生成モードの処理"""
    # generate_test_file.pyの新しいパスを設定
    dev_tools_path = Path(__file__).parent.parent / "dev" / "tools"
    if dev_tools_path not in sys.path:
        sys.path.insert(0, str(dev_tools_path))
    
    from generate_test_file import TestFileGenerator
    
    if double_click_mode:
        console.print("[cyan][設定] テスト用記法網羅ファイルを生成中...[/cyan]")
        console.print("[dim]   すべての記法パターンを網羅したテストファイルを作成します[/dim]")
    else:
        console.print("[cyan][設定] テスト用記法網羅ファイルを生成中...[/cyan]")
    
    # 進捗表示付きでファイル生成
    with Progress() as progress:
        task = progress.add_task("[cyan]パターン生成中", total=100)
        
        generator = TestFileGenerator(max_combinations=pattern_count)
        
        # 生成開始
        for i in range(0, 51, 10):
            progress.update(task, completed=i)
            time.sleep(0.1)
        
        output_file = generator.generate_file(test_output)
        stats = generator.get_statistics()
        
        for i in range(51, 101, 10):
            progress.update(task, completed=i)
            time.sleep(0.05)
        progress.update(task, completed=100)
    
    _display_test_stats(stats, output_file, double_click_mode)
    _test_generated_file(output_file, output, config, show_test_cases, no_preview, double_click_mode)
    return True


def _display_test_stats(stats: dict, output_file: Path, double_click_mode: bool) -> None:
    """テスト統計情報の表示"""
    if double_click_mode:
        console.print(f"[green][完了] テストファイルを生成しました:[/green] {output_file}")
        console.print(f"[dim]   [統計] 生成パターン数: {stats['total_patterns']}[/dim]")
        console.print(f"[dim]   [キーワード]  単一キーワード数: {stats['single_keywords']}[/dim]")
        console.print(f"[dim]   [生成] ハイライト色数: {stats['highlight_colors']}[/dim]")
        console.print(f"[dim]    最大組み合わせ数: {stats['max_combinations']}[/dim]")
    else:
        console.print(f"[green][完了] テストファイルを生成しました:[/green] {output_file}")
        console.print(f"[dim]   - 生成パターン数: {stats['total_patterns']}[/dim]")
        console.print(f"[dim]   - 単一キーワード数: {stats['single_keywords']}[/dim]")
        console.print(f"[dim]   - ハイライト色数: {stats['highlight_colors']}[/dim]")
        console.print(f"[dim]   - 最大組み合わせ数: {stats['max_combinations']}[/dim]")


def _test_generated_file(output_file: Path, output: str, config: str, show_test_cases: bool, 
                        no_preview: bool, double_click_mode: bool) -> None:
    """生成されたテストファイルの変換テスト"""
    if double_click_mode:
        console.print("\n[yellow][テスト] 生成されたファイルをHTMLに変換中...[/yellow]")
        console.print("[dim]   すべての記法が正しく処理されるかテストしています[/dim]")
    else:
        console.print("\n[yellow][テスト] 生成されたファイルのテスト変換を実行中...[/yellow]")
        
    try:
        config_obj = load_config(config)
        if config:
            config_obj.validate_config()
        
        test_output_file = convert_file(output_file, output or "dist", config_obj, 
                                      show_stats=False, show_test_cases=show_test_cases, template=None)
        
        _display_test_results(test_output_file, output_file, double_click_mode)
        
        if not no_preview:
            if double_click_mode:
                console.print("[blue][ブラウザ] ブラウザで結果を表示中...[/blue]")
            else:
                console.print("[blue][ブラウザ] ブラウザで開いています...[/blue]")
            webbrowser.open(test_output_file.resolve().as_uri())
            
    except Exception as e:
        console.print(f"[red][エラー] テスト変換中にエラーが発生しました: {e}[/red]")
        raise click.ClickException(f"テスト変換中にエラーが発生しました: {e}")


def _display_test_results(test_output_file: Path, output_file: Path, double_click_mode: bool) -> None:
    """テスト結果の表示"""
    if double_click_mode:
        console.print(f"[green][完了] HTML変換成功:[/green] {test_output_file}")
        console.print("[dim]   [ファイル] テストファイル (.txt) と変換結果 (.html) の両方が生成されました[/dim]")
        
        # ファイルサイズ情報を表示
        txt_size = output_file.stat().st_size
        html_size = test_output_file.stat().st_size
        console.print(f"[dim]    テキストファイル: {txt_size:,} バイト[/dim]")
        console.print(f"[dim]    HTMLファイル: {html_size:,} バイト[/dim]")
    else:
        console.print(f"[green][完了] テスト変換成功:[/green] {test_output_file}")


def copy_images(input_path, output_path, ast):
    """画像ファイルを出力ディレクトリにコピー"""
    # ASTから画像ノードを抽出
    image_nodes = [node for node in ast if getattr(node, 'type', None) == 'image']
    
    if not image_nodes:
        return
    
    # 入力ファイルのディレクトリ内の images フォルダを確認
    source_images_dir = input_path.parent / "images"
    
    if not source_images_dir.exists():
        console.print(f"[yellow]警告: images フォルダが見つかりません:[/yellow] {source_images_dir}")
        return
    
    # 出力先の images ディレクトリを作成
    dest_images_dir = output_path / "images"
    dest_images_dir.mkdir(parents=True, exist_ok=True)
    
    # 各画像ファイルをコピー
    copied_files = []
    missing_files = []
    duplicate_files = {}
    
    for node in image_nodes:
        filename = node.content
        source_file = source_images_dir / filename
        dest_file = dest_images_dir / filename
        
        if source_file.exists():
            # ファイル名の重複チェック
            if filename in copied_files:
                if filename not in duplicate_files:
                    duplicate_files[filename] = 2
                else:
                    duplicate_files[filename] += 1
            else:
                shutil.copy2(source_file, dest_file)
                copied_files.append(filename)
        else:
            missing_files.append(filename)
    
    # 結果をレポート
    if copied_files:
        console.print(f"[green]{len(copied_files)}個の画像ファイルをコピーしました[/green]")
    
    if missing_files:
        console.print(f"[red][エラー] {len(missing_files)}個の画像ファイルが見つかりません:[/red]")
        for filename in missing_files:
            console.print(f"[red]   - {filename}[/red]")
    
    if duplicate_files:
        console.print(f"[yellow][警告]  同名の画像ファイルが複数回参照されています:[/yellow]")
        for filename, count in duplicate_files.items():
            console.print(f"[yellow]   - {filename} ({count}回参照)[/yellow]")


def convert_file(input_file: str, output: str, config=None, show_stats: bool = True, 
                show_test_cases: bool = False, template: str = None, include_source: bool = False) -> Path:
    """単一ファイルの変換処理"""
    input_path = Path(input_file)
    
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # テストケース名の抽出（オプション）
    test_cases = []
    if show_test_cases:
        import re
        test_case_pattern = r'# \[TEST-(\d+)\] ([^:]+): (.+)'
        test_cases = re.findall(test_case_pattern, text)
        if test_cases:
            console.print(f"[blue][テスト] テストケース検出: {len(test_cases)}個[/blue]")
            for i, (num, category, description) in enumerate(test_cases[:5]):  # 最初の5個のみ表示
                console.print(f"[dim]   - [TEST-{num}] {category}: {description}[/dim]")
            if len(test_cases) > 5:
                console.print(f"[dim]   ... 他 {len(test_cases) - 5}個[/dim]")
    
    # パース処理
    console.print("[cyan][処理] パース中...[/cyan]")
    with Progress() as progress:
        file_size = len(text)
        task = progress.add_task("[cyan]テキストを解析中", total=100)
        
        start_time = time.time()
        ast = parse(text, config)
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:
            for i in range(0, 101, 20):
                progress.update(task, completed=i)
                time.sleep(0.05)
        progress.update(task, completed=100)
    
    # レンダリング処理
    console.print("[yellow][生成] HTML生成中...[/yellow]")
    with Progress() as progress:
        task = progress.add_task("[yellow]HTMLを生成中", total=100)
        
        start_time = time.time()
        # ソーステキストを含める場合
        if include_source:
            html = render(ast, config, template=template, title=input_path.stem, source_text=text, source_filename=input_path.name)
        else:
            html = render(ast, config, template=template, title=input_path.stem)
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:
            for i in range(0, 101, 25):
                progress.update(task, completed=i)
                time.sleep(0.04)
        progress.update(task, completed=100)
    
    # 出力ディレクトリの作成
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # HTMLファイルの書き込み
    output_file = output_path / f"{input_path.stem}.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 画像ファイルのコピー
    copy_images(input_path, output_path, ast)
    
    if show_stats:
        # エラーの統計情報を表示
        error_count = sum(1 for node in ast if getattr(node, 'type', None) == 'error')
        if error_count > 0:
            # サンプルファイルかどうかをチェック
            is_sample = input_path.name in ['02-basic.txt', '03-comprehensive.txt']
            
            if is_sample:
                console.print(f"[yellow][警告]  {error_count}個のエラーが検出されました（想定されたエラーです）[/yellow]")
                console.print("[yellow]   これらのエラーは、記法の学習用にわざと含まれています[/yellow]")
                console.print("[yellow]   HTMLファイルでエラー箇所を確認してください[/yellow]")
            else:
                console.print(f"[yellow][警告]  警告: {error_count}個のエラーが検出されました[/yellow]")
                console.print("[yellow]   HTMLファイルでエラー箇所を確認してください[/yellow]")
        
        console.print(f"[green][完了] 完了:[/green] {output_file}")
        
        # 統計情報の表示
        total_nodes = len(ast)
        console.print(f"[dim]   - 処理したブロック数: {total_nodes}[/dim]")
        console.print(f"[dim]   - ファイルサイズ: {len(text)} 文字[/dim]")
    
    return output_file


def generate_sample(output_dir: str = "kumihan_sample", use_source_toggle: bool = False):
    """サンプルファイルを生成"""
    output_path = Path(output_dir)
    
    console.print(f"[cyan][処理] サンプルを生成中: {output_path}[/cyan]")
    
    # 出力ディレクトリを作成
    output_path.mkdir(parents=True, exist_ok=True)
    
    # サンプルテキストファイルを作成
    sample_txt = output_path / "showcase.txt"
    with open(sample_txt, "w", encoding="utf-8") as f:
        f.write(SHOWCASE_SAMPLE)
    
    # 画像ディレクトリを作成
    images_dir = output_path / "images"
    images_dir.mkdir(exist_ok=True)
    
    # サンプル画像を生成
    for filename, base64_data in SAMPLE_IMAGES.items():
        image_path = images_dir / filename
        image_data = base64.b64decode(base64_data)
        with open(image_path, "wb") as f:
            f.write(image_data)
    
    # HTMLに変換（トグル機能付きテンプレートを使用）
    with Progress() as progress:
        # パース
        task = progress.add_task("[cyan]テキストを解析中", total=100)
        ast = parse(SHOWCASE_SAMPLE)
        progress.update(task, completed=100)
        
        # レンダリング（テンプレート選択）
        task = progress.add_task("[cyan]HTMLを生成中", total=100)
        if use_source_toggle:
            html = render(ast, template="base-with-source-toggle.html.j2", title="showcase", source_text=SHOWCASE_SAMPLE, source_filename="showcase.txt")
        else:
            html = render(ast, template="base.html.j2", title="showcase")
        progress.update(task, completed=100)
    
    # HTMLファイルを保存
    html_path = output_path / "showcase.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 画像はすでに正しい場所にあるため、追加のコピーは不要
    
    console.print(f"[green][完了] サンプル生成完了！[/green]")
    console.print(f"[green]   [フォルダ] 出力先: {output_path.absolute()}[/green]")
    console.print(f"[green]   [ファイル] テキスト: {sample_txt.name}[/green]")
    console.print(f"[green]   [ブラウザ] HTML: {html_path.name}[/green]")
    console.print(f"[green]   [画像]  画像: {len(SAMPLE_IMAGES)}個[/green]")
    
    # ブラウザでは開かない（--no-previewと同じ動作）
    
    return output_path


def convert_docs(docs_dir="docs", output_dir="docs_html"):
    """ドキュメントファイルをHTMLに変換"""
    docs_path = Path(docs_dir)
    output_path = Path(output_dir)
    
    console.print(f"[cyan][ドキュメント] ドキュメント変換開始: {docs_path}[/cyan]")
    
    # 対象ファイルの定義
    target_files = [
        ("readme.txt", "README"),
        ("quickstart.txt", "クイックスタートガイド"),
    ]
    
    # ユーザーマニュアルがあれば追加
    user_manual = docs_path / "user" / "USER_MANUAL.txt"
    if user_manual.exists():
        target_files.append((str(user_manual), "ユーザーマニュアル"))
    
    # 出力ディレクトリを作成
    output_path.mkdir(parents=True, exist_ok=True)
    
    converted_files = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]ドキュメント変換中", total=len(target_files))
        
        for i, (file_path, title) in enumerate(target_files):
            file_path = docs_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if file_path.exists():
                console.print(f"[yellow][ファイル] 変換中: {title}[/yellow]")
                
                # ファイルを読み込み
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # パース
                ast = parse(text)
                
                # ドキュメント用テンプレートでレンダリング
                html = render(ast, template="docs.html.j2", title=title)
                
                # HTMLファイル名を決定
                if file_path.name == "readme.txt":
                    output_file = output_path / "readme.html"
                elif file_path.name == "quickstart.txt":
                    output_file = output_path / "quickstart.html"
                elif "USER_MANUAL" in file_path.name:
                    output_file = output_path / "user-manual.html"
                else:
                    output_file = output_path / f"{file_path.stem}.html"
                
                # HTMLファイルを保存
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(html)
                
                converted_files.append((title, output_file))
                console.print(f"[green]  [完了] 完了: {output_file.name}[/green]")
            else:
                console.print(f"[yellow]  [警告]  スキップ: {file_path} (ファイルが見つかりません)[/yellow]")
            
            progress.update(task, completed=i + 1)
    
    # 結果表示
    console.print(f"\n[green][完了] ドキュメント変換完了![/green]")
    console.print(f"[green]   [フォルダ] 出力先: {output_path.absolute()}[/green]")
    console.print(f"[green]   [ファイル] 変換済みファイル: {len(converted_files)}個[/green]")
    
    for title, file_path in converted_files:
        console.print(f"[dim]   - {title}: {file_path.name}[/dim]")
    
    # インデックスファイルを作成
    index_html = generate_docs_index(converted_files, output_path)
    console.print(f"[green]    インデックス: {index_html.name}[/green]")
    
    # ブラウザで開く
    console.print(f"\n[cyan][ブラウザ] ブラウザでドキュメントを表示中...[/cyan]")
    webbrowser.open(f"file://{index_html.absolute()}")
    
    return output_path


def generate_docs_index(converted_files, output_path):
    """ドキュメント用インデックスページを生成"""
    index_content = """;;;見出し1
Kumihan-Formatter ドキュメント
;;;

このページでは、Kumihan-Formatterのすべてのドキュメントにアクセスできます。

;;;見出し2
[ドキュメント] 利用可能なドキュメント
;;;

"""
    
    for title, file_path in converted_files:
        # HTMLファイルへのリンクを追加（実際のリンクは手動で修正が必要）
        index_content += f";;;枠線\n**{title}**\n{file_path.name}\n;;;\n\n"
    
    index_content += """;;;見出し2
[リンク] その他のリソース
;;;

- GitHub リポジトリ: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
- Issues（バグ報告・要望）: GitHub Issues
- Discussions（質問・相談）: GitHub Discussions

;;;太字+ハイライト color=#e3f2fd
すべてのドキュメントはKumihan-Formatterを使って生成されています
;;;"""
    
    # インデックスファイルをHTMLに変換
    ast = parse(index_content)
    html = render(ast, template="docs.html.j2", title="ドキュメント一覧")
    
    index_file = output_path / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    return index_file


@click.group()
def cli():
    """Kumihan-Formatter - 美しい組版を、誰でも簡単に。"""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option("-o", "--output", default="dist", help="出力ディレクトリ")
@click.option("--no-preview", is_flag=True, help="HTML生成後にブラウザを開かない")
@click.option("--watch", is_flag=True, help="ファイルの変更を監視して自動再生成")
@click.option("--config", type=click.Path(exists=True), help="設定ファイルのパス")
@click.option("--generate-test", is_flag=True, help="テスト用記法網羅ファイルを生成")
@click.option("--test-output", default="test_patterns.txt", help="テストファイルの出力名")
@click.option("--pattern-count", type=int, default=100, help="生成するパターン数の上限")
@click.option("--double-click-mode", is_flag=True, help="ダブルクリック実行モード（ユーザーフレンドリーな表示）")
@click.option("--show-test-cases", is_flag=True, help="テストケース名を表示（テスト用ファイル変換時）")
@click.option("--generate-sample", "generate_sample_flag", is_flag=True, help="機能ショーケースサンプルを生成")
@click.option("--sample-output", default="kumihan_sample", help="サンプル出力ディレクトリ")
@click.option("--with-source-toggle", is_flag=True, help="記法と結果を切り替えるトグル機能付きで出力")
@click.option("--experimental", type=str, help="実験的機能を有効化 (例: scroll-sync)")
def convert(input_file, output, no_preview, watch, config, generate_test, test_output, pattern_count, double_click_mode, show_test_cases, generate_sample_flag, sample_output, with_source_toggle, experimental):
    """テキストファイルをHTMLに変換します"""
    
    try:
        # サンプル生成モードの処理
        if generate_sample_flag:
            _handle_sample_generation(output, sample_output, with_source_toggle)
            return
        
        # テストファイル生成モードの処理
        if generate_test:
            _handle_test_generation(test_output, pattern_count, double_click_mode, 
                                  output, no_preview, show_test_cases, config)
            return
        
        # 通常の変換処理
        if not input_file:
            console.print("[red][エラー] エラー:[/red] 入力ファイルが指定されていません")
            console.print("[dim]   テストファイル生成には --generate-test オプションを使用してください[/dim]")
            sys.exit(1)
        
        # 設定ファイルの読み込み
        config_obj = load_config(config)
        if config:
            config_obj.validate_config()
        
        input_path = Path(input_file)
        console.print(f"[green][ドキュメント] 読み込み中:[/green] {input_path}")
        
        # ソーストグル機能の確認（--with-source-toggleが指定されていない場合）
        use_source_toggle = with_source_toggle
        
        if not with_source_toggle:
            # すべてのファイルでYes/No確認
            console.print("\n[cyan][ヒント] 記法と結果を並べて表示する機能があります[/cyan]")
            console.print("[dim]   改行処理などの動作を実際に確認しながら記法を学習できます[/dim]")
            response = console.input("[yellow]この機能を使用しますか？ (Y/n): [/yellow]")
            use_source_toggle = response.lower() in ['y', 'yes', '']
        
        # テンプレート選択（実験的機能の考慮）
        template_name = None
        if use_source_toggle:
            if experimental == "scroll-sync":
                console.print("[yellow][実験] 実験的機能を有効化:[/yellow] スクロール同期")
                console.print("[dim]   この機能は実験的で、予期しない動作をする可能性があります[/dim]")
                template_name = "experimental/base-with-scroll-sync.html.j2"
            else:
                template_name = "base-with-source-toggle.html.j2"
        
        # 初回変換
        output_file = convert_file(input_file, output, config_obj, show_test_cases=show_test_cases, template=template_name, include_source=use_source_toggle)
        
        # ブラウザでプレビュー
        if not no_preview:
            console.print("[blue][ブラウザ] ブラウザで開いています...[/blue]")
            webbrowser.open(output_file.resolve().as_uri())
        
        # ウォッチモードの処理
        if watch:
            try:
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler
            except ImportError:
                console.print("[red][エラー] エラー:[/red] watchdog ライブラリがインストールされていません")
                console.print("[dim]   pip install watchdog を実行してください[/dim]")
                sys.exit(1)
            
            class FileChangeHandler(FileSystemEventHandler):
                def __init__(self, input_file, output, config, show_test_cases, template_name, include_source):
                    self.input_file = Path(input_file)
                    self.output = output
                    self.config = config
                    self.show_test_cases = show_test_cases
                    self.template_name = template_name
                    self.include_source = include_source
                    self.last_modified = 0
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    
                    modified_path = Path(event.src_path)
                    if modified_path.resolve() == self.input_file.resolve():
                        # 重複イベントを防ぐ
                        current_time = time.time()
                        if current_time - self.last_modified < 1:
                            return
                        self.last_modified = current_time
                        
                        try:
                            console.print(f"\n[blue][更新] ファイルが変更されました:[/blue] {modified_path.name}")
                            convert_file(self.input_file, self.output, self.config, show_stats=False, show_test_cases=self.show_test_cases, template=self.template_name, include_source=self.include_source)
                            console.print(f"[green][更新] 自動更新完了:[/green] {time.strftime('%H:%M:%S')}")
                        except Exception as e:
                            console.print(f"[red][エラー] 自動更新エラー:[/red] {e}")
            
            console.print(f"\n[cyan][監視] ファイル監視を開始:[/cyan] {input_path}")
            console.print("[dim]   ファイルを編集すると自動的に再生成されます[/dim]")
            console.print("[dim]   停止するには Ctrl+C を押してください[/dim]")
            
            event_handler = FileChangeHandler(input_file, output, config_obj, show_test_cases, template_name, use_source_toggle)
            observer = Observer()
            observer.schedule(event_handler, path=str(input_path.parent), recursive=False)
            observer.start()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow] ファイル監視を停止しました[/yellow]")
                observer.stop()
            observer.join()
            
    except FileNotFoundError as e:
        console.print(f"[red][エラー] ファイルエラー:[/red] ファイルが見つかりません: {input_file}")
        sys.exit(1)
    except UnicodeDecodeError as e:
        console.print(f"[red][エラー] エンコーディングエラー:[/red] ファイルを UTF-8 として読み込めません")
        console.print(f"[dim]   ファイル: {input_file}[/dim]")
        sys.exit(1)
    except PermissionError as e:
        console.print(f"[red][エラー] 権限エラー:[/red] ファイルにアクセスできません: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red][エラー] 予期しないエラー:[/red] {e}")
        console.print("[dim]   詳細なエラー情報が必要な場合は、GitHubのissueで報告してください[/dim]")
        sys.exit(1)


@cli.command()
@click.option("-o", "--output", default="docs_html", help="出力ディレクトリ")
@click.option("--docs-dir", default="docs", help="ドキュメントディレクトリ")
@click.option("--no-preview", is_flag=True, help="HTML生成後にブラウザを開かない")
def docs(output, docs_dir, no_preview):
    """ドキュメントをHTMLに変換します"""
    try:
        output_path = convert_docs(docs_dir, output)
        
        if not no_preview and output_path:
            index_file = output_path / "index.html"
            if index_file.exists():
                console.print(f"[cyan][ブラウザ] ブラウザでドキュメントを表示中...[/cyan]")
                webbrowser.open(f"file://{index_file.absolute()}")
        
    except Exception as e:
        console.print(f"[red][エラー] ドキュメント変換エラー:[/red] {e}")
        sys.exit(1)


def load_distignore_patterns():
    """
    .distignoreファイルから除外パターンを読み込む
    
    Returns:
        list: 除外パターンのリスト
    """
    patterns = []
    distignore_path = Path(".distignore")
    
    if distignore_path.exists():
        with open(distignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # コメント行と空行をスキップ
                if line and not line.startswith("#"):
                    patterns.append(line)
    
    return patterns


def should_exclude(path: Path, patterns: list, base_path: Path) -> bool:
    """
    指定されたパスが除外パターンに一致するかチェック
    
    Args:
        path: チェックするパス
        patterns: 除外パターンのリスト
        base_path: 基準となるパス
    
    Returns:
        bool: 除外すべきならTrue
    """
    relative_path = path.relative_to(base_path)
    relative_str = str(relative_path)
    
    for pattern in patterns:
        # ディレクトリパターンの処理
        if pattern.endswith('/'):
            # ディレクトリ配下のファイルをチェック
            dir_pattern = pattern.rstrip('/')
            
            # 完全パスマッチング
            if relative_str.startswith(dir_pattern + '/') or relative_str == dir_pattern:
                return True
            
            # 部分マッチング（ディレクトリ名）
            for part in relative_path.parts:
                if fnmatch.fnmatch(part, dir_pattern):
                    return True
        else:
            # ファイルパターンの処理
            if fnmatch.fnmatch(relative_str, pattern):
                return True
            # ファイル名のみでもマッチング
            if fnmatch.fnmatch(path.name, pattern):
                return True
    
    return False


@cli.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("-o", "--output", default="zip_distribution", help="ZIP配布用出力ディレクトリ")
@click.option("--zip-name", default="kumihan-formatter-distribution", help="ZIPファイル名（拡張子なし）")
@click.option("--convert-markdown", is_flag=True, default=True, help="Markdownファイルを自動でHTMLに変換（デフォルト: 有効）")
@click.option("--no-zip", is_flag=True, help="ZIPファイルを作成せず、ディレクトリのみ作成")
@click.option("--include-originals", is_flag=True, help="元のMarkdownファイルも同梱")
@click.option("--no-preview", is_flag=True, help="生成後にブラウザでプレビューしない")
def zip_dist(source_dir, output, zip_name, convert_markdown, no_zip, include_originals, no_preview):
    """配布用ZIPパッケージを作成します
    
    指定されたディレクトリ内の.mdファイルを自動でHTMLに変換し、
    適切なナビゲーション付きで配布用ZIPを作成します。
    同人作家など技術知識のないユーザー向けに最適化されています。
    """
    import zipfile
    import tempfile
    
    try:
        source_path = Path(source_dir)
        output_path = Path(output)
        
        console.print(f"[green][ZIP配布] 配布パッケージ作成開始:[/green] {source_path}")
        
        # 除外パターンを読み込み
        exclude_patterns = load_distignore_patterns()
        if exclude_patterns:
            console.print(f"[blue][除外設定] .distignoreから{len(exclude_patterns)}個の除外パターンを読み込みました[/blue]")
        
        # 作業用一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "distribution"
            temp_path.mkdir(parents=True, exist_ok=True)
            
            console.print("[cyan][コピー] ソースファイルをコピー中...[/cyan]")
            
            # ソースディレクトリの全内容をコピー（除外パターンを適用）
            copied_count = 0
            excluded_count = 0
            
            for item in source_path.rglob("*"):
                if item.is_file():
                    # 除外チェック
                    if should_exclude(item, exclude_patterns, source_path):
                        excluded_count += 1
                        continue
                    
                    relative_path = item.relative_to(source_path)
                    dest_path = temp_path / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
                    copied_count += 1
            
            console.print(f"[green][コピー完了] {copied_count}個のファイルをコピー[/green]")
            if excluded_count > 0:
                console.print(f"[yellow][除外] {excluded_count}個のファイルを除外[/yellow]")
            
            # Markdownファイルの変換処理
            if convert_markdown:
                console.print("[yellow][変換] Markdownファイルを検索・HTML変換中...[/yellow]")
                
                # Markdownファイルを検出
                md_files = list(temp_path.rglob("*.md"))
                
                if md_files:
                    console.print(f"[blue][検出] {len(md_files)}個のMarkdownファイルを発見[/blue]")
                    
                    # HTML変換を実行
                    converted_files = convert_markdown_to_html(temp_path, temp_path)
                    
                    console.print(f"[green][変換完了] {len(converted_files)}個のHTMLファイルを生成[/green]")
                    
                    # 元のMarkdownファイルを削除（include_originalsが無効な場合）
                    if not include_originals:
                        console.print("[yellow][クリーンアップ] 元のMarkdownファイルを削除中...[/yellow]")
                        for md_file in md_files:
                            if md_file.exists():
                                md_file.unlink()
                        console.print("[green][完了] 元ファイルのクリーンアップ完了[/green]")
                    else:
                        console.print("[blue][保持] 元のMarkdownファイルも配布パッケージに同梱[/blue]")
                else:
                    console.print("[yellow][情報] Markdownファイルが見つかりませんでした[/yellow]")
            else:
                console.print("[blue][スキップ] Markdown変換をスキップ[/blue]")
            
            # 出力ディレクトリを準備
            output_path.mkdir(parents=True, exist_ok=True)
            
            if no_zip:
                # ZIPファイルを作成せず、ディレクトリのみコピー
                final_dir = output_path / zip_name
                if final_dir.exists():
                    shutil.rmtree(final_dir)
                shutil.copytree(temp_path, final_dir)
                console.print(f"[green][完了] 配布ディレクトリを作成:[/green] {final_dir}")
                
                # プレビュー
                if not no_preview:
                    index_file = final_dir / "index.html"
                    if index_file.exists():
                        console.print("[blue][プレビュー] ブラウザでプレビューを表示中...[/blue]")
                        webbrowser.open(index_file.resolve().as_uri())
                
            else:
                # ZIPファイルを作成
                zip_file_path = output_path / f"{zip_name}.zip"
                
                console.print(f"[cyan][圧縮] ZIPファイル作成中:[/cyan] {zip_file_path.name}")
                
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                    for file_path in temp_path.rglob("*"):
                        if file_path.is_file():
                            archive_name = file_path.relative_to(temp_path)
                            zipf.write(file_path, archive_name)
                
                # ZIPファイル情報を表示
                zip_size = zip_file_path.stat().st_size
                size_mb = zip_size / (1024 * 1024)
                console.print(f"[green][完了] ZIPファイル作成完了:[/green] {zip_file_path}")
                console.print(f"[dim]   ファイルサイズ: {size_mb:.2f} MB[/dim]")
                
                # ZIPの中身をプレビュー用に展開
                if not no_preview:
                    preview_dir = output_path / f"{zip_name}_preview"
                    if preview_dir.exists():
                        shutil.rmtree(preview_dir)
                    
                    with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                        zipf.extractall(preview_dir)
                    
                    index_file = preview_dir / "index.html"
                    if index_file.exists():
                        console.print("[blue][プレビュー] ブラウザでプレビューを表示中...[/blue]")
                        webbrowser.open(index_file.resolve().as_uri())
            
            console.print("[green][成功] 配布パッケージの作成が完了しました！[/green]")
            
    except Exception as e:
        console.print(f"[red][エラー] 配布パッケージ作成エラー:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    cli()