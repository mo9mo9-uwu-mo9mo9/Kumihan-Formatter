"""
日本語エラーメッセージ強化 - Issue #401対応

ユーザーフレンドリーな日本語エラーメッセージと解決方法を提供。
"""

from pathlib import Path
from typing import Dict, List, Optional

from .error_types import ErrorCategory, ErrorLevel, ErrorSolution, UserFriendlyError


class JapaneseMessageCatalog:
    """
    日本語エラーメッセージカタログ

    設計ドキュメント:
    - Issue #401: エラーハンドリングの強化と統合
    - ユーザーフレンドリーなメッセージ提供
    - 初心者にも分かりやすい説明

    機能:
    - エラータイプ別の詳細メッセージ
    - 段階的な解決手順
    - 分かりやすい説明文
    """

    # ファイルシステムエラーメッセージ
    FILE_SYSTEM_MESSAGES = {
        "file_not_found": {
            "title": "📁 ファイルが見つかりません",
            "description": "指定されたファイルが存在しないか、パスが間違っています。",
            "quick_fix": "ファイル名とパスを確認してください",
            "detailed_steps": [
                "ファイル名のスペルミスがないか確認してください",
                "ファイルが正しいフォルダに保存されているか確認してください",
                "ファイルの拡張子（.txt など）が正しいか確認してください",
                "ファイルが他のアプリケーションで開かれていないか確認してください",
                "フルパス（絶対パス）で指定してみてください",
            ],
            "alternatives": [
                "ファイルをKumihan-Formatterのフォルダにコピーして再実行",
                "ドラッグ＆ドロップでファイルを指定",
                "ファイル選択ダイアログを使用",
            ],
        },
        "permission_denied": {
            "title": "🔒 ファイルへのアクセスが拒否されました",
            "description": "ファイルやフォルダに対する読み取り・書き込み権限がありません。",
            "quick_fix": "ファイルが他のプログラムで開かれていないか確認してください",
            "detailed_steps": [
                "ファイルを開いているWord、Excel、テキストエディタなどをすべて閉じてください",
                "ファイルの「プロパティ」から「読み取り専用」のチェックを外してください",
                "管理者として実行してみてください",
                "ファイルを別の場所（デスクトップなど）にコピーして実行してください",
            ],
            "alternatives": [
                "ファイルをデスクトップにコピーして変換",
                "新しいファイル名で保存して再実行",
                "管理者権限でKumihan-Formatterを起動",
            ],
        },
        "file_too_large": {
            "title": "📊 ファイルサイズが制限を超えています",
            "description": "処理可能なファイルサイズの上限を超えています。",
            "quick_fix": "ファイルを分割するか、内容を削減してください",
            "detailed_steps": [
                "ファイルを複数の小さなファイルに分割してください",
                "不要な内容や空行を削除してください",
                "画像参照がある場合は、画像ファイルのサイズを縮小してください",
                "分割したファイルを個別に変換してください",
            ],
            "alternatives": [
                "章ごとに別ファイルに分割",
                "重要な部分のみを抽出して変換",
                "設定でファイルサイズ制限を調整",
            ],
        },
    }

    # エンコーディングエラーメッセージ
    ENCODING_MESSAGES = {
        "decode_error": {
            "title": "📝 文字化けが検出されました",
            "description": "ファイルの文字エンコーディングが正しく読み取れません。",
            "quick_fix": "ファイルをUTF-8形式で保存し直してください",
            "detailed_steps": [
                "テキストエディタ（メモ帳、VSCodeなど）でファイルを開いてください",
                "「名前を付けて保存」または「文字エンコーディングの変更」を選択してください",
                "文字エンコーディングを「UTF-8」に変更してください",
                "ファイルを保存して、再度変換を実行してください",
            ],
            "alternatives": [
                "別のテキストエディタで開いて保存",
                "文字エンコーディング変換ツールを使用",
                "元のファイル作成者に正しい形式での保存を依頼",
            ],
        },
        "encoding_detection_failed": {
            "title": "🔍 文字エンコーディングの自動検出に失敗しました",
            "description": "ファイルの文字エンコーディングを特定できませんでした。",
            "quick_fix": "UTF-8形式で保存されたファイルを使用してください",
            "detailed_steps": [
                "元のファイルがどの文字エンコーディングで作成されたか確認してください",
                "可能であれば、ファイル作成者に確認してください",
                "テキストエディタの「文字エンコーディング指定」機能を使用してください",
                "UTF-8形式で新しくファイルを作成し直してください",
            ],
        },
    }

    # 構文エラーメッセージ
    SYNTAX_MESSAGES = {
        "invalid_marker": {
            "title": "✏️ 記法エラーが検出されました",
            "description": "Kumihan記法の書き方に間違いがあります。",
            "quick_fix": "記法の基本ルールを確認してください",
            "detailed_steps": [
                "マーカーは ;;; で開始し、;;; で終了する必要があります",
                "マーカーは行の先頭に記述してください",
                "有効なキーワード（太字、見出し1など）を使用してください",
                "複合記法の場合は + で連結してください",
            ],
            "alternatives": [
                "記法ガイド（SPEC.md）を参照",
                "サンプルファイルを確認",
                "よく使われる記法例を参照",
            ],
        },
        "unknown_keyword": {
            "title": "❓ 不明なキーワードが使用されています",
            "description": "サポートされていないキーワードが記法内で使用されています。",
            "quick_fix": "有効なキーワードを使用してください",
            "detailed_steps": [
                "使用可能なキーワード一覧を確認してください",
                "スペルミスがないかチェックしてください",
                "全角・半角文字の違いを確認してください",
                "最新版のKumihan-Formatterを使用しているか確認してください",
            ],
        },
    }

    # レンダリングエラーメッセージ
    RENDERING_MESSAGES = {
        "template_not_found": {
            "title": "🎨 テンプレートが見つかりません",
            "description": "指定されたHTMLテンプレートファイルが見つかりません。",
            "quick_fix": "テンプレート名を確認するか、デフォルトテンプレートを使用してください",
            "detailed_steps": [
                "テンプレート名のスペルミスがないか確認してください",
                "利用可能なテンプレート一覧を確認してください",
                "テンプレートファイルが正しい場所にあるか確認してください",
                "設定ファイルでテンプレートパスが正しく指定されているか確認してください",
            ],
            "alternatives": [
                "デフォルトテンプレートで変換を実行",
                "別のテンプレートを試す",
                "カスタムテンプレートを作成",
            ],
        },
        "html_generation_failed": {
            "title": "🌐 HTML生成に失敗しました",
            "description": "変換処理中にHTMLの生成でエラーが発生しました。",
            "quick_fix": "入力ファイルの内容を確認してください",
            "detailed_steps": [
                "記法の使用方法が正しいか確認してください",
                "特殊文字（<, >, &など）が適切にエスケープされているか確認してください",
                "ファイル内に破損したデータがないか確認してください",
                "より小さなファイルで試してみてください",
            ],
        },
    }

    # システムエラーメッセージ
    SYSTEM_MESSAGES = {
        "memory_error": {
            "title": "💾 メモリ不足エラーが発生しました",
            "description": "処理に必要なメモリが不足しています。",
            "quick_fix": "他のアプリケーションを閉じて、メモリを解放してください",
            "detailed_steps": [
                "不要なアプリケーションやブラウザタブを閉じてください",
                "ファイルサイズを小さくしてください",
                "コンピュータを再起動してメモリをクリアしてください",
                "より小さな単位でファイルを分割して処理してください",
            ],
            "alternatives": [
                "バッチ処理でファイルを分割",
                "システムの再起動",
                "メモリ使用量の多いアプリケーションを終了",
            ],
        },
        "unexpected_error": {
            "title": "🚨 予期しないエラーが発生しました",
            "description": "システム内部でエラーが発生しました。",
            "quick_fix": "操作を再試行するか、開発チームに報告してください",
            "detailed_steps": [
                "エラーメッセージの詳細をコピーしてください",
                "使用していたファイルと操作手順を記録してください",
                "GitHubのIssueページで新しいIssueを作成してください",
                "エラー詳細と再現手順を記載して投稿してください",
            ],
            "alternatives": [
                "Kumihan-Formatterの再起動",
                "コンピュータの再起動",
                "最新版への更新",
            ],
        },
    }

    @classmethod
    def get_file_system_error(
        cls, error_type: str, file_path: str = None, **kwargs
    ) -> UserFriendlyError:
        """ファイルシステムエラーのメッセージを生成"""
        if error_type not in cls.FILE_SYSTEM_MESSAGES:
            error_type = "file_not_found"  # デフォルト

        template = cls.FILE_SYSTEM_MESSAGES[error_type]

        # ファイルパスを含むメッセージに調整
        title = template["title"]
        if file_path:
            title += f"（ファイル: {Path(file_path).name}）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=template["quick_fix"],
                detailed_steps=template["detailed_steps"],
                alternative_approaches=template.get("alternatives", []),
            ),
            context={"file_path": file_path, **kwargs},
        )

    @classmethod
    def get_encoding_error(
        cls, error_type: str, file_path: str = None, **kwargs
    ) -> UserFriendlyError:
        """エンコーディングエラーのメッセージを生成"""
        if error_type not in cls.ENCODING_MESSAGES:
            error_type = "decode_error"  # デフォルト

        template = cls.ENCODING_MESSAGES[error_type]

        title = template["title"]
        if file_path:
            title += f"（ファイル: {Path(file_path).name}）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.ENCODING,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=template["quick_fix"],
                detailed_steps=template["detailed_steps"],
                alternative_approaches=template.get("alternatives", []),
            ),
            context={"file_path": file_path, **kwargs},
        )

    @classmethod
    def get_syntax_error(
        cls, error_type: str, line_number: int = None, **kwargs
    ) -> UserFriendlyError:
        """構文エラーのメッセージを生成"""
        if error_type not in cls.SYNTAX_MESSAGES:
            error_type = "invalid_marker"  # デフォルト

        template = cls.SYNTAX_MESSAGES[error_type]

        title = template["title"]
        if line_number:
            title += f"（{line_number}行目）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.SYNTAX,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=template["quick_fix"],
                detailed_steps=template["detailed_steps"],
                alternative_approaches=template.get("alternatives", []),
            ),
            context={"line_number": line_number, **kwargs},
        )

    @classmethod
    def get_rendering_error(
        cls, error_type: str, template_name: str = None, **kwargs
    ) -> UserFriendlyError:
        """レンダリングエラーのメッセージを生成"""
        if error_type not in cls.RENDERING_MESSAGES:
            error_type = "html_generation_failed"  # デフォルト

        template = cls.RENDERING_MESSAGES[error_type]

        title = template["title"]
        if template_name:
            title += f"（テンプレート: {template_name}）"

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.RENDERING,
            user_message=title,
            solution=ErrorSolution(
                quick_fix=template["quick_fix"],
                detailed_steps=template["detailed_steps"],
                alternative_approaches=template.get("alternatives", []),
            ),
            context={"template_name": template_name, **kwargs},
        )

    @classmethod
    def get_system_error(cls, error_type: str, **kwargs) -> UserFriendlyError:
        """システムエラーのメッセージを生成"""
        if error_type not in cls.SYSTEM_MESSAGES:
            error_type = "unexpected_error"  # デフォルト

        template = cls.SYSTEM_MESSAGES[error_type]

        level = (
            ErrorLevel.CRITICAL
            if error_type == "unexpected_error"
            else ErrorLevel.ERROR
        )

        return UserFriendlyError(
            error_code=f"E{hash(error_type) % 1000:03d}",
            level=level,
            category=ErrorCategory.SYSTEM,
            user_message=template["title"],
            solution=ErrorSolution(
                quick_fix=template["quick_fix"],
                detailed_steps=template["detailed_steps"],
                alternative_approaches=template.get("alternatives", []),
            ),
            context=kwargs,
        )


class UserGuidanceProvider:
    """
    ユーザーガイダンス提供システム

    初心者ユーザー向けの分かりやすい説明とガイダンスを提供
    """

    # よくある質問と回答
    COMMON_QUESTIONS = {
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
    TROUBLESHOOTING_STEPS = {
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
        guidance = {}

        # エラーカテゴリ別のガイダンス
        if error.category == ErrorCategory.FILE_SYSTEM:
            guidance["基本確認事項"] = cls.TROUBLESHOOTING_STEPS.get(
                "cannot_open_file", []
            )

        elif error.category == ErrorCategory.ENCODING:
            if "encoding" in cls.COMMON_QUESTIONS:
                qa = cls.COMMON_QUESTIONS["how_to_fix_encoding"]
                guidance[qa["question"]] = qa["answer"]

        elif error.category == ErrorCategory.SYNTAX:
            guidance["構文エラー対処法"] = cls.TROUBLESHOOTING_STEPS.get(
                "syntax_error_occurred", []
            )

            if "what_is_kumihan_syntax" in cls.COMMON_QUESTIONS:
                qa = cls.COMMON_QUESTIONS["what_is_kumihan_syntax"]
                guidance[qa["question"]] = qa["answer"]

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


# モジュールレベル関数
def create_user_friendly_error(
    category: str, error_type: str, **context
) -> UserFriendlyError:
    """ユーザーフレンドリーエラーを作成する便利関数"""

    if category == "file_system":
        return JapaneseMessageCatalog.get_file_system_error(error_type, **context)
    elif category == "encoding":
        return JapaneseMessageCatalog.get_encoding_error(error_type, **context)
    elif category == "syntax":
        return JapaneseMessageCatalog.get_syntax_error(error_type, **context)
    elif category == "rendering":
        return JapaneseMessageCatalog.get_rendering_error(error_type, **context)
    elif category == "system":
        return JapaneseMessageCatalog.get_system_error(error_type, **context)
    else:
        return JapaneseMessageCatalog.get_system_error("unexpected_error", **context)
