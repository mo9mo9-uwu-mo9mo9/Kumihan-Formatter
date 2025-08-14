#!/usr/bin/env python3
"""Gemini協業自動判定システム

作業開始時にGemini協業が必要かを自動判定し、Token節約を実現する。
Issue #876の反省を踏まえた改善システム。

Usage:
    python gemini_collaboration_checker.py "MyPy型注釈修正作業"
    python gemini_collaboration_checker.py --check-todo "MyPy Strictモードエラー修正（5件のno-any-return）"

Created: 2025-08-14 (Issue #876反省改善)
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

class GeminiCollaborationChecker:
    """Gemini協業判定システム"""

    # Gemini協業対象パターン（定型作業）
    GEMINI_PATTERNS = {
        "mypy_fixes": [
            r"mypy.*修正",
            r"型注釈.*修正",
            r"no-any-return",
            r"return.*型.*修正",
            r"strict.*mode.*エラー"
        ],
        "lint_fixes": [
            r"flake8.*修正",
            r"lint.*修正",
            r"未使用.*インポート",
            r"長い行.*分割",
            r"E501.*修正",
            r"F401.*修正"
        ],
        "formatting": [
            r"black.*整形",
            r"isort.*修正",
            r"インポート.*順序",
            r"フォーマット.*修正",
            r"コード.*整形"
        ],
        "batch_processing": [
            r"複数ファイル",
            r"一括.*処理",
            r"[\d]+ファイル.*修正",
            r"全.*ファイル.*対応"
        ],
        "repetitive_tasks": [
            r"[\d]+件.*修正",
            r"同様.*修正",
            r"繰り返し.*作業",
            r"定型.*作業"
        ]
    }

    # Token使用量推定（概算）
    TOKEN_ESTIMATES = {
        "mypy_single_fix": 200,
        "mypy_batch_fix": 500,
        "flake8_single_fix": 150,
        "flake8_batch_fix": 400,
        "format_single_file": 100,
        "format_batch_files": 300,
        "code_review": 300,
        "test_execution": 200
    }

    # Gemini協業推奨しきい値
    GEMINI_THRESHOLD_TOKENS = 1000
    GEMINI_THRESHOLD_FILES = 3

    def __init__(self):
        """初期化"""
        self.reports_dir = Path(__file__).parent
        self.history_file = self.reports_dir / "collaboration_history.json"

    def check_gemini_needed(self, task_description: str) -> Tuple[bool, Dict[str, Any]]:
        """
        作業内容からGemini協業が必要かを判定

        Args:
            task_description: 作業内容の説明

        Returns:
            Tuple[bool, Dict]: (Gemini必要か, 詳細情報)
        """
        results = {
            "task": task_description,
            "gemini_recommended": False,
            "confidence": 0.0,
            "reasons": [],
            "patterns_matched": [],
            "estimated_tokens": 0,
            "cost_savings_potential": "0%",
            "automation_level": "MANUAL_ONLY"
        }

        # パターンマッチング分析
        matched_categories = []
        for category, patterns in self.GEMINI_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, task_description, re.IGNORECASE):
                    matched_categories.append(category)
                    results["patterns_matched"].append(f"{category}: {pattern}")
                    break

        # Token使用量推定
        estimated_tokens = self._estimate_tokens(task_description, matched_categories)
        results["estimated_tokens"] = estimated_tokens

        # Gemini推奨判定ロジック
        gemini_needed = False
        reasons = []
        confidence = 0.0

        # 1. 定型作業パターンチェック
        if matched_categories:
            gemini_needed = True
            reasons.append(f"定型作業パターン検出: {', '.join(matched_categories)}")
            confidence += 0.3

        # 2. Token使用量チェック
        if estimated_tokens >= self.GEMINI_THRESHOLD_TOKENS:
            gemini_needed = True
            reasons.append(f"Token使用量 {estimated_tokens} >= しきい値 {self.GEMINI_THRESHOLD_TOKENS}")
            confidence += 0.4

        # 3. 複数ファイル処理チェック
        file_count = self._extract_file_count(task_description)
        if file_count >= self.GEMINI_THRESHOLD_FILES:
            gemini_needed = True
            reasons.append(f"複数ファイル処理 ({file_count}ファイル)")
            confidence += 0.3

        # 自動化レベル判定
        automation_level = self._determine_automation_level(
            matched_categories, estimated_tokens, confidence
        )

        # コスト削減効果計算
        cost_savings = self._calculate_cost_savings(estimated_tokens)

        # 結果更新
        results.update({
            "gemini_recommended": gemini_needed,
            "confidence": min(confidence, 1.0),
            "reasons": reasons,
            "cost_savings_potential": f"{cost_savings}%",
            "automation_level": automation_level
        })

        return gemini_needed, results

    def _estimate_tokens(self, task_description: str, categories: List[str]) -> int:
        """Token使用量を推定"""
        base_tokens = 500  # 基本作業

        # カテゴリ別加算
        for category in categories:
            if category == "mypy_fixes":
                # MyPy修正の件数を推定
                match = re.search(r"(\d+)件", task_description)
                if match:
                    count = int(match.group(1))
                    base_tokens += count * self.TOKEN_ESTIMATES["mypy_single_fix"]
                else:
                    base_tokens += self.TOKEN_ESTIMATES["mypy_batch_fix"]

            elif category == "lint_fixes":
                base_tokens += self.TOKEN_ESTIMATES["flake8_batch_fix"]

            elif category == "formatting":
                # ファイル数を推定
                file_count = self._extract_file_count(task_description)
                if file_count > 1:
                    base_tokens += file_count * self.TOKEN_ESTIMATES["format_single_file"]
                else:
                    base_tokens += self.TOKEN_ESTIMATES["format_batch_files"]

            elif category == "batch_processing":
                base_tokens += 1000  # 一括処理は大きめ

        # コードレビュー・テスト実行の加算
        if re.search(r"レビュー|確認", task_description):
            base_tokens += self.TOKEN_ESTIMATES["code_review"]

        if re.search(r"テスト|test", task_description):
            base_tokens += self.TOKEN_ESTIMATES["test_execution"]

        return base_tokens

    def _extract_file_count(self, text: str) -> int:
        """テキストからファイル数を抽出"""
        # "5ファイル" のようなパターンを検索
        match = re.search(r"(\d+)ファイル", text)
        if match:
            return int(match.group(1))

        # "複数ファイル" は最低3ファイルと推定
        if re.search(r"複数.*ファイル", text):
            return 3

        return 1

    def _determine_automation_level(self, categories: List[str], tokens: int, confidence: float) -> str:
        """自動化レベルを判定"""
        if confidence >= 0.8 and tokens >= 2000:
            return "FULL_AUTO"
        elif confidence >= 0.6 and ("mypy_fixes" in categories or "lint_fixes" in categories):
            return "SEMI_AUTO"
        elif confidence >= 0.4:
            return "APPROVAL_REQUIRED"
        else:
            return "MANUAL_ONLY"

    def _calculate_cost_savings(self, estimated_tokens: int) -> int:
        """コスト削減効果を計算（概算）"""
        if estimated_tokens < 1000:
            return 0

        # Claude vs Gemini のコスト比率（概算）
        # Claude: $15/1M input, $75/1M output
        # Gemini Flash: $0.30/1M input, $2.50/1M output
        claude_cost = estimated_tokens * (15 + 75) / 1_000_000  # 簡易計算
        gemini_cost = estimated_tokens * (0.30 + 2.50) / 1_000_000

        if claude_cost > 0:
            savings = ((claude_cost - gemini_cost) / claude_cost) * 100
            return min(int(savings), 99)  # 最大99%

        return 0

    def generate_gemini_instruction(self, task_description: str, results: Dict[str, Any]) -> str:
        """Gemini向けの作業指示書を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        instruction = f"""# Gemini協業指示書

## 作業概要
- **タスク**: {task_description}
- **生成日時**: {timestamp}
- **自動化レベル**: {results['automation_level']}
- **推定Token節約**: {results['cost_savings_potential']}

## 検出パターン
{chr(10).join(f"- {pattern}" for pattern in results['patterns_matched'])}

## 作業指示

### 実行対象
```bash
# 以下のコマンドを実行してください
"""

        # パターンに応じた具体的指示を追加
        if "mypy_fixes" in str(results["patterns_matched"]):
            instruction += """
python3 -m mypy kumihan_formatter --strict
# エラー箇所の型注釈を修正
# None → Any の変更を適切に実施
"""

        if "lint_fixes" in str(results["patterns_matched"]):
            instruction += """
python3 -m flake8 kumihan_formatter
# 検出されたエラーを自動修正
# 未使用インポート削除、長い行分割など
"""

        if "formatting" in str(results["patterns_matched"]):
            instruction += """
python3 -m black kumihan_formatter
python3 -m isort kumihan_formatter
# コードフォーマットの統一
"""

        instruction += """
```

### 品質確認
1. 修正後の構文エラーチェック
2. 既存テストの通過確認
3. 変更内容のサマリー作成

### 報告書作成
- 修正ファイル一覧
- 変更内容詳細
- 品質チェック結果
- 次のClaude確認ポイント

## 注意事項
- 3層検証体制に従い、構文チェック→品質チェック→Claude最終確認
- エラーが発生した場合は即座に報告
- 既存機能への影響がないことを確認

---
*自動生成 - gemini_collaboration_checker.py*
"""

        return instruction

    def save_collaboration_history(self, results: Dict[str, Any]) -> None:
        """協業履歴を保存"""
        history = []
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": results["task"],
            "gemini_recommended": results["gemini_recommended"],
            "confidence": results["confidence"],
            "estimated_tokens": results["estimated_tokens"],
            "cost_savings_potential": results["cost_savings_potential"]
        }

        history.append(entry)

        # 最新100件のみ保持
        if len(history) > 100:
            history = history[-100:]

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

def main():
    """コマンドライン実行"""
    if len(sys.argv) < 2:
        print("Usage: python gemini_collaboration_checker.py 'task_description'")
        print("Example: python gemini_collaboration_checker.py 'MyPy型注釈修正（5件）'")
        sys.exit(1)

    task_description = sys.argv[1]
    checker = GeminiCollaborationChecker()

    # 判定実行
    gemini_needed, results = checker.check_gemini_needed(task_description)

    # 結果表示
    print(f"\n🤖 Gemini協業判定結果")
    print(f"=" * 50)
    print(f"タスク: {task_description}")
    print(f"Gemini推奨: {'✅ YES' if gemini_needed else '❌ NO'}")
    print(f"信頼度: {results['confidence']:.1%}")
    print(f"推定Token: {results['estimated_tokens']:,}")
    print(f"コスト削減効果: {results['cost_savings_potential']}")
    print(f"自動化レベル: {results['automation_level']}")

    if results['reasons']:
        print(f"\n📋 推奨理由:")
        for reason in results['reasons']:
            print(f"  - {reason}")

    if results['patterns_matched']:
        print(f"\n🎯 マッチしたパターン:")
        for pattern in results['patterns_matched']:
            print(f"  - {pattern}")

    # Gemini指示書生成（推奨時）
    if gemini_needed:
        instruction = checker.generate_gemini_instruction(task_description, results)
        instruction_file = checker.reports_dir / f"gemini_instruction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(instruction_file, 'w', encoding='utf-8') as f:
            f.write(instruction)

        print(f"\n📄 Gemini指示書生成: {instruction_file}")
        print(f"💡 Geminiに上記ファイルを渡して作業実行してください")

    # 履歴保存
    checker.save_collaboration_history(results)

    return 0 if gemini_needed else 1

if __name__ == "__main__":
    sys.exit(main())
