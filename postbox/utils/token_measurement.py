#!/usr/bin/env python3
"""
Token Usage Measurement System for Accurate Cost Management
Gemini API実行時の実際のToken使用量測定・コスト計算システム
"""

import datetime
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TokenUsage:
    """Token使用量データクラス"""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    model: str
    timestamp: str
    task_id: Optional[str] = None


class TokenMeasurementSystem:
    """Token使用量動的測定システム"""

    def __init__(self, data_dir: str = "postbox/monitoring"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # データファイルパス
        self.cost_tracking_path = self.data_dir / "cost_tracking.json"
        self.accuracy_history_path = self.data_dir / "token_accuracy.json"
        self.measurement_log_path = self.data_dir / "token_measurements.json"

        # Gemini 2.5 Flash料金設定（USD per 1M tokens）
        self.pricing = {
            "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
            "claude-3-opus": {"input": 15.00, "output": 75.00},
        }

        # 測定精度追跡
        self.accuracy_data = self._load_accuracy_data()

        print("🧮 TokenMeasurementSystem 初期化完了")
        print(f"📊 現在の測定精度: {self.get_current_accuracy():.1%}")

    def measure_actual_tokens(
        self, api_response: Dict[str, Any], model: str = "gemini-2.5-flash"
    ) -> TokenUsage:
        """Gemini API応答から実際のToken使用量を測定"""

        try:
            # API応答からToken情報を抽出
            input_tokens = self._extract_input_tokens(api_response)
            output_tokens = self._extract_output_tokens(api_response)

            # 抽出できない場合の推定処理
            if input_tokens == 0 or output_tokens == 0:
                print(
                    "⚠️ API応答からToken数を抽出できませんでした。推定値を使用します。"
                )
                input_tokens, output_tokens = self._estimate_tokens_from_response(
                    api_response
                )

            total_tokens = input_tokens + output_tokens
            cost = self.calculate_real_cost(input_tokens, output_tokens, model)

            token_usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                model=model,
                timestamp=datetime.datetime.now().isoformat(),
            )

            print(
                f"📊 Token測定結果: 入力={input_tokens}, 出力={output_tokens}, コスト=${cost:.4f}"
            )

            return token_usage

        except Exception as e:
            print(f"❌ Token測定エラー: {e}")
            # フォールバック: 推定値を返す
            return self._create_fallback_usage(model)

    def calculate_real_cost(
        self, input_tokens: int, output_tokens: int, model: str = "gemini-2.5-flash"
    ) -> float:
        """実際のToken使用量に基づくコスト計算"""

        if model not in self.pricing:
            print(f"⚠️ 未知のモデル: {model}。デフォルト料金を使用。")
            model = "gemini-2.5-flash"

        pricing = self.pricing[model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        total_cost = input_cost + output_cost

        return round(total_cost, 6)  # 小数点6桁まで

    def track_efficiency(
        self, estimated_tokens: int, actual_usage: TokenUsage
    ) -> Dict[str, Any]:
        """測定精度・効率性追跡"""

        actual_total = actual_usage.total_tokens
        accuracy_ratio = (
            actual_total / estimated_tokens if estimated_tokens > 0 else 1.0
        )

        efficiency_data = {
            "estimated_tokens": estimated_tokens,
            "actual_tokens": actual_total,
            "accuracy_ratio": accuracy_ratio,
            "precision": 1.0
            - min(abs(accuracy_ratio - 1.0), 1.0),  # 1.0に近いほど精度が高い
            "cost_difference": self.calculate_real_cost(estimated_tokens, 0)
            - actual_usage.cost,
            "model": actual_usage.model,
            "timestamp": actual_usage.timestamp,
        }

        # 精度データ蓄積
        self._record_accuracy(efficiency_data)

        print(
            f"📈 効率性追跡: 精度={efficiency_data['precision']:.1%}, "
            f"実測比={accuracy_ratio:.2f}"
        )

        return efficiency_data

    def update_cost_tracking(self, task_id: str, actual_usage: TokenUsage) -> None:
        """cost_tracking.jsonを実測値で更新"""

        try:
            # 既存データ読み込み
            if self.cost_tracking_path.exists():
                with open(self.cost_tracking_path, "r", encoding="utf-8") as f:
                    cost_data = json.load(f)
            else:
                cost_data = {"total_cost": 0.0, "tasks": []}

            # 新しいタスクデータ作成
            task_data = {
                "task_id": task_id,
                "timestamp": actual_usage.timestamp,
                "token_usage": {
                    "input_tokens": actual_usage.input_tokens,
                    "output_tokens": actual_usage.output_tokens,
                    "model": actual_usage.model,
                },
                "estimated_cost": actual_usage.cost,
                "measurement_method": "actual_api_response",
            }

            # 既存タスクの更新または追加
            task_found = False
            for i, existing_task in enumerate(cost_data["tasks"]):
                if existing_task["task_id"] == task_id:
                    cost_data["tasks"][i] = task_data
                    task_found = True
                    break

            if not task_found:
                cost_data["tasks"].append(task_data)

            # 総コスト再計算
            cost_data["total_cost"] = sum(
                task.get("estimated_cost", 0.0) for task in cost_data["tasks"]
            )

            # ファイル保存
            with open(self.cost_tracking_path, "w", encoding="utf-8") as f:
                json.dump(cost_data, f, indent=2, ensure_ascii=False)

            print(f"💾 コスト追跡更新: {task_id} → ${actual_usage.cost:.4f}")

        except Exception as e:
            print(f"❌ コスト追跡更新エラー: {e}")

    def get_current_accuracy(self) -> float:
        """現在の測定精度取得"""

        records = self.accuracy_data.get("records", [])
        if not records:
            return 0.0

        # 最新10件の精度計算
        recent_records = records[-10:]
        precisions = [record.get("precision", 0.0) for record in recent_records]

        return statistics.mean(precisions) if precisions else 0.0

    def generate_accuracy_report(self) -> Dict[str, Any]:
        """精度レポート生成"""

        records = self.accuracy_data.get("records", [])

        if not records:
            return {"status": "no_data", "message": "測定データがありません"}

        # 統計計算
        recent_records = records[-20:] if len(records) >= 20 else records
        accuracy_ratios = [r["accuracy_ratio"] for r in recent_records]
        precisions = [r["precision"] for r in recent_records]

        report = {
            "total_measurements": len(records),
            "recent_measurements": len(recent_records),
            "current_accuracy": statistics.mean(precisions) if precisions else 0.0,
            "accuracy_trend": {
                "mean_ratio": (
                    statistics.mean(accuracy_ratios) if accuracy_ratios else 1.0
                ),
                "std_deviation": (
                    statistics.stdev(accuracy_ratios)
                    if len(accuracy_ratios) > 1
                    else 0.0
                ),
                "min_ratio": min(accuracy_ratios) if accuracy_ratios else 1.0,
                "max_ratio": max(accuracy_ratios) if accuracy_ratios else 1.0,
            },
            "target_achievement": {
                "target_accuracy": 0.8,  # 80%精度目標
                "current_status": (
                    "達成"
                    if (statistics.mean(precisions) if precisions else 0.0) >= 0.8
                    else "未達成"
                ),
                "improvement_needed": max(
                    0.8 - (statistics.mean(precisions) if precisions else 0.0), 0
                ),
            },
            "recommendations": self._generate_accuracy_recommendations(recent_records),
        }

        return report

    def _extract_input_tokens(self, api_response: Dict[str, Any]) -> int:
        """API応答から入力Token数を抽出"""

        # Gemini API応答フォーマットに基づく抽出
        try:
            # 一般的なパターン
            if "usage" in api_response:
                return int(api_response["usage"].get("prompt_tokens", 0))

            # 別のパターン
            if "metadata" in api_response:
                usage = api_response["metadata"].get("usage", {})
                return int(usage.get("input_tokens", 0))

            # さらに別のパターン
            if "input_tokens" in api_response:
                return int(api_response["input_tokens"])

            return 0

        except Exception as e:
            print(f"⚠️ 入力Token抽出エラー: {e}")
            return 0

    def _extract_output_tokens(self, api_response: Dict[str, Any]) -> int:
        """API応答から出力Token数を抽出"""

        try:
            # 一般的なパターン
            if "usage" in api_response:
                return int(api_response["usage"].get("completion_tokens", 0))

            # 別のパターン
            if "metadata" in api_response:
                usage = api_response["metadata"].get("usage", {})
                return int(usage.get("output_tokens", 0))

            # さらに別のパターン
            if "output_tokens" in api_response:
                return int(api_response["output_tokens"])

            return 0

        except Exception as e:
            print(f"⚠️ 出力Token抽出エラー: {e}")
            return 0

    def _estimate_tokens_from_response(
        self, api_response: Dict[str, Any]
    ) -> Tuple[int, int]:
        """API応答から推定Token数を計算"""

        try:
            # レスポンステキストから推定
            response_text = ""

            # テキスト抽出パターン
            if "choices" in api_response and api_response["choices"]:
                response_text = (
                    api_response["choices"][0].get("message", {}).get("content", "")
                )
            elif "text" in api_response:
                response_text = api_response["text"]
            elif "content" in api_response:
                response_text = str(api_response["content"])
            else:
                response_text = str(api_response)

            # 簡易的なToken推定（1Token = 約4文字）
            estimated_output = max(len(response_text) // 4, 100)
            estimated_input = max(
                estimated_output // 2, 200
            )  # 入力は出力の約半分と仮定

            return estimated_input, estimated_output

        except Exception:
            # デフォルト推定値
            return 500, 300

    def _create_fallback_usage(self, model: str) -> TokenUsage:
        """フォールバック用Token使用量作成"""

        # 保守的な推定値
        input_tokens = 600
        output_tokens = 400
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_real_cost(input_tokens, output_tokens, model)

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            model=model,
            timestamp=datetime.datetime.now().isoformat(),
        )

    def _record_accuracy(self, efficiency_data: Dict[str, Any]) -> None:
        """精度データの記録"""

        self.accuracy_data["records"].append(efficiency_data)

        # データサイズ制限（最新100件）
        if len(self.accuracy_data["records"]) > 100:
            self.accuracy_data["records"] = self.accuracy_data["records"][-100:]

        # 統計更新
        self.accuracy_data["last_update"] = datetime.datetime.now().isoformat()
        self._save_accuracy_data()

    def _load_accuracy_data(self) -> Dict[str, Any]:
        """精度データ読み込み"""

        if self.accuracy_history_path.exists():
            try:
                with open(self.accuracy_history_path, "r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                    return data
            except Exception as e:
                print(f"⚠️ 精度データ読み込みエラー: {e}")

        # デフォルトデータ
        return {
            "records": [],
            "last_update": datetime.datetime.now().isoformat(),
            "version": "1.0",
        }

    def _save_accuracy_data(self) -> None:
        """精度データ保存"""

        try:
            with open(self.accuracy_history_path, "w", encoding="utf-8") as f:
                json.dump(self.accuracy_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 精度データ保存エラー: {e}")

    def _generate_accuracy_recommendations(
        self, recent_records: List[Dict[str, Any]]
    ) -> List[str]:
        """精度改善提案生成"""

        if not recent_records:
            return ["データ蓄積中のため、提案はありません"]

        recommendations = []
        accuracy_ratios = [r["accuracy_ratio"] for r in recent_records]
        avg_ratio = statistics.mean(accuracy_ratios)

        if avg_ratio > 1.2:
            recommendations.append(
                "実測値が見積もりを20%以上上回っています。見積もりアルゴリズムの調整を推奨"
            )
        elif avg_ratio < 0.8:
            recommendations.append(
                "実測値が見積もりを20%以上下回っています。見積もりの精度向上余地あり"
            )

        if len(accuracy_ratios) > 1:
            std_dev = statistics.stdev(accuracy_ratios)
            if std_dev > 0.3:
                recommendations.append(
                    "測定結果のばらつきが大きいです。測定方法の安定化を推奨"
                )

        current_accuracy = statistics.mean(
            [r.get("precision", 0) for r in recent_records]
        )
        if current_accuracy < 0.8:
            recommendations.append(
                f"現在の精度{current_accuracy:.1%}は目標80%を下回っています。測定方法の見直しを推奨"
            )

        if not recommendations:
            recommendations.append("測定精度は良好です。現在の方法を継続してください")

        return recommendations

    def export_measurement_log(self, output_path: Optional[str] = None) -> str:
        """測定ログのエクスポート"""

        if output_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"tmp/token_measurements_export_{timestamp}.json"

        export_data = {
            "export_timestamp": datetime.datetime.now().isoformat(),
            "measurement_system_version": "1.0",
            "accuracy_data": self.accuracy_data,
            "pricing_config": self.pricing,
            "summary": self.generate_accuracy_report(),
        }

        # ファイル出力
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"📤 測定ログエクスポート完了: {output_path}")

        return output_path


def main() -> None:
    """テスト実行"""

    # システム初期化
    measurement_system = TokenMeasurementSystem()

    # サンプルAPI応答でテスト
    sample_response = {
        "usage": {"prompt_tokens": 1234, "completion_tokens": 567},
        "choices": [
            {
                "message": {
                    "content": (
                        "This is a sample response for testing token measurement."
                    )
                }
            }
        ],
    }

    # Token測定テスト
    usage = measurement_system.measure_actual_tokens(sample_response)
    print("\n📊 測定結果:")
    print(f"入力Token: {usage.input_tokens}")
    print(f"出力Token: {usage.output_tokens}")
    print(f"コスト: ${usage.cost:.4f}")

    # 効率性追跡テスト
    efficiency = measurement_system.track_efficiency(1500, usage)
    print(f"\n📈 効率性: {efficiency['precision']:.1%}")

    # コスト追跡更新テスト
    measurement_system.update_cost_tracking("test_task_001", usage)

    # 精度レポート生成
    report = measurement_system.generate_accuracy_report()
    print(f"\n📋 精度レポート: {report['current_accuracy']:.1%}")


if __name__ == "__main__":
    main()
