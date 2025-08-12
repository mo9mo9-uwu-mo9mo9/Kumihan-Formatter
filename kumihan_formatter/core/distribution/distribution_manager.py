"""
配布管理 - メイン制御

配布構造管理のメイン制御とオーケストレーション
Issue #319対応 - distribution_manager.py から分離
"""

from pathlib import Path

from ..doc_classifier import DocumentClassifier, DocumentType
from .distribution_converter import DistributionConverter
from .distribution_processor import DistributionProcessor
from .distribution_structure import DistributionStructure


class DistributionManager:
    """配布構造管理器

    責任: 配布構造作成の全体制御・各処理のオーケストレーション
    """

    def __init__(self, ui=None) -> None:
        """配布管理器を初期化

        Args:
            ui: UIインスタンス（進捗表示用）
        """
        self.ui = ui
        self.classifier = DocumentClassifier()
        self.structure = DistributionStructure(ui)
        self.converter = DistributionConverter(ui)
        self.processor = DistributionProcessor(ui)

    def create_user_friendly_distribution(
        self,
        source_dir: Path,
        output_dir: Path,
        convert_docs: bool = True,
        include_developer_docs: bool = False,
    ) -> dict[str, int]:
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
        self.structure.create_structure(output_dir)

        # 文書変換と配置
        if convert_docs:
            conversion_stats = self._process_document_conversion(
                classified_files, output_dir, include_developer_docs
            )
            stats.update(conversion_stats)

        # メインプログラムファイルの処理
        program_stats = self.processor.copy_program_files(
            classified_files, source_dir, output_dir
        )
        stats["copied_as_is"] += program_stats["copied_as_is"]

        # インデックスファイルの作成
        self._create_documentation_index(output_dir, classified_files)

        # 配布情報ファイルの作成
        self.processor.create_distribution_info(output_dir, stats)

        if self.ui:
            self.ui.success("配布構造の作成が完了")
            self.processor.report_statistics(stats)

        return stats

    def _process_document_conversion(
        self,
        classified_files: dict[DocumentType, list[Path]],
        output_dir: Path,
        include_developer_docs: bool,
    ) -> dict[str, int]:
        """文書変換処理を実行"""
        stats = {"converted_to_html": 0, "converted_to_txt": 0, "copied_as_is": 0}

        # ユーザー重要文書（.txt変換）
        essential_dir = self.structure.get_target_directory(output_dir, "essential")
        for file_path in classified_files[DocumentType.USER_ESSENTIAL]:
            if self.converter.convert_to_txt(file_path, essential_dir):
                stats["converted_to_txt"] += 1

        # ユーザーガイド（HTML変換）
        user_dir = self.structure.get_target_directory(output_dir, "user")
        for file_path in classified_files[DocumentType.USER_GUIDE]:
            if self.converter.convert_to_html(file_path, user_dir):
                stats["converted_to_html"] += 1

        # 開発者・技術文書（必要時のみ）
        if include_developer_docs:
            dev_dir = self.structure.get_target_directory(output_dir, "developer")
            tech_dir = self.structure.get_target_directory(output_dir, "technical")

            for file_path in classified_files[DocumentType.DEVELOPER]:
                if self.processor._copy_file_as_is(
                    file_path, file_path.parent, dev_dir
                ):
                    stats["copied_as_is"] += 1

            for file_path in classified_files[DocumentType.TECHNICAL]:
                if self.processor._copy_file_as_is(
                    file_path, file_path.parent, tech_dir
                ):
                    stats["copied_as_is"] += 1

        return stats

    def _create_documentation_index(
        self, output_dir: Path, classified_files: dict[DocumentType, list[Path]]
    ) -> None:
        """文書インデックスを作成"""
        index_content = self._generate_index_html(classified_files)
        index_file = output_dir / "docs" / "index.html"

        try:
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(index_content)

            if self.ui:
                self.ui.info("文書インデックスを作成: docs/index.html")

        except Exception as e:
            if self.ui:
                self.ui.warning(f"インデックス作成失敗: {e}")

    def _generate_index_html(
        self, classified_files: dict[DocumentType, list[Path]]
    ) -> str:
        """インデックスHTMLを生成（簡略版）"""
        from datetime import datetime

        generation_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # 基本的なHTMLテンプレート
        return f"""<!DOCTYPE html>

            <li><a href="essential/はじめに.txt">はじめに.txt</a></li>
            <li><a href="essential/インストール方法.txt">インストール方法.txt</a></li>
        </ul>
    </div>

    <div class="section">
        <h2>📚 ユーザーガイド</h2>
        <p>詳細な使用方法（HTML形式）</p>
        <ul>
            <li><a href="user/使い方ガイド.html">使い方ガイド.html</a></li>
            <li><a href="user/トラブルシューティング.html">トラブルシューティング.html</a></li>
        </ul>
    </div>

    <footer style="margin-top: 50px; text-align: center; color: #666;">
        <p>生成日時: {generation_time}</p>
    </footer>
</body>
</html>"""
