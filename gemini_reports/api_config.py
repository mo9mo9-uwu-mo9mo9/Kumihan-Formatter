#!/usr/bin/env python3
"""Gemini API設定・認証管理

Gemini APIキーの安全な管理と設定を提供。
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


class GeminiAPIConfig:
    """Gemini API設定管理"""

    def __init__(self):
        self.config_file = Path(__file__).parent / "api_config.json"
        self.env_var_name = "GEMINI_API_KEY"

    def get_api_key(self) -> Optional[str]:
        """API キーを取得（優先順: 環境変数 > 設定ファイル）"""
        # 環境変数から取得
        api_key = os.getenv(self.env_var_name)
        if api_key:
            return api_key

        # 設定ファイルから取得
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get("gemini_api_key")
            except Exception:
                pass

        return None

    def set_api_key(self, api_key: str, method: str = "env") -> bool:
        """API キーを設定"""
        if method == "env":
            os.environ[self.env_var_name] = api_key
            print(f"✅ 環境変数 {self.env_var_name} に API キーを設定")
            return True
        elif method == "file":
            try:
                config = {}
                if self.config_file.exists():
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)

                config["gemini_api_key"] = api_key

                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                print(f"✅ 設定ファイル {self.config_file} に API キーを保存")
                return True
            except Exception as e:
                print(f"❌ 設定ファイル保存失敗: {e}")
                return False
        else:
            print(f"❌ 不正な設定方法: {method}")
            return False

    def is_configured(self) -> bool:
        """API キーが設定されているかチェック"""
        return self.get_api_key() is not None

    def get_config_status(self) -> Dict[str, Any]:
        """設定状況を取得"""
        return {
            "api_key_configured": self.is_configured(),
            "env_var_set": bool(os.getenv(self.env_var_name)),
            "config_file_exists": self.config_file.exists(),
            "config_methods": ["environment variable", "config file"]
        }


def setup_api_key_interactive() -> bool:
    """対話的APIキー設定"""
    config = GeminiAPIConfig()

    if config.is_configured():
        print("✅ Gemini API キーは既に設定されています")
        return True

    print("🔑 Gemini API キーの設定が必要です")
    print("\nAPI キーの取得方法:")
    print("1. https://aistudio.google.com/app/apikey にアクセス")
    print("2. Google アカウントでログイン")
    print("3. 'Create API Key' をクリック")
    print("4. API キーをコピー")

    api_key = input("\nGemini API キーを入力してください: ").strip()

    if not api_key:
        print("❌ API キーが入力されませんでした")
        return False

    print("\n設定方法を選択してください:")
    print("1. 環境変数（推奨）")
    print("2. 設定ファイル")

    choice = input("選択 (1 or 2): ").strip()

    if choice == "1":
        success = config.set_api_key(api_key, "env")
    elif choice == "2":
        success = config.set_api_key(api_key, "file")
    else:
        print("❌ 無効な選択です")
        return False

    if success:
        print("✅ API キーの設定が完了しました")
        return True
    else:
        print("❌ API キーの設定に失敗しました")
        return False


# CLI実行用
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini API設定管理")
    parser.add_argument("--setup", action="store_true", help="対話的API キー設定")
    parser.add_argument("--status", action="store_true", help="設定状況確認")
    parser.add_argument("--set-key", help="API キーを設定")
    parser.add_argument("--method", choices=["env", "file"], default="env", help="設定方法")

    args = parser.parse_args()

    config = GeminiAPIConfig()

    if args.setup:
        setup_api_key_interactive()
    elif args.status:
        status = config.get_config_status()
        print("📊 Gemini API設定状況")
        print("=" * 30)
        for key, value in status.items():
            print(f"{key}: {value}")
    elif args.set_key:
        success = config.set_api_key(args.set_key, args.method)
        if success:
            print("✅ API キー設定完了")
        else:
            print("❌ API キー設定失敗")
    else:
        parser.print_help()
