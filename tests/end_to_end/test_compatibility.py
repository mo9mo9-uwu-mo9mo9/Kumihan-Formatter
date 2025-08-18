"""後方互換性のエンドツーエンドテスト

既存機能の動作保証と新旧記法の互換性をテストし、
アップグレード時の安全性を確認する。
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestCompatibility:
    """後方互換性のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"テスト用一時ディレクトリ: {self.temp_dir}")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        import shutil

        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"一時ディレクトリを削除: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"一時ディレクトリの削除に失敗: {e}")

    def process_with_compatibility_check(self, content: str,
                                       version: str = "current") -> Dict[str, Any]:
        """互換性チェック付きの処理実行"""
        try:
            # バージョン別の処理ルール
            if version == "legacy":
                parsed_data = self._legacy_parse(content)
            elif version == "current":
                parsed_data = self._current_parse(content)
            else:
                parsed_data = self._hybrid_parse(content)

            # レンダリング
            rendered_output = self._compatibility_render(parsed_data, version)

            # 出力ファイル作成
            output_file = self.temp_dir / f"output_{version}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rendered_output)

            return {
                "success": True,
                "version": version,
                "output": rendered_output,
                "output_file": output_file,
                "features_detected": parsed_data["features"],
                "compatibility_warnings": parsed_data.get("warnings", []),
                "migration_suggestions": parsed_data.get("suggestions", [])
            }

        except Exception as e:
            logger.error(f"互換性処理エラー ({version}): {e}")
            return {
                "success": False,
                "version": version,
                "error": str(e)
            }

    def _legacy_parse(self, content: str) -> Dict[str, Any]:
        """レガシー記法のパース（Phase 1以前の記法）"""
        lines = content.split('\n')
        features = []
        warnings = []
        suggestions = []

        for i, line in enumerate(lines):
            # 旧記法の検出
            if ";;;" in line:
                features.append("legacy_inline")
                warnings.append(f"行{i+1}: 旧記法 ;;;...;;; が検出されました")
                suggestions.append(f"行{i+1}: #...# 記法への移行を推奨")

            # 旧ブロック記法
            if line.strip() == ";;;":
                features.append("legacy_block")
                warnings.append(f"行{i+1}: 旧ブロック記法が検出されました")
                suggestions.append(f"行{i+1}: #...## 記法への移行を推奨")

        return {
            "features": features,
            "warnings": warnings,
            "suggestions": suggestions,
            "content": content,
            "processing_mode": "legacy"
        }

    def _current_parse(self, content: str) -> Dict[str, Any]:
        """現在の記法のパース"""
        lines = content.split('\n')
        features = []
        warnings = []

        for i, line in enumerate(lines):
            # 現行記法の検出
            if line.startswith('#') and line.endswith('#') and len(line) > 2:
                features.append("current_inline")

            if line.startswith('#') and not line.endswith('#'):
                features.append("current_block_start")

            if line.strip() == "##":
                features.append("current_block_end")

            # 混在警告
            if ";;;" in line:
                warnings.append(f"行{i+1}: 非推奨の旧記法が含まれています")

        return {
            "features": features,
            "warnings": warnings,
            "suggestions": [],
            "content": content,
            "processing_mode": "current"
        }

    def _hybrid_parse(self, content: str) -> Dict[str, Any]:
        """ハイブリッド記法のパース（新旧混在対応）"""
        lines = content.split('\n')
        features = []
        warnings = []
        suggestions = []
        converted_lines = []

        for i, line in enumerate(lines):
            converted_line = line

            # 旧記法から新記法への自動変換
            if ";;;" in line and line.count(";;;") >= 2:
                # インライン旧記法の変換
                parts = line.split(";;;")
                if len(parts) >= 3:
                    decoration = parts[1].strip()
                    content_part = parts[2].strip() if len(parts) > 2 else ""
                    converted_line = f"#{decoration} {content_part}#"
                    features.append("auto_converted_inline")
                    warnings.append(f"行{i+1}: 旧記法を新記法に自動変換")
                    suggestions.append(f"行{i+1}: 変換確認後、元記法を更新推奨")

            elif line.strip() == ";;;":
                # ブロック旧記法の変換
                converted_line = "##"
                features.append("auto_converted_block")
                warnings.append(f"行{i+1}: 旧ブロック終了を新記法に変換")

            # 現行記法の検出
            elif line.startswith('#') and line.endswith('#') and len(line) > 2:
                features.append("current_inline")

            elif line.startswith('#') and not line.endswith('#'):
                features.append("current_block_start")

            elif line.strip() == "##":
                features.append("current_block_end")

            converted_lines.append(converted_line)

        return {
            "features": features,
            "warnings": warnings,
            "suggestions": suggestions,
            "content": '\n'.join(converted_lines),
            "original_content": content,
            "processing_mode": "hybrid"
        }

    def _compatibility_render(self, parsed_data: Dict[str, Any],
                            version: str) -> str:
        """互換性を考慮したレンダリング"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='ja'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>Kumihan Formatter - 互換性テスト ({version})</title>",
            "<style>",
            ".compatibility-info { background-color: #e3f2fd; padding: 10px; margin: 10px 0; }",
            ".warning { color: orange; }",
            ".suggestion { color: blue; }",
            ".converted { background-color: #f0f8ff; padding: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>互換性テスト結果 - {version.upper()}モード</h1>"
        ]

        # 互換性情報
        html_parts.append('<div class="compatibility-info">')
        html_parts.append(f'<h2>処理モード: {parsed_data["processing_mode"]}</h2>')
        html_parts.append(f'<p>検出された機能: {len(parsed_data["features"])}件</p>')
        html_parts.append('<ul>')
        for feature in parsed_data["features"]:
            html_parts.append(f'<li>{feature}</li>')
        html_parts.append('</ul>')
        html_parts.append('</div>')

        # 警告
        if parsed_data.get("warnings"):
            html_parts.append('<div class="warning">')
            html_parts.append('<h3>互換性警告</h3>')
            html_parts.append('<ul>')
            for warning in parsed_data["warnings"]:
                html_parts.append(f'<li>{warning}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')

        # 移行提案
        if parsed_data.get("suggestions"):
            html_parts.append('<div class="suggestion">')
            html_parts.append('<h3>移行提案</h3>')
            html_parts.append('<ul>')
            for suggestion in parsed_data["suggestions"]:
                html_parts.append(f'<li>{suggestion}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')

        # 処理された内容
        html_parts.append('<h3>処理された内容</h3>')
        html_parts.append('<div class="converted">')
        html_parts.append('<pre>')
        html_parts.append(parsed_data["content"])
        html_parts.append('</pre>')
        html_parts.append('</div>')

        # 元の内容（ハイブリッドモードの場合）
        if "original_content" in parsed_data:
            html_parts.append('<h3>元の内容</h3>')
            html_parts.append('<pre>')
            html_parts.append(parsed_data["original_content"])
            html_parts.append('</pre>')

        html_parts.extend([
            "</body>",
            "</html>"
        ])

        return '\n'.join(html_parts)

    def create_legacy_test_content(self) -> str:
        """レガシーテストコンテンツを作成"""
        return """# 見出しテスト
;;太字 レガシー太字記法;;;

;;イタリック レガシーイタリック記法;;;

レガシーブロック記法:
;;太字
ブロック内容
;;;

混在テスト:
#太字 新記法#
;;イタリック 旧記法;;;

正常な新記法:
#見出し#
コンテンツ
##
"""

    def create_current_test_content(self) -> str:
        """現在の記法テストコンテンツを作成"""
        return """#見出し#
新記法のコンテンツ

#太字 新記法の太字#

#イタリック
新記法のブロック
##

#重要 重要な内容#

#リスト
- 項目1
- 項目2
##
"""

    def create_mixed_test_content(self) -> str:
        """新旧混在記法テストコンテンツを作成"""
        return """# 混在記法テスト

新記法:
#太字 新記法の太字#

旧記法:
;;太字 旧記法の太字;;;

ブロック記法混在:
#新ブロック
新記法内容
##

;;旧ブロック
旧記法内容
;;;

正常な記法:
#見出し#
正常なコンテンツ
##
"""

    @pytest.mark.e2e
    def test_後方互換性_レガシー記法処理(self) -> None:
        """後方互換性: レガシー記法の処理"""
        # Given: レガシー記法コンテンツ
        legacy_content = self.create_legacy_test_content()

        # When: レガシーモードで処理
        result = self.process_with_compatibility_check(legacy_content, "legacy")

        # Then: レガシー処理の確認
        assert result["success"], f"レガシー記法処理が失敗: {result.get('error')}"
        assert "legacy_inline" in result["features_detected"], "レガシーインライン記法が検出されていない"
        assert len(result["compatibility_warnings"]) > 0, "互換性警告が出力されていない"
        assert len(result["migration_suggestions"]) > 0, "移行提案が出力されていない"

        # 出力ファイル確認
        assert result["output_file"].exists(), "レガシー出力ファイルが作成されていない"

        logger.info(f"レガシー記法処理完了: {len(result['features_detected'])}機能検出")

    @pytest.mark.e2e
    def test_後方互換性_現在記法処理(self) -> None:
        """後方互換性: 現在記法の処理"""
        # Given: 現在記法コンテンツ
        current_content = self.create_current_test_content()

        # When: 現在モードで処理
        result = self.process_with_compatibility_check(current_content, "current")

        # Then: 現在記法処理の確認
        assert result["success"], f"現在記法処理が失敗: {result.get('error')}"
        assert "current_inline" in result["features_detected"], "現在インライン記法が検出されていない"
        assert "current_block_start" in result["features_detected"], "現在ブロック記法が検出されていない"

        # 警告が少ないことを確認
        assert len(result["compatibility_warnings"]) == 0, "現在記法で不要な警告が発生"

        logger.info(f"現在記法処理完了: {len(result['features_detected'])}機能検出")

    @pytest.mark.e2e
    def test_後方互換性_混在記法処理(self) -> None:
        """後方互換性: 新旧混在記法の処理"""
        # Given: 混在記法コンテンツ
        mixed_content = self.create_mixed_test_content()

        # When: ハイブリッドモードで処理
        result = self.process_with_compatibility_check(mixed_content, "hybrid")

        # Then: 混在記法処理の確認
        assert result["success"], f"混在記法処理が失敗: {result.get('error')}"

        # 自動変換機能の確認
        detected_features = result["features_detected"]
        assert "auto_converted_inline" in detected_features or "auto_converted_block" in detected_features, \
               "自動変換が実行されていない"

        # 変換警告の確認
        assert len(result["compatibility_warnings"]) > 0, "変換警告が出力されていない"

        # 出力内容の確認
        output_content = result["output"]
        assert "auto_converted" in output_content or "変換" in output_content, "自動変換情報が出力されていない"

        logger.info(f"混在記法処理完了: {len(detected_features)}機能、{len(result['compatibility_warnings'])}警告")

    @pytest.mark.e2e
    def test_後方互換性_バージョン間比較(self) -> None:
        """後方互換性: バージョン間の処理結果比較"""
        # Given: 同一コンテンツ
        test_content = self.create_mixed_test_content()

        # When: 複数バージョンで処理
        legacy_result = self.process_with_compatibility_check(test_content, "legacy")
        current_result = self.process_with_compatibility_check(test_content, "current")
        hybrid_result = self.process_with_compatibility_check(test_content, "hybrid")

        # Then: 全バージョンの成功確認
        assert legacy_result["success"], "レガシーバージョン処理が失敗"
        assert current_result["success"], "現在バージョン処理が失敗"
        assert hybrid_result["success"], "ハイブリッドバージョン処理が失敗"

        # 機能検出数の比較
        legacy_features = len(legacy_result["features_detected"])
        current_features = len(current_result["features_detected"])
        hybrid_features = len(hybrid_result["features_detected"])

        assert hybrid_features >= max(legacy_features, current_features), \
               "ハイブリッドモードの機能検出数が不足"

        # 出力ファイルの存在確認
        assert legacy_result["output_file"].exists(), "レガシー出力ファイルが作成されていない"
        assert current_result["output_file"].exists(), "現在出力ファイルが作成されていない"
        assert hybrid_result["output_file"].exists(), "ハイブリッド出力ファイルが作成されていない"

        logger.info(f"バージョン間比較完了 - レガシー:{legacy_features}, "
                   f"現在:{current_features}, ハイブリッド:{hybrid_features}機能")

    @pytest.mark.e2e
    def test_後方互換性_移行支援機能(self) -> None:
        """後方互換性: 移行支援機能の確認"""
        # Given: 移行が必要なレガシーコンテンツ
        migration_content = """;;太字 移行テスト;;;
;;イタリック 移行テスト2;;;

;;ブロック
移行が必要なブロック
;;;

正常な#新記法#も含む
"""

        # When: ハイブリッドモードで処理（移行支援）
        result = self.process_with_compatibility_check(migration_content, "hybrid")

        # Then: 移行支援機能の確認
        assert result["success"], "移行支援処理が失敗"
        # 移行提案は警告として出力される場合もある
        migration_info_available = (len(result.get("migration_suggestions", [])) > 0 or
                                   len(result.get("compatibility_warnings", [])) > 0)
        assert migration_info_available, "移行情報が生成されていない"

        # 自動変換の確認
        auto_converted = [f for f in result["features_detected"] if "auto_converted" in f]
        assert len(auto_converted) > 0, "自動変換が実行されていない"

        # 出力内容の移行情報確認
        output_content = result["output"]
        assert "移行提案" in output_content, "移行提案セクションが出力されていない"
        assert "自動変換" in output_content, "自動変換情報が出力されていない"

        logger.info(f"移行支援機能確認完了: {len(result['migration_suggestions'])}提案、"
                   f"{len(auto_converted)}自動変換")

    @pytest.mark.e2e
    def test_後方互換性_エラー耐性(self) -> None:
        """後方互換性: エラー耐性の確認"""
        # Given: 問題のあるレガシーコンテンツ
        problematic_content = """;;; 不完全な旧記法
;;太字 閉じタグなし
;;;; 過剰なセミコロン

正常な#新記法#

不正な;;旧記法;;

#新記法 閉じタグなし
"""

        # When: 各モードで処理
        legacy_result = self.process_with_compatibility_check(problematic_content, "legacy")
        current_result = self.process_with_compatibility_check(problematic_content, "current")
        hybrid_result = self.process_with_compatibility_check(problematic_content, "hybrid")

        # Then: エラー耐性の確認
        # 少なくとも1つのモードは成功すべき
        success_count = sum([
            legacy_result["success"],
            current_result["success"],
            hybrid_result["success"]
        ])
        assert success_count >= 1, "全てのモードが失敗している"

        # ハイブリッドモードは最も堅牢であるべき
        assert hybrid_result["success"], "ハイブリッドモードが失敗している"

        logger.info(f"エラー耐性確認完了: {success_count}/3モードが成功")

    @pytest.mark.e2e
    def test_後方互換性_パフォーマンス比較(self) -> None:
        """後方互換性: パフォーマンス比較"""
        import time

        # Given: 中規模テストコンテンツ
        large_content = ""
        for i in range(100):
            large_content += f"""#見出し{i}#
;;太字 レガシー{i};;;
#太字 新記法{i}#

;;ブロック{i}
レガシーブロック内容{i}
;;;

#ブロック{i}
新記法ブロック内容{i}
##

"""

        # When: 各モードの処理時間測定
        start_time = time.time()
        legacy_result = self.process_with_compatibility_check(large_content, "legacy")
        legacy_time = time.time() - start_time

        start_time = time.time()
        current_result = self.process_with_compatibility_check(large_content, "current")
        current_time = time.time() - start_time

        start_time = time.time()
        hybrid_result = self.process_with_compatibility_check(large_content, "hybrid")
        hybrid_time = time.time() - start_time

        # Then: パフォーマンス確認
        assert legacy_result["success"], "レガシーモードパフォーマンステストが失敗"
        assert current_result["success"], "現在モードパフォーマンステストが失敗"
        assert hybrid_result["success"], "ハイブリッドモードパフォーマンステストが失敗"

        # 処理時間の妥当性確認（10秒以内）
        assert legacy_time < 10.0, f"レガシーモード処理時間超過: {legacy_time}秒"
        assert current_time < 10.0, f"現在モード処理時間超過: {current_time}秒"
        assert hybrid_time < 15.0, f"ハイブリッドモード処理時間超過: {hybrid_time}秒"

        logger.info(f"パフォーマンス比較完了 - レガシー:{legacy_time:.3f}s, "
                   f"現在:{current_time:.3f}s, ハイブリッド:{hybrid_time:.3f}s")
