#!/usr/bin/env python3
"""
シンプルCLI - 緊急復旧版
基本的なファイル変換機能のみ提供
"""

import sys
import argparse
import logging
from pathlib import Path
from .unified_api import KumihanFormatter


def setup_logging(verbose: bool = False) -> None:
    """ログ設定"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(levelname)s: %(message)s", stream=sys.stderr
    )


def convert_command(args) -> int:
    """ファイル変換コマンド"""
    try:
        formatter = KumihanFormatter()

        print(f"変換開始: {args.input} -> {args.output or '(自動生成)'}")

        result = formatter.convert(input_file=args.input, output_file=args.output)

        if result["status"] == "success":
            print(f"✅ 変換完了: {result['output_file']}")
            print(f"   要素数: {result.get('elements_count', 0)}")
            return 0
        else:
            print(f"❌ 変換失敗: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1


def parse_command(args) -> int:
    """テキスト解析コマンド"""
    try:
        formatter = KumihanFormatter()

        if args.file:
            result = formatter.parse_file(args.file)
            print(f"解析対象: {args.file}")
        else:
            text = sys.stdin.read()
            result = formatter.parse_text(text)
            print("解析対象: 標準入力")

        if result["status"] == "success":
            print(f"✅ 解析完了")
            print(f"   要素数: {result.get('total_elements', 0)}")
            if args.verbose:
                import json

                print("解析結果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        else:
            print(f"❌ 解析失敗: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1


def validate_command(args) -> int:
    """構文検証コマンド"""
    try:
        formatter = KumihanFormatter()

        if args.file:
            content = Path(args.file).read_text(encoding="utf-8")
            print(f"検証対象: {args.file}")
        else:
            content = sys.stdin.read()
            print("検証対象: 標準入力")

        result = formatter.validate_syntax(content)

        if result["status"] == "valid":
            print("✅ 構文は正常です")
            return 0
        elif result["status"] == "invalid":
            print("❌ 構文エラーが見つかりました:")
            for error in result.get("errors", []):
                print(f"   • {error}")
            return 1
        else:
            print(f"❌ 検証失敗: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1


def info_command(args) -> int:
    """システム情報コマンド"""
    try:
        formatter = KumihanFormatter()
        info = formatter.get_system_info()

        print("=== Kumihan-Formatter システム情報 ===")
        print(f"バージョン: {info['version']}")
        print(f"アーキテクチャ: {info['architecture']}")
        print(f"ステータス: {info.get('status', 'unknown')}")
        print("コンポーネント:")
        for name, component in info.get("components", {}).items():
            print(f"  • {name}: {component}")

        return 0

    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1


def main() -> int:
    """メイン関数"""
    parser = argparse.ArgumentParser(
        prog="kumihan-formatter",
        description="Kumihan-Formatter: テキストファイルをHTMLに変換",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")

    # convert コマンド
    convert_parser = subparsers.add_parser("convert", help="ファイル変換")
    convert_parser.add_argument("input", help="入力ファイル")
    convert_parser.add_argument(
        "-o", "--output", help="出力ファイル (省略時は自動生成)"
    )
    convert_parser.set_defaults(func=convert_command)

    # parse コマンド
    parse_parser = subparsers.add_parser("parse", help="テキスト解析")
    parse_parser.add_argument("-f", "--file", help="解析ファイル (省略時は標準入力)")
    parse_parser.set_defaults(func=parse_command)

    # validate コマンド
    validate_parser = subparsers.add_parser("validate", help="構文検証")
    validate_parser.add_argument("-f", "--file", help="検証ファイル (省略時は標準入力)")
    validate_parser.set_defaults(func=validate_command)

    # info コマンド
    info_parser = subparsers.add_parser("info", help="システム情報")
    info_parser.set_defaults(func=info_command)

    args = parser.parse_args()

    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
