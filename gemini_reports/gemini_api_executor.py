#!/usr/bin/env python3
"""Gemini API統合実行システム

実際のGemini APIを使用してClaude作成の作業指示書に基づく実装を実行。
真のClaude-Geminiオーケストレーション体制を実現。

Created: 2025-08-15 (真のAPI統合版)
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")


class GeminiAPIExecutor:
    """実際のGemini APIを使用した実装実行システム"""

    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None):
        """初期化

        Args:
            api_key: Gemini API キー（環境変数 GEMINI_API_KEY からも取得可能）
            config_path: 設定ファイルパス（デフォルト: gemini_reports/config.json）
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai library is required")

        # 設定ファイル読み込み
        self.config = self._load_config(config_path)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter")

        # Gemini API設定
        genai.configure(api_key=self.api_key)
        model_name = self.config["gemini_api"]["model_name"]
        self.model = genai.GenerativeModel(model_name)

        # 設定から読み込み
        self.generation_config = self.config["gemini_api"]["generation_config"]

        # リトライ設定
        retry_config = self.config["gemini_api"]["retry_config"]
        self.max_retries = retry_config["max_retries"]
        self.retry_delays = retry_config["retry_delays"]
        self.quota_retry_delay = retry_config["quota_retry_delay"]

        # ログ設定
        logging_config = self.config["logging"]
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, logging_config["level"]))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(logging_config["format"])
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # 統計・エラー詳細ログ
        self.execution_stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
            "quota_errors": 0,
            "network_errors": 0,
            "parsing_errors": 0,
            "timeout_errors": 0,
            "error_details": [],  # 詳細エラーログ
            "total_tokens_used": 0
        }

        # 設定保存
        self.max_error_entries = logging_config["max_error_entries"]

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """設定ファイルを読み込み

        Args:
            config_path: 設定ファイルパス

        Returns:
            設定辞書
        """
        if config_path is None:
            # デフォルト設定ファイルパス
            current_dir = Path(__file__).parent
            config_path = str(current_dir / "config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # logger未初期化のため直接print
            print(f"⚠️ 設定ファイルが見つかりません: {config_path}. デフォルト設定を使用します。")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"❌ 設定ファイルの解析エラー: {e}. デフォルト設定を使用します。")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "gemini_api": {
                "model_name": "gemini-2.0-flash-exp",
                "generation_config": {
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 8192
                },
                "retry_config": {
                    "max_retries": 3,
                    "retry_delays": [1, 5, 15],
                    "quota_retry_delay": 60,
                    "timeout_seconds": 120
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "max_error_entries": 100
            },
            "file_output": {
                "temp_directory": "tmp",
                "encoding": "utf-8",
                "create_backup": True
            },
            "quality_checks": {
                "enable_syntax_check": True,
                "enable_mypy_check": False,
                "enable_flake8_check": False
            }
        }

    def _log_error_details(self, error_type: str, error_message: str, task_id: str, context: Optional[Dict[str, Any]] = None) -> None:
        """詳細エラーログを記録

        Args:
            error_type: エラータイプ
            error_message: エラーメッセージ
            task_id: タスクID
            context: 追加コンテキスト情報
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "error_type": error_type,
            "error_message": str(error_message),
            "context": context or {}
        }

        self.execution_stats["error_details"].append(error_entry)

        # 設定された最大件数のみ保持
        if len(self.execution_stats["error_details"]) > self.max_error_entries:
            self.execution_stats["error_details"] = self.execution_stats["error_details"][-self.max_error_entries:]

        self.logger.error(f"[{error_type}] Task {task_id}: {error_message}")
        if context:
            self.logger.debug(f"Error context: {context}")

    async def execute_task(self, work_instruction: str, task_id: str) -> Dict[str, Any]:
        """Gemini APIを使用してタスクを実行

        Args:
            work_instruction: Claude作成の詳細作業指示書
            task_id: タスクID

        Returns:
            実行結果辞書
        """
        print(f"🤖 Gemini API実行開始: {task_id}")

        start_time = datetime.now()

        result = {
            "task_id": task_id,
            "status": "failed",
            "implemented_files": [],
            "modified_lines": 0,
            "gemini_response": "",
            "extracted_code": {},
            "execution_time": 0,
            "token_usage": {"input_tokens": 0, "output_tokens": 0},
            "errors": [],
            "warnings": []
        }

        try:
            # Gemini APIに送信するプロンプト作成
            prompt = self._create_gemini_prompt(work_instruction)

            # API実行
            print("📡 Gemini APIに送信中...")
            response = await self._call_gemini_api(prompt)

            result["gemini_response"] = response
            self.execution_stats["total_requests"] += 1

            # レスポンス解析
            extracted_code = self._extract_code_blocks(response)
            result["extracted_code"] = extracted_code

            if extracted_code:
                # ファイル作成・修正実行
                implemented_files = await self._implement_code(extracted_code, task_id)
                result["implemented_files"] = implemented_files
                result["modified_lines"] = self._count_total_lines(implemented_files)
                result["status"] = "completed"

                print(f"✅ Gemini実装完了: {len(implemented_files)}ファイル")
                self.execution_stats["successful_requests"] += 1
            else:
                error_msg = "Geminiレスポンスからコードを抽出できませんでした"
                result["errors"].append(error_msg)
                self.execution_stats["failed_requests"] += 1
                self.execution_stats["parsing_errors"] += 1
                self._log_error_details("PARSING_ERROR", error_msg, task_id, {
                    "response_length": len(response),
                    "response_preview": response[:500] if response else "No response"
                })

        except asyncio.TimeoutError as e:
            error_msg = f"Gemini API タイムアウト: {str(e)}"
            result["errors"].append(error_msg)
            self.execution_stats["failed_requests"] += 1
            self.execution_stats["timeout_errors"] += 1
            self._log_error_details("TIMEOUT_ERROR", error_msg, task_id, {
                "timeout_duration": "120s",
                "instruction_length": len(work_instruction)
            })
            print(f"⏰ {error_msg}")

        except Exception as e:
            error_msg = f"Gemini API実行エラー: {str(e)}"
            result["errors"].append(error_msg)
            self.execution_stats["failed_requests"] += 1

            # エラータイプ別の分類
            if "quota" in str(e).lower() or "429" in str(e):
                self.execution_stats["quota_errors"] += 1
                error_type = "QUOTA_ERROR"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                self.execution_stats["network_errors"] += 1
                error_type = "NETWORK_ERROR"
            else:
                error_type = "UNKNOWN_ERROR"

            self._log_error_details(error_type, error_msg, task_id, {
                "exception_type": type(e).__name__,
                "instruction_length": len(work_instruction)
            })
            print(f"❌ Gemini API実行失敗: {e}")

        # 実行時間計算
        end_time = datetime.now()
        result["execution_time"] = int((end_time - start_time).total_seconds())

        return result

    def _create_gemini_prompt(self, work_instruction: str) -> str:
        """Gemini APIに送信するプロンプトを作成"""
        prompt = f"""あなたは優秀なPythonデベロッパーです。以下の作業指示書に従って実装を行ってください。

# 作業指示書
{work_instruction}

# 実装要件
1. **完全なファイル実装**: ファイルごとに完全なコードを提供してください
2. **品質基準遵守**: MyPy、Flake8、Blackの基準に準拠してください
3. **コードブロック形式**: 以下の形式でコードを記述してください

```python
# ファイル: path/to/file.py
コード内容
```

4. **エラーハンドリング**: 適切な例外処理を含めてください
5. **型注釈**: 全ての関数・メソッドに型注釈を追加してください
6. **ドキュメント**: docstringを適切に記述してください

# 禁止事項
- 不完全なコード片の提供
- 品質基準に準拠しないコード
- 指示書にない機能の追加
- 既存システムへの破壊的変更

指示書の要件を100%満たす実装を提供してください。"""

        return prompt

    async def _call_gemini_api(self, prompt: str) -> str:
        """Gemini APIを呼び出し（リトライ機能付き）"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Gemini API呼び出し試行 {attempt + 1}/{self.max_retries + 1}")

                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=self.generation_config
                )

                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts and len(candidate.content.parts) > 0:
                        self.logger.info("Gemini API呼び出し成功")
                        return str(candidate.content.parts[0].text)
                    else:
                        raise Exception(f"Gemini APIレスポンス構造エラー: content={candidate.content}")
                else:
                    raise Exception(f"Gemini APIレスポンスエラー: candidates={response.candidates}")

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # エラータイプ別統計更新
                if "429" in error_str or "quota" in error_str:
                    self.execution_stats["quota_errors"] += 1
                    self.logger.warning(f"クォータ制限エラー (試行 {attempt + 1}): {e}")

                    if attempt < self.max_retries:
                        wait_time = self.quota_retry_delay
                        self.logger.info(f"クォータ制限のため {wait_time}秒待機")
                        await asyncio.sleep(wait_time)
                        continue

                elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
                    self.execution_stats["network_errors"] += 1
                    self.logger.warning(f"ネットワークエラー (試行 {attempt + 1}): {e}")

                else:
                    self.logger.error(f"API呼び出しエラー (試行 {attempt + 1}): {e}")

                # リトライ実行
                if attempt < self.max_retries:
                    self.execution_stats["retry_attempts"] += 1
                    wait_time = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    self.logger.info(f"リトライまで {wait_time}秒待機")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"最大リトライ回数に達しました。最後のエラー: {e}")

        raise Exception(f"Gemini API呼び出し失敗 (最大{self.max_retries + 1}回試行): {str(last_error)}")

    def _extract_code_blocks(self, response: str) -> Dict[str, str]:
        """Geminiレスポンスからコードブロックを抽出（フェイルセーフ付き）"""
        extracted_code = {}

        try:
            self.logger.info("コードブロック抽出開始")

            # ファイルパス付きコードブロックのパターン
            pattern = r'```python\s*\n#\s*ファイル:\s*([^\n]+)\n(.*?)```'
            matches = re.findall(pattern, response, re.DOTALL)

            for file_path, code in matches:
                file_path = file_path.strip()
                code = code.strip()

                # コード検証
                if len(code) < 10:
                    self.logger.warning(f"コードが短すぎます: {file_path} ({len(code)}文字)")
                    continue

                extracted_code[file_path] = code
                self.logger.info(f"📄 コード抽出: {file_path} ({len(code)}文字)")

            # 通常のコードブロックも抽出（ファイルパス推定）
            if not extracted_code:
                self.logger.info("ファイルパス付きコードが見つからないため、汎用抽出を実行")
                pattern = r'```python\n(.*?)```'
                matches = re.findall(pattern, response, re.DOTALL)

                for i, code in enumerate(matches):
                    code = code.strip()
                    if len(code) < 10:  # 最小コード長チェック
                        continue

                    file_path = f"tmp/gemini_generated_{i+1}.py"
                    extracted_code[file_path] = code
                    self.logger.info(f"📄 汎用コード抽出: {file_path}")

            # 抽出結果の最終検証
            if not extracted_code:
                self.logger.error("レスポンスからコードブロックを抽出できませんでした")
                self.logger.debug(f"レスポンス内容 (先頭500文字): {response[:500]}")

                # フェイルセーフ: マークダウンなしの可能性をチェック
                if "def " in response or "class " in response or "import " in response:
                    self.logger.info("マークダウンなしのコードを検出、そのまま使用")
                    extracted_code["tmp/fallback_code.py"] = response.strip()

        except Exception as e:
            self.logger.error(f"コードブロック抽出中にエラー: {e}")
            # 完全フェイルセーフ
            if response.strip():
                extracted_code["tmp/emergency_fallback.py"] = response.strip()
                self.logger.warning("緊急フェイルセーフ: レスポンス全体をコードとして保存")

        self.logger.info(f"コードブロック抽出完了: {len(extracted_code)}ファイル")
        return extracted_code

    async def _implement_code(self, extracted_code: Dict[str, str], task_id: str) -> List[str]:
        """抽出したコードを実際のファイルに実装"""
        implemented_files = []

        for file_path, code in extracted_code.items():
            try:
                # ファイルパス正規化
                if not file_path.startswith('/'):
                    if file_path.startswith('kumihan_formatter/'):
                        full_path = file_path
                    elif file_path.startswith('tmp/'):
                        full_path = file_path
                    else:
                        full_path = f"tmp/{file_path}"
                else:
                    full_path = file_path.lstrip('/')

                # ディレクトリ作成
                Path(full_path).parent.mkdir(parents=True, exist_ok=True)

                # ファイル作成
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(code)

                implemented_files.append(full_path)
                print(f"📁 ファイル作成: {full_path}")

                # 基本的な構文チェック
                if await self._basic_syntax_check(full_path):
                    print(f"✅ 構文チェック通過: {full_path}")
                else:
                    print(f"⚠️ 構文チェック失敗: {full_path}")

            except Exception as e:
                print(f"❌ ファイル作成失敗 {file_path}: {e}")

        return implemented_files

    async def _basic_syntax_check(self, file_path: str) -> bool:
        """基本的な構文チェック"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def _count_total_lines(self, files: List[str]) -> int:
        """実装ファイルの総行数をカウント"""
        total_lines = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except Exception:
                pass
        return total_lines

    def get_execution_stats(self) -> Dict[str, Any]:
        """実行統計を取得"""
        success_rate = 0
        retry_rate = 0

        if self.execution_stats["total_requests"] > 0:
            success_rate = (
                self.execution_stats["successful_requests"] /
                self.execution_stats["total_requests"]
            )
            retry_rate = (
                self.execution_stats["retry_attempts"] /
                self.execution_stats["total_requests"]
            )

        return {
            **self.execution_stats,
            "success_rate": success_rate,
            "retry_rate": retry_rate,
            "avg_tokens_per_request": (
                self.execution_stats["total_tokens_used"] /
                max(1, self.execution_stats["total_requests"])
            ),
            "error_breakdown": {
                "quota_errors": self.execution_stats["quota_errors"],
                "network_errors": self.execution_stats["network_errors"],
                "parsing_errors": self.execution_stats["parsing_errors"],
                "timeout_errors": self.execution_stats["timeout_errors"],
                "other_errors": (
                    self.execution_stats["failed_requests"] -
                    self.execution_stats["quota_errors"] -
                    self.execution_stats["network_errors"] -
                    self.execution_stats["parsing_errors"] -
                    self.execution_stats["timeout_errors"]
                )
            },
            "recent_errors": self.execution_stats["error_details"][-10:],  # 最新10件のエラー
            "error_summary": self._get_error_summary()
        }

    def _get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを生成"""
        error_types: Dict[str, int] = {}
        recent_errors = self.execution_stats["error_details"][-50:]  # 最新50件を分析

        for error in recent_errors:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "most_common_errors": sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_logged_errors": len(self.execution_stats["error_details"]),
            "error_rate_trend": self._calculate_error_trend()
        }

    def _calculate_error_trend(self) -> str:
        """最近のエラー率トレンドを計算"""
        recent_errors = self.execution_stats["error_details"][-20:]  # 最新20件
        if len(recent_errors) < 5:
            return "insufficient_data"

        # 前半と後半でエラー数比較
        half_point = len(recent_errors) // 2
        first_half = recent_errors[:half_point]
        second_half = recent_errors[half_point:]

        if len(second_half) > len(first_half):
            return "increasing"
        elif len(second_half) < len(first_half):
            return "decreasing"
        else:
            return "stable"

    async def test_connection(self) -> Dict[str, Any]:
        """API接続テスト"""
        try:
            test_prompt = "Hello, are you working? Please respond with 'API connection successful'."
            response = await self._call_gemini_api(test_prompt)

            return {
                "status": "success",
                "response": response,
                "api_available": True
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "api_available": False
            }


# CLI実行用
async def main() -> None:
    """CLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Gemini API統合実行システム")
    parser.add_argument("--test", action="store_true", help="API接続テスト")
    parser.add_argument("--instruction", help="作業指示書ファイル")
    parser.add_argument("--task-id", help="タスクID")
    parser.add_argument("--stats", action="store_true", help="実行統計表示")

    args = parser.parse_args()

    try:
        executor = GeminiAPIExecutor()

        if args.test:
            print("🧪 Gemini API接続テスト...")
            result = await executor.test_connection()
            if result["status"] == "success":
                print("✅ API接続成功")
                print(f"レスポンス: {result['response']}")
            else:
                print("❌ API接続失敗")
                print(f"エラー: {result['error']}")
            return

        if args.stats:
            stats = executor.get_execution_stats()
            print("📊 Gemini API実行統計")
            print("=" * 30)
            for key, value in stats.items():
                print(f"{key}: {value}")
            return

        if args.instruction and args.task_id:
            with open(args.instruction, 'r', encoding='utf-8') as f:
                instruction = f.read()

            result = await executor.execute_task(instruction, args.task_id)
            print(f"\n🎯 実行結果:")
            print(f"ステータス: {result['status']}")
            print(f"実装ファイル数: {len(result['implemented_files'])}")
            print(f"実装行数: {result['modified_lines']}")
            print(f"実行時間: {result['execution_time']}秒")

            if result['errors']:
                print(f"\nエラー: {result['errors']}")

            return

        parser.print_help()

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
