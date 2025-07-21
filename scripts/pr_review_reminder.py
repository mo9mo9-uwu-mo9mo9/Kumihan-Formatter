#!/usr/bin/env python3
"""
PR作成後のレビュー依頼リマインダー
PR作成時に自動で実行されるスクリプト
"""
# os removed as unused
import sys
from datetime import datetime


def show_review_reminder() -> None:
    """PRレビュー依頼のリマインダーを表示"""
    print("=" * 60)
    print("🔔 PR作成後の必須手順リマインダー")
    print("=" * 60)
    print()
    print("✅ PR作成完了！次に以下を実行してください:")
    print()
    print("1. 📋 PRページに移動")
    print("2. 💬 コメント欄に以下を投稿:")
    print()
    print("   @claude 以下のコミットをレビューしてください：")
    print("   - [コミットハッシュ] コミット概要")
    print("   - TDD原則に従った実装であるかチェック")
    print("   - コーディング規約への準拠確認")
    print()
    print("3. ⏳ レビュー完了まで待機")
    print("4. 🔄 指摘事項があれば修正・追加コミット")
    print("5. ✅ 承認後、手動マージを実行")
    print()
    print("=" * 60)
    print("⚠️  注意: @claude-ai ではなく @claude を使用")
    print("⚠️  注意: オートマージは使用禁止")
    print("=" * 60)
    print()


def main() -> None:
    """メイン処理"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quiet":
        return

    show_review_reminder()

    # ログファイルに記録
    log_file = ".github/pr_review_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - PR作成リマインダー表示\n")
    except Exception:
        pass  # ログ書き込みエラーは無視


if __name__ == "__main__":
    main()
