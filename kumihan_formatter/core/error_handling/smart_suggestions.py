"""
スマート提案システム
"""

import difflib
import platform
from pathlib import Path


class SmartSuggestions:
    """スマート提案システム"""

    # 有効なKumihan記法キーワード
    VALID_KEYWORDS = [
        "太字",
        "イタリック",
        "見出し1",
        "見出し2",
        "見出し3",
        "見出し4",
        "見出し5",
        "枠線",
        "ハイライト",
        "折りたたみ",
        "ネタバレ",
        "目次",
        "画像",
    ]

    # よくある間違いパターン
    COMMON_MISTAKES = {
        "太文字": "太字",
        "ボールド": "太字",
        "bold": "太字",
        "強調": "太字",
        "見だし": "見出し1",
        "ヘッダー": "見出し1",
        "タイトル": "見出し1",
        "斜体": "イタリック",
        "italic": "イタリック",
        "線": "枠線",
        "ボックス": "枠線",
        "囲み": "枠線",
        "マーカー": "ハイライト",
        "highlight": "ハイライト",
        "蛍光ペン": "ハイライト",
        "コラプス": "折りたたみ",
        "アコーディオン": "折りたたみ",
        "隠す": "折りたたみ",
        "スポイラー": "ネタバレ",
        "spoiler": "ネタバレ",
        "隠し": "ネタバレ",
        "もくじ": "目次",
        "インデックス": "目次",
        "index": "目次",
        "pic": "画像",
        "img": "画像",
        "写真": "画像",
        "イメージ": "画像",
    }

    @classmethod
    def suggest_keyword(cls, invalid_keyword: str) -> list[str]:
        """無効なキーワードに対する提案を生成"""
        suggestions = []

        # 直接的な間違いパターンをチェック（大文字小文字を区別しない）
        for mistake, correct in cls.COMMON_MISTAKES.items():
            if mistake.lower() == invalid_keyword.lower():
                suggestions.append(correct)
                break  # 見つかったら最初の一つだけ追加

        # 類似文字列検索（緩い条件で行う）
        close_matches = difflib.get_close_matches(
            invalid_keyword, cls.VALID_KEYWORDS, n=3, cutoff=0.4
        )
        suggestions.extend(close_matches)

        # 重複除去して返す
        return list(dict.fromkeys(suggestions))

    @classmethod
    def suggest_encoding(cls, error: UnicodeDecodeError) -> list[str]:
        """エンコーディングエラーに対するエンコーディング候補を提案"""
        suggestions = []

        # エラーの内容からエンコーディングを推定
        byte_sequence = error.object[error.start : error.end]

        # Shift-JIS/CP932の特徴的なバイト列を検出
        if len(byte_sequence) >= 2:
            first_byte = byte_sequence[0]
            # Shift-JISの文字範囲
            if 0x81 <= first_byte <= 0x9F or 0xE0 <= first_byte <= 0xFC:
                suggestions.extend(["shift_jis", "cp932"])

        # UTF-16のBOM検出
        if byte_sequence.startswith(b"\xff\xfe"):
            suggestions.append("utf-16-le")
        elif byte_sequence.startswith(b"\xfe\xff"):
            suggestions.append("utf-16-be")
        elif b"\xff\xfe" in byte_sequence or b"\xfe\xff" in byte_sequence:
            suggestions.extend(["utf-16", "utf-16-le", "utf-16-be"])

        # プラットフォーム固有のエンコーディング追加
        if platform.system() == "Windows":
            if "cp932" not in suggestions:
                suggestions.append("cp932")

        # 一般的なエンコーディングを最後に追加
        common_encodings = ["latin1", "iso-8859-1"]
        for enc in common_encodings:
            if enc not in suggestions:
                suggestions.append(enc)

        return suggestions

    @classmethod
    def suggest_file_encoding(cls, file_path: Path) -> list[str]:
        """ファイルエンコーディングエラーの提案"""
        suggestions = []

        if platform.system() == "Windows":
            suggestions.extend(
                [
                    "メモ帳で開いて「ファイル > 名前を付けて保存」で文字コードを「UTF-8」に変更",
                    "サクラエディタで文字コード変換機能を使用",
                    "VSCodeで「文字エンコーディングの変更」を選択",
                ]
            )
        elif platform.system() == "Darwin":  # macOS
            suggestions.extend(
                [
                    "テキストエディットで「フォーマット > プレーンテキストにする」後、UTF-8で保存",
                    "VSCodeで「文字エンコーディングの変更」を選択",
                    "CotEditorで文字エンコーディングを変更",
                ]
            )
        else:  # Linux
            suggestions.extend(
                [
                    "nkfコマンドでエンコーディング変換: nkf -w --overwrite ファイル名",
                    "VSCodeで「文字エンコーディングの変更」を選択",
                    "geditで「ファイル > 名前を付けて保存」で文字エンコーディングを指定",
                ]
            )

        return suggestions

    @classmethod
    def suggest_file_path(cls, missing_path: str) -> list[str]:
        """ファイルパスエラーの提案"""
        suggestions = []
        path_obj = Path(missing_path)

        # カレントディレクトリで類似ファイルを検索
        cwd = Path.cwd()
        for pattern in ["*", "**/*"]:
            try:
                for file_path in cwd.glob(pattern):
                    if file_path.is_file():
                        # ファイル名の類似度をチェック
                        if difflib.get_close_matches(
                            path_obj.name, [file_path.name], n=1, cutoff=0.5
                        ):
                            suggestions.append(file_path)
                        # ステム（拡張子なし）での類似度もチェック
                        elif difflib.get_close_matches(
                            path_obj.stem, [file_path.stem], n=1, cutoff=0.5
                        ):
                            suggestions.append(file_path)
            except (OSError, PermissionError):
                # アクセス権限エラーは無視
                continue

        # 最大5つまでに制限
        return suggestions[:5]

    @classmethod
    def suggest_permission_fix(cls, file_path: str) -> list[str]:
        """権限エラーの修正提案"""
        suggestions = []

        if platform.system() == "Windows":
            suggestions.extend(
                [
                    "管理者として実行してください",
                    "ファイルのプロパティで書き込み権限を確認してください",
                    "アンチウイルスソフトがファイルをブロックしていないか確認してください",
                ]
            )
        else:  # Unix-like systems
            suggestions.extend(
                [
                    f"chmod +r {file_path}  # 読み取り権限を追加",
                    f"chmod +w {file_path}  # 書き込み権限を追加",
                    "sudo を使用して実行してください",
                    "ファイルの所有者を確認してください",
                ]
            )

        return suggestions

    @classmethod
    def suggest_memory_optimization(cls, context: dict) -> list[str]:
        """メモリ最適化の提案"""
        suggestions = []
        file_size = context.get("file_size", 0)
        operation = context.get("operation", "")

        if file_size > 50 * 1024 * 1024:  # 50MB以上
            suggestions.extend(
                [
                    "大きなファイルはチャンクに分割して処理してください",
                    "ストリーミング処理を使用してメモリ使用量を削減してください",
                    "不要なデータを事前にフィルタリングしてください",
                ]
            )

        if operation == "parse":
            suggestions.extend(
                [
                    "パース処理を段階的に行ってください",
                    "中間結果をファイルに保存して メモリを解放してください",
                ]
            )

        return suggestions

    @classmethod
    def suggest_syntax_fix(cls, error_line: str) -> list[str]:
        """構文エラーの修正提案"""
        suggestions = []

        # 未閉装飾記法の検出と修正
        if ";;;" in error_line:
            # 開始タグはあるが終了タグが不完全なパターン
            if error_line.count(";;;") % 2 != 0:
                # 最後の部分を修正
                if error_line.endswith(";;"):
                    suggestions.append(error_line + ";")
                elif not error_line.endswith(";;;"):
                    suggestions.append(error_line + ";;;")

        # 無効なキーワードの検出と修正
        import re

        decoration_pattern = r";;;([^;]+);;;[^;]*;;;"
        matches = re.findall(decoration_pattern, error_line)

        for match in matches:
            keyword_suggestions = cls.suggest_keyword(match)
            for suggestion in keyword_suggestions[:2]:  # 上位2つまで
                fixed_line = error_line.replace(f";;{match};;;", f";;{suggestion};;;")
                suggestions.append(fixed_line)

        return suggestions[:3]  # 最大3つまで

    @classmethod
    def get_similar_keywords(cls, keyword: str, max_count: int = 3) -> list[str]:
        """類似キーワードの取得"""
        return difflib.get_close_matches(
            keyword, cls.VALID_KEYWORDS, n=max_count, cutoff=0.4
        )
