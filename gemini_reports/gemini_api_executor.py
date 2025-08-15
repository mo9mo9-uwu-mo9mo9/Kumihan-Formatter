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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import google.generativeai as genai
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
        genai.configure(api_key=self.api_key)  # type: ignore
        model_name = self.config["gemini_api"]["model_name"]
        self.model = genai.GenerativeModel(model_name)  # type: ignore

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
                config_data: Dict[str, Any] = json.load(f)
                return config_data
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

    def _determine_task_type(self, work_instruction: str) -> str:
        """作業指示書からタスクタイプを自動判定

        Args:
            work_instruction: 作業指示書の内容

        Returns:
            タスクタイプ ('modification', 'creation', 'enhancement')
        """
        instruction_lower = work_instruction.lower()

        # 修正タスクのキーワード
        modification_keywords = [
            '修正', 'fix', 'error', 'エラー', 'mypy', 'flake8', 'lint',
            '型注釈', 'type annotation', 'バグ', 'bug', '改修'
        ]

        # 新規作成タスクのキーワード
        creation_keywords = [
            'tmp/', '新規', '作成', 'create', '実装', 'implement',
            'システム', 'dashboard', 'ダッシュボード'
        ]

        # ファイル修正の明示的指定チェック
        if any(keyword in instruction_lower for keyword in modification_keywords):
            # 既存ファイルディレクトリの言及をチェック
            existing_dirs = ['gemini_reports/', 'kumihan_formatter/', 'docs/', 'core/']
            if any(dir_name in work_instruction for dir_name in existing_dirs):
                return 'modification'

        # 明示的にtmp/指定やシステム作成
        if any(keyword in instruction_lower for keyword in creation_keywords):
            return 'creation'

        # 機能追加・拡張
        enhancement_keywords = ['追加', 'add', '機能', 'feature', '拡張', 'extend']
        if any(keyword in instruction_lower for keyword in enhancement_keywords):
            return 'enhancement'

        # デフォルトは新規作成（安全側）
        return 'creation'

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

        # タスクタイプ自動判定
        task_type = self._determine_task_type(work_instruction)

        result: Dict[str, Any] = {
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
                implemented_files = await self._implement_code(extracted_code, task_id, task_type)
                result["implemented_files"] = implemented_files
                result["modified_lines"] = self._count_total_lines(implemented_files)

                # Phase 4: 品質検証・フィードバック強化
                quality_check_result = await self._perform_quality_verification(
                    implemented_files, task_id, work_instruction
                )
                result["quality_checks"] = quality_check_result["checks"]
                result["quality_feedback"] = quality_check_result["feedback"]

                # 品質検証結果に基づく状態判定
                if quality_check_result["overall_pass"]:
                    result["status"] = "completed"
                    print(f"✅ Gemini実装完了: {len(implemented_files)}ファイル")
                    self.execution_stats["successful_requests"] += 1
                else:
                    result["status"] = "quality_failed"
                    result["errors"].extend(quality_check_result["errors"])
                    print(f"⚠️ Gemini実装品質不適合: {quality_check_result['errors']}")
                    self.execution_stats["failed_requests"] += 1
                    # 学習データに記録
                    await self._record_failure_pattern(work_instruction, quality_check_result)
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

    def _resolve_file_path(self, file_path: str, task_type: str) -> str:
        """タスクタイプに基づいてファイルパスを解決

        Args:
            file_path: 元のファイルパス
            task_type: タスクタイプ

        Returns:
            解決されたファイルパス
        """
        # 絶対パスの場合
        if file_path.startswith('/'):
            return file_path.lstrip('/')

        # 既に適切なプレフィックスがある場合
        if file_path.startswith(('kumihan_formatter/', 'tmp/', 'docs/', 'gemini_reports/')):
            return file_path

        # タスクタイプ別の処理
        if task_type == 'modification':
            # 修正タスクの場合：既存ファイル構造を推定

            # gemini_reportsディレクトリのファイル修正
            if any(hint in file_path.lower() for hint in ['gemini', 'api', 'orchestrator', 'config']):
                return f"gemini_reports/{file_path}"

            # kumihan_formatterディレクトリのファイル修正
            if any(hint in file_path.lower() for hint in ['core', 'parser', 'formatter', 'cli']):
                return f"kumihan_formatter/{file_path}"

            # docsディレクトリのファイル修正
            if any(hint in file_path.lower() for hint in ['doc', 'guide', 'readme', 'md']):
                return f"docs/{file_path}"

            # 既存ファイルが存在するかチェック
            import os
            possible_paths = [
                f"gemini_reports/{file_path}",
                f"kumihan_formatter/{file_path}",
                f"docs/{file_path}",
                file_path  # 現在のディレクトリ直下
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    self.logger.info(f"既存ファイル発見: {path}")
                    return path

            # 既存ファイルが見つからない場合は警告してtmp/配下に
            self.logger.warning(f"修正対象ファイルが見つかりません: {file_path}, tmp/配下に作成します")
            return f"tmp/{file_path}"

        elif task_type == 'enhancement':
            # 機能追加の場合：既存プロジェクト構造に追加
            if 'gemini' in file_path.lower():
                return f"gemini_reports/{file_path}"
            else:
                return f"kumihan_formatter/{file_path}"

        else:  # task_type == 'creation' or default
            # 新規作成の場合：tmp/配下に作成
            return f"tmp/{file_path}"

    async def _implement_code(self, extracted_code: Dict[str, str], task_id: str, task_type: str = 'creation') -> List[str]:
        """抽出したコードを実際のファイルに実装

        Args:
            extracted_code: 抽出されたコード辞書
            task_id: タスクID
            task_type: タスクタイプ ('modification', 'creation', 'enhancement')
        """
        implemented_files = []

        for file_path, code in extracted_code.items():
            try:
                # ファイルパス正規化（タスクタイプ考慮）
                full_path = self._resolve_file_path(file_path, task_type)

                self.logger.info(f"📁 ファイル実装開始: {file_path} → {full_path} (type: {task_type})")

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

    async def _perform_quality_verification(self, implemented_files: List[str], task_id: str, work_instruction: str) -> Dict[str, Any]:
        """品質検証・フィードバック強化システム

        Args:
            implemented_files: 実装済みファイル一覧
            task_id: タスクID
            work_instruction: 元の作業指示書

        Returns:
            品質検証結果とフィードバック
        """
        self.logger.info(f"🔍 品質検証開始: {task_id}")

        verification_result: Dict[str, Any] = {
            "checks": {
                "syntax_pass": True,
                "mypy_pass": True,
                "flake8_pass": True,
                "file_location_correct": True
            },
            "feedback": [],
            "errors": [],
            "overall_pass": True
        }

        try:
            # 1. ファイル配置確認（重要な改善点）
            location_check = await self._verify_file_locations(implemented_files, work_instruction)
            verification_result["checks"]["file_location_correct"] = location_check["correct"]
            if not location_check["correct"]:
                verification_result["errors"].extend(location_check["errors"])
                verification_result["feedback"].append("修正ファイルがtmp/配下に保存されました。既存ファイル修正の場合は元の場所に保存すべきです。")

            # 2. MyPy型注釈修正の実効性確認
            if "mypy" in work_instruction.lower() or "型注釈" in work_instruction:
                mypy_check = await self._verify_mypy_fixes(implemented_files)
                verification_result["checks"]["mypy_pass"] = mypy_check["pass"]
                if not mypy_check["pass"]:
                    verification_result["errors"].extend(mypy_check["errors"])
                    verification_result["feedback"].append("MyPy修正が不完全です。再修正が必要です。")

            # 3. 構文チェック強化
            for file_path in implemented_files:
                if file_path.endswith('.py'):
                    syntax_ok = await self._enhanced_syntax_check(file_path)
                    if not syntax_ok:
                        verification_result["checks"]["syntax_pass"] = False
                        verification_result["errors"].append(f"構文エラー: {file_path}")

            # 4. 総合判定
            verification_result["overall_pass"] = all(verification_result["checks"].values())

            # 5. 改善提案生成
            if not verification_result["overall_pass"]:
                improvement_suggestions = await self._generate_improvement_suggestions(
                    verification_result["errors"], work_instruction
                )
                verification_result["improvement_suggestions"] = improvement_suggestions

        except Exception as e:
            self.logger.error(f"品質検証中にエラー: {e}")
            verification_result["errors"].append(f"品質検証システムエラー: {str(e)}")
            verification_result["overall_pass"] = False

        self.logger.info(f"品質検証完了: {task_id} (合格: {verification_result['overall_pass']})")
        return verification_result

    async def _verify_file_locations(self, implemented_files: List[str], work_instruction: str) -> Dict[str, Any]:
        """ファイル配置の正確性を検証"""
        result: Dict[str, Any] = {"correct": True, "errors": []}

        # 修正タスクかどうかを判定
        is_modification_task = any(
            keyword in work_instruction.lower()
            for keyword in ['修正', 'fix', 'error', 'エラー', 'mypy', 'flake8']
        )

        if is_modification_task:
            for file_path in implemented_files:
                if file_path.startswith('tmp/') and not 'tmp/' in work_instruction:
                    result["correct"] = False
                    result["errors"].append(f"修正対象ファイルがtmp/配下に保存: {file_path}")

        return result

    async def _verify_mypy_fixes(self, implemented_files: List[str]) -> Dict[str, Any]:
        """MyPy修正の実効性を検証"""
        result: Dict[str, Any] = {"pass": True, "errors": []}

        try:
            for file_path in implemented_files:
                if file_path.endswith('.py'):
                    # MyPyチェック実行
                    mypy_result = subprocess.run(
                        [sys.executable, "-m", "mypy", file_path, "--strict"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if mypy_result.returncode != 0:
                        result["pass"] = False
                        result["errors"].append(f"MyPyエラー ({file_path}): {mypy_result.stdout}")

        except Exception as e:
            result["pass"] = False
            result["errors"].append(f"MyPy検証エラー: {str(e)}")

        return result

    async def _enhanced_syntax_check(self, file_path: str) -> bool:
        """強化された構文チェック"""
        try:
            # 基本構文チェック
            result = subprocess.run(
                [sys.executable, "-c", f"import ast; ast.parse(open('{file_path}').read())"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _generate_improvement_suggestions(self, errors: List[str], work_instruction: str) -> List[str]:
        """品質改善提案を生成"""
        suggestions = []

        # エラーパターン別の改善提案
        for error in errors:
            if "tmp/配下に保存" in error:
                suggestions.append("指示書にファイル修正の場合は '既存ファイルの直接修正' を明記する")
            elif "MyPyエラー" in error:
                suggestions.append("型注釈修正時はより具体的な型指定例を提供する")
            elif "構文エラー" in error:
                suggestions.append("完全なファイル実装を要求し、コード片の提供を禁止する")

        return suggestions

    async def _record_failure_pattern(self, work_instruction: str, quality_result: Dict[str, Any]) -> None:
        """失敗パターンを学習データとして記録"""
        try:
            failure_pattern = {
                "timestamp": datetime.now().isoformat(),
                "instruction_type": self._determine_task_type(work_instruction),
                "instruction_length": len(work_instruction),
                "failure_reasons": quality_result["errors"],
                "improvement_suggestions": quality_result.get("improvement_suggestions", []),
                "quality_checks": quality_result["checks"]
            }

            # 学習データファイルに追記
            learning_file = Path("gemini_reports/failure_patterns.json")
            if learning_file.exists():
                with open(learning_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
            else:
                patterns = []

            patterns.append(failure_pattern)

            # 最新100件のみ保持
            if len(patterns) > 100:
                patterns = patterns[-100:]

            with open(learning_file, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)

            self.logger.info(f"失敗パターンを記録: {learning_file}")

        except Exception as e:
            self.logger.error(f"失敗パターン記録エラー: {e}")

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
