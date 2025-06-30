"""Distribution Structure Manager

配布構造管理システム - Issue #118対応
エンドユーザー向け配布物の構造と文書変換を管理する
"""

import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .doc_classifier import DocumentClassifier, DocumentType
from .markdown_converter import SimpleMarkdownConverter, convert_markdown_file


class DistributionManager:
    """配布構造管理器

    エンドユーザー向けの配布物を作成・管理する
    """

    def __init__(self, ui=None):
        """配布管理器を初期化

        Args:
            ui: UIインスタンス（進捗表示用）
        """
        self.ui = ui
        self.classifier = DocumentClassifier()
        self.markdown_converter = SimpleMarkdownConverter()

    def create_user_friendly_distribution(
        self,
        source_dir: Path,
        output_dir: Path,
        convert_docs: bool = True,
        include_developer_docs: bool = False,
    ) -> Dict[str, int]:
        """ユーザーフレンドリーな配布構造を作成

        Args:
            source_dir: ソースディレクトリ
            output_dir: 出力ディレクトリ
            convert_docs: 文書変換を実行するか
            include_developer_docs: 開発者向け文書を含めるか

        Returns:
            Dict: 処理統計（変換ファイル数等）
        """
        stats = {
            "total_files": 0,
            "converted_to_html": 0,
            "converted_to_txt": 0,
            "copied_as_is": 0,
            "excluded": 0,
        }

        if self.ui:
            self.ui.info("配布用文書構造の作成を開始")

        # ファイル分類
        classified_files = self.classifier.classify_directory(source_dir)
        stats["total_files"] = sum(len(files) for files in classified_files.values())

        if self.ui:
            self.ui.info(f"文書分類完了: {stats['total_files']}件のファイルを処理")

        # 配布構造を作成
        self._create_distribution_structure(output_dir)

        # 文書変換と配置
        if convert_docs:
            stats.update(
                self._process_document_conversion(
                    classified_files, source_dir, output_dir, include_developer_docs
                )
            )

        # メインプログラムファイルの処理
        stats.update(self._copy_program_files(classified_files, source_dir, output_dir))

        # インデックスファイルの作成
        self._create_documentation_index(output_dir, classified_files)

        # 配布情報ファイルの作成
        self._create_distribution_info(output_dir, stats)

        if self.ui:
            self.ui.success("配布構造の作成が完了")
            self._report_statistics(stats)

        return stats

    def _create_distribution_structure(self, output_dir: Path) -> None:
        """配布用ディレクトリ構造を作成"""
        directories = [
            "docs/essential",  # 最重要文書（.txt）
            "docs/user",  # ユーザーガイド（HTML）
            "docs/developer",  # 開発者文書（必要時）
            "docs/technical",  # 技術文書（必要時）
            "examples",  # サンプルファイル
            "kumihan_formatter",  # メインプログラム
        ]

        for dir_path in directories:
            (output_dir / dir_path).mkdir(parents=True, exist_ok=True)

    def _process_document_conversion(
        self,
        classified_files: Dict[DocumentType, List[Path]],
        source_dir: Path,
        output_dir: Path,
        include_developer_docs: bool,
    ) -> Dict[str, int]:
        """文書変換処理"""
        stats = {"converted_to_html": 0, "converted_to_txt": 0, "copied_as_is": 0}

        # ユーザー重要文書（.txt変換）
        for file_path in classified_files[DocumentType.USER_ESSENTIAL]:
            self._convert_to_txt(file_path, source_dir, output_dir / "docs/essential")
            stats["converted_to_txt"] += 1

        # ユーザーガイド（HTML変換）
        for file_path in classified_files[DocumentType.USER_GUIDE]:
            self._convert_to_html(file_path, source_dir, output_dir / "docs/user")
            stats["converted_to_html"] += 1

        # 開発者・技術文書（必要時のみ）
        if include_developer_docs:
            for file_path in classified_files[DocumentType.DEVELOPER]:
                self._copy_file_as_is(
                    file_path, source_dir, output_dir / "docs/developer"
                )
                stats["copied_as_is"] += 1

            for file_path in classified_files[DocumentType.TECHNICAL]:
                self._copy_file_as_is(
                    file_path, source_dir, output_dir / "docs/technical"
                )
                stats["copied_as_is"] += 1

        return stats

    def _copy_program_files(
        self,
        classified_files: Dict[DocumentType, List[Path]],
        source_dir: Path,
        output_dir: Path,
    ) -> Dict[str, int]:
        """メインプログラムファイルの処理"""
        stats = {"copied_as_is": 0}

        # サンプルファイル
        for file_path in classified_files[DocumentType.EXAMPLE]:
            relative_path = file_path.relative_to(source_dir)
            target_path = output_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_path)
            stats["copied_as_is"] += 1

        # メインプログラム（kumihan_formatter/ 以下）
        kumihan_formatter_dir = source_dir / "kumihan_formatter"
        if kumihan_formatter_dir.exists():
            target_dir = output_dir / "kumihan_formatter"
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(kumihan_formatter_dir, target_dir)

            # Python ファイル数をカウント
            py_files = list(target_dir.rglob("*.py"))
            stats["copied_as_is"] += len(py_files)

        # セットアップファイル
        setup_files = ["setup_windows.bat", "setup_macos.command", "pyproject.toml"]
        for filename in setup_files:
            setup_file = source_dir / filename
            if setup_file.exists():
                shutil.copy2(setup_file, output_dir / filename)
                stats["copied_as_is"] += 1

        return stats

    def _convert_to_txt(
        self, file_path: Path, source_dir: Path, output_dir: Path
    ) -> None:
        """MarkdownファイルをプレーンテキストIDに変換"""
        try:
            # Markdownを読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 簡単なMarkdown→テキスト変換
            text_content = self._markdown_to_plain_text(content)

            # 出力ファイル名を決定
            output_filename = self._get_user_friendly_filename(file_path, ".txt")
            output_file = output_dir / output_filename

            # テキストファイルとして保存
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text_content)

            if self.ui:
                self.ui.info(f"TXT変換: {file_path.name} → {output_filename}")

        except Exception as e:
            if self.ui:
                self.ui.warning(f"TXT変換失敗: {file_path.name} - {e}")

    def _convert_to_html(
        self, file_path: Path, source_dir: Path, output_dir: Path
    ) -> None:
        """MarkdownファイルをHTMLに変換"""
        try:
            # 出力ファイル名を決定
            output_filename = self._get_user_friendly_filename(file_path, ".html")
            output_file = output_dir / output_filename

            # タイトルを生成
            title = self._generate_title_from_filename(file_path)

            # Markdown→HTML変換
            success = convert_markdown_file(file_path, output_file, title)

            if success and self.ui:
                self.ui.info(f"HTML変換: {file_path.name} → {output_filename}")
            elif not success and self.ui:
                self.ui.warning(f"HTML変換失敗: {file_path.name}")

        except Exception as e:
            if self.ui:
                self.ui.warning(f"HTML変換失敗: {file_path.name} - {e}")

    def _copy_file_as_is(
        self, file_path: Path, source_dir: Path, output_dir: Path
    ) -> None:
        """ファイルをそのままコピー"""
        try:
            relative_path = file_path.relative_to(source_dir)
            target_file = output_dir / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_file)

        except Exception as e:
            if self.ui:
                self.ui.warning(f"ファイルコピー失敗: {file_path.name} - {e}")

    def _markdown_to_plain_text(self, markdown_content: str) -> str:
        """Markdownをプレーンテキストに変換"""
        # 基本的なMarkdown記法を除去
        text = markdown_content

        # 見出しマーカーを除去
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # リンクからテキスト部分のみを抽出
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # 強調記法を除去
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # コードブロックのマーカーを除去
        text = re.sub(r"```.*?\n", "", text)
        text = re.sub(r"```", "", text)

        # インラインコードのマーカーを除去
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 水平線を除去
        text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)

        # 複数の空行を単一の空行に変換
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        return text.strip()

    def _get_user_friendly_filename(self, file_path: Path, new_extension: str) -> str:
        """ユーザーフレンドリーなファイル名を生成"""
        # ファイル名のマッピング
        name_mappings = {
            "readme.md": f"はじめに{new_extension}",
            "install.md": f"インストール方法{new_extension}",
            "usage.md": f"使い方ガイド{new_extension}",
            "troubleshooting.md": f"トラブルシューティング{new_extension}",
            "faq.md": f"よくある質問{new_extension}",
            "tutorial.md": f"チュートリアル{new_extension}",
            "quickstart.md": f"クイックスタート{new_extension}",
            "license": f"ライセンス{new_extension}",
            "contributing.md": f"開発参加ガイド{new_extension}",
        }

        filename_lower = file_path.name.lower()
        return name_mappings.get(filename_lower, file_path.stem + new_extension)

    def _generate_title_from_filename(self, file_path: Path) -> str:
        """ファイル名からタイトルを生成"""
        title_mappings = {
            "readme.md": "はじめに",
            "install.md": "インストール方法",
            "usage.md": "使い方ガイド",
            "troubleshooting.md": "トラブルシューティング",
            "faq.md": "よくある質問",
            "tutorial.md": "チュートリアル",
            "quickstart.md": "クイックスタート",
        }

        filename_lower = file_path.name.lower()
        return title_mappings.get(filename_lower, file_path.stem)

    def _create_documentation_index(
        self, output_dir: Path, classified_files: Dict[DocumentType, List[Path]]
    ) -> None:
        """文書インデックスページを作成"""
        index_content = self._generate_index_html(classified_files)
        index_file = output_dir / "docs" / "index.html"

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_content)

        if self.ui:
            self.ui.info("文書インデックスを作成: docs/index.html")

    def _generate_index_html(
        self, classified_files: Dict[DocumentType, List[Path]]
    ) -> str:
        """インデックスHTMLを生成"""
        generation_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan-Formatter ドキュメント</title>
    <style>
        body {{
            font-family: 'Hiragino Kaku Gothic Pro', 'ヒラギノ角ゴ Pro', 'Yu Gothic', 'メイリオ', Meiryo, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4a90e2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 2em;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        .doc-section {{
            margin: 1.5em 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #4a90e2;
        }}
        .doc-list {{
            list-style-type: none;
            padding: 0;
        }}
        .doc-list li {{
            margin: 0.5em 0;
            padding: 8px 12px;
            background-color: white;
            border-radius: 3px;
            border: 1px solid #e0e0e0;
        }}
        .doc-list a {{
            color: #4a90e2;
            text-decoration: none;
            font-weight: bold;
        }}
        .doc-list a:hover {{
            text-decoration: underline;
        }}
        .doc-description {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .footer {{
            margin-top: 3em;
            padding: 15px;
            background-color: #f0f0f0;
            border-radius: 5px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Kumihan-Formatter ドキュメント</h1>
        
        <p>Kumihan-Formatter をご利用いただき、ありがとうございます。<br>
        このページでは、利用可能な文書を種類別に整理してご案内しています。</p>
        
        <div class="doc-section">
            <h2>🎯 まず最初に読む文書</h2>
            <p>Kumihan-Formatter を使い始める前に、必ずお読みください。</p>
            <ul class="doc-list">
                <li>
                    <a href="essential/はじめに.txt">📄 はじめに.txt</a>
                    <div class="doc-description">Kumihan-Formatter の概要と基本的な使い方</div>
                </li>
                <li>
                    <a href="essential/クイックスタート.txt">⚡ クイックスタート.txt</a>
                    <div class="doc-description">すぐに使い始めるための簡単な手順</div>
                </li>
                <li>
                    <a href="essential/ライセンス.txt">📜 ライセンス.txt</a>
                    <div class="doc-description">利用条件とライセンス情報</div>
                </li>
            </ul>
        </div>
        
        <div class="doc-section">
            <h2>📖 詳しい使い方ガイド</h2>
            <p>より詳細な使い方や高度な機能について説明しています。</p>
            <ul class="doc-list">
                <li>
                    <a href="user/インストール方法.html">💾 インストール方法</a>
                    <div class="doc-description">詳細なインストール手順と環境設定</div>
                </li>
                <li>
                    <a href="user/使い方ガイド.html">📚 使い方ガイド</a>
                    <div class="doc-description">基本機能から応用機能まで詳しく解説</div>
                </li>
                <li>
                    <a href="user/トラブルシューティング.html">🔧 トラブルシューティング</a>
                    <div class="doc-description">よくある問題と解決方法</div>
                </li>
                <li>
                    <a href="user/よくある質問.html">❓ よくある質問</a>
                    <div class="doc-description">ユーザーからよく寄せられる質問と回答</div>
                </li>
            </ul>
        </div>
        
        <div class="doc-section">
            <h2>📝 サンプルファイル</h2>
            <p>実際に試せるサンプルファイルと実例集です。</p>
            <ul class="doc-list">
                <li>
                    <a href="../examples/">📁 examples フォルダ</a>
                    <div class="doc-description">様々なサンプルファイルと実用例</div>
                </li>
            </ul>
        </div>
        
        <div class="footer">
            このドキュメントは {generation_time} に自動生成されました。<br>
            Kumihan-Formatter v0.3.0 | <a href="https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter" target="_blank">GitHub</a>
        </div>
    </div>
</body>
</html>"""

    def _create_distribution_info(
        self, output_dir: Path, stats: Dict[str, int]
    ) -> None:
        """配布情報ファイルを作成"""
        info_content = self._generate_distribution_info(stats)
        info_file = output_dir / "配布情報.txt"

        with open(info_file, "w", encoding="utf-8") as f:
            f.write(info_content)

    def _generate_distribution_info(self, stats: Dict[str, int]) -> str:
        """配布情報テキストを生成"""
        generation_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        return f"""Kumihan-Formatter 配布パッケージ
================================

配布日時: {generation_time}
バージョン: 0.3.0

📦 パッケージ内容
----------------
・docs/essential/     重要文書（.txt形式）
・docs/user/          ユーザーガイド（HTML形式）  
・examples/           サンプルファイル・実例集
・kumihan_formatter/  メインプログラム

📊 処理統計
----------
・総ファイル数: {stats['total_files']}件
・HTML変換: {stats['converted_to_html']}件
・TXT変換: {stats['converted_to_txt']}件  
・そのままコピー: {stats['copied_as_is']}件
・除外: {stats['excluded']}件

🚀 使い始め方
------------
1. docs/essential/はじめに.txt をお読みください
2. docs/essential/クイックスタート.txt で基本操作を確認
3. examples/ フォルダでサンプルファイルをお試しください
4. 詳しい説明は docs/index.html をブラウザで開いてご覧ください

💡 ヘルプ・サポート
-----------------
・トラブルシューティング: docs/user/トラブルシューティング.html
・よくある質問: docs/user/よくある質問.html
・GitHub: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter

このパッケージは同人作家など、技術知識のない方でも
簡単にお使いいただけるよう配慮して作成されています。

Kumihan-Formatter をお楽しみください！
"""

    def _report_statistics(self, stats: Dict[str, int]) -> None:
        """統計レポートを出力"""
        if self.ui:
            self.ui.info("📊 配布構造作成統計:")
            self.ui.info(f"  総ファイル数: {stats['total_files']}件")
            self.ui.info(f"  HTML変換: {stats['converted_to_html']}件")
            self.ui.info(f"  TXT変換: {stats['converted_to_txt']}件")
            self.ui.info(f"  コピー: {stats['copied_as_is']}件")


def create_user_distribution(
    source_dir: Path,
    output_dir: Path,
    convert_docs: bool = True,
    include_developer_docs: bool = False,
    ui=None,
) -> Dict[str, int]:
    """ユーザー向け配布物を作成（外部API）

    Args:
        source_dir: ソースディレクトリ
        output_dir: 出力ディレクトリ
        convert_docs: 文書変換を行うか
        include_developer_docs: 開発者向け文書を含めるか
        ui: UIインスタンス

    Returns:
        Dict: 処理統計
    """
    manager = DistributionManager(ui)
    return manager.create_user_friendly_distribution(
        source_dir, output_dir, convert_docs, include_developer_docs
    )
