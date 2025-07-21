"""
ユーザー ガイダンス プロバイダー

初心者向けのわかりやすいガイダンス・ヘルプ機能
Issue #492 Phase 5A - japanese_messages.py分割
"""

from typing import Dict, List, Optional, Union

from .error_types import ErrorCategory, UserFriendlyError


class UserGuidanceProvider:
    """
    ユーザーガイダンス提供システム

    初心者ユーザー向けの分かりやすい説明とガイダンスを提供
    """

    # よくある質問と回答
    COMMON_QUESTIONS: Dict[str, Dict[str, Union[str, List[str]]]] = {
        "how_to_fix_encoding": {
            "question": "文字化けエラーを直すにはどうすればいいですか？",
            "answer": [
                "1. メモ帳でファイルを開いてください",
                "2. 「ファイル」→「名前を付けて保存」を選択してください",
                "3. 下部の「文字コード」を「UTF-8」に変更してください",
                "4. 「保存」ボタンを押してください",
                "5. Kumihan-Formatterで再度変換してください",
            ],
        },
        "what_is_kumihan_syntax": {
            "question": "Kumihan記法とは何ですか？",
            "answer": [
                "Kumihan記法は、美しい文書を簡単に作成するための記述方法です。",
                "例: ;;;太字;;;テキスト → 太字で表示されます",
                "例: ;;;見出し1;;;タイトル → 大きな見出しになります",
                "詳しくはSPEC.mdファイルをご覧ください。",
            ],
        },
        "where_is_output_file": {
            "question": "変換されたHTMLファイルはどこに保存されますか？",
            "answer": [
                "通常は「dist」フォルダに保存されます。",
                "元のファイルと同じ場所に「dist」フォルダが作成されます。",
                "フォルダが見つからない場合は、ファイル検索で「*.html」を検索してください。",
            ],
        },
    }

    # トラブルシューティングガイド
    TROUBLESHOOTING_STEPS: Dict[str, List[str]] = {
        "cannot_open_file": [
            "ファイルの存在を確認してください",
            "ファイル名に間違いがないか確認してください",
            "ファイルが移動されていないか確認してください",
            "ファイルが他のアプリで開かれていないか確認してください",
        ],
        "syntax_error_occurred": [
            "記法ガイド（SPEC.md）を確認してください",
            "マーカー（;;;）の数が正しいか確認してください",
            "キーワードのスペルが正しいか確認してください",
            "行の先頭にスペースが入っていないか確認してください",
        ],
        "conversion_failed": [
            "エラーメッセージの内容を確認してください",
            "より小さなファイルで試してください",
            "ファイルの内容に特殊文字がないか確認してください",
            "最新版のKumihan-Formatterを使用しているか確認してください",
        ],
    }

    @classmethod
    def get_guidance_for_error(
        cls, error: UserFriendlyError
    ) -> Optional[Dict[str, List[str]]]:
        """エラーに対する追加ガイダンスを取得"""
        guidance: Dict[str, List[str]] = {}

        # エラーカテゴリ別のガイダンス
        if error.category == ErrorCategory.FILE_SYSTEM:
            guidance["基本確認事項"] = cls.TROUBLESHOOTING_STEPS.get(
                "cannot_open_file", []
            )

        elif error.category == ErrorCategory.ENCODING:
            if "encoding" in cls.COMMON_QUESTIONS:
                qa = cls.COMMON_QUESTIONS["how_to_fix_encoding"]
                guidance[str(qa["question"])] = list(qa["answer"])

        elif error.category == ErrorCategory.SYNTAX:
            guidance["構文エラー対処法"] = cls.TROUBLESHOOTING_STEPS.get(
                "syntax_error_occurred", []
            )

            if "what_is_kumihan_syntax" in cls.COMMON_QUESTIONS:
                qa = cls.COMMON_QUESTIONS["what_is_kumihan_syntax"]
                guidance[str(qa["question"])] = list(qa["answer"])

        elif error.category == ErrorCategory.RENDERING:
            guidance["変換失敗時の対処法"] = cls.TROUBLESHOOTING_STEPS.get(
                "conversion_failed", []
            )

        return guidance if guidance else None

    @classmethod
    def get_beginner_tips(cls, operation: str) -> List[str]:
        """初心者向けのティップスを取得"""
        tips = {
            "convert": [
                "初回使用時は、サンプルファイルで動作を確認してみてください",
                "大きなファイルより小さなファイルで最初は試してください",
                "エラーが出た場合は、メッセージをよく読んで指示に従ってください",
            ],
            "syntax": [
                "記法は ;;;キーワード;;; の形で使用します",
                "マーカー（;;;）の数を間違えないよう注意してください",
                "行の先頭にスペースを入れないでください",
            ],
            "file_handling": [
                "ファイルはUTF-8形式で保存してください",
                "ファイル名に特殊文字は使用しないでください",
                "変換前にファイルのバックアップを取ることをお勧めします",
            ],
        }

        return tips.get(operation, [])
