"""
スマート提案システム
"""

import difflib
import platform
from pathlib import Path
from typing import List


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
    def suggest_keyword(cls, invalid_keyword: str) -> List[str]:
        """無効なキーワードに対する提案を生成"""
        suggestions = []

        # 直接的な間違いパターンをチェック
        if invalid_keyword in cls.COMMON_MISTAKES:
            suggestions.append(cls.COMMON_MISTAKES[invalid_keyword])

        # 類似文字列検索
        close_matches = difflib.get_close_matches(invalid_keyword, cls.VALID_KEYWORDS, n=3, cutoff=0.6)
        suggestions.extend(close_matches)

        # 重複除去して返す
        return list(dict.fromkeys(suggestions))

    @classmethod
    def suggest_file_encoding(cls, file_path: Path) -> List[str]:
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
