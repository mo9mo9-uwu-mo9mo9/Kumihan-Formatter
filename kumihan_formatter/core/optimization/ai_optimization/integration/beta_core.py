"""
Beta統合コアシステム実装

Alpha-Beta協調制御・相乗効果計算
- Alpha基盤+Beta拡張協調制御
- 相乗効果計算・最大化
- 統合モード管理・効果測定
"""

import time
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from kumihan_formatter.core.utilities.logger import get_logger

from ..autonomous.controller import AutonomousController
from ..basic_ml_system import BasicMLSystem
from ..learning.system import LearningSystem
from ..prediction_engine import PredictionEngine

warnings.filterwarnings("ignore")


class IntegrationMode(Enum):
    """統合モード列挙"""

    ALPHA_ONLY = "alpha_only"
    BETA_ENHANCED = "beta_enhanced"
    FULL_INTEGRATION = "full_integration"
    EMERGENCY_FALLBACK = "emergency_fallback"


class SynergyType(Enum):
    """相乗効果タイプ列挙"""

    PREDICTION_ENHANCEMENT = "prediction_enhancement"
    LEARNING_ACCELERATION = "learning_acceleration"
    EFFICIENCY_AMPLIFICATION = "efficiency_amplification"
    STABILITY_IMPROVEMENT = "stability_improvement"


@dataclass
class IntegrationMetrics:
    """統合メトリクス"""

    timestamp: float
    alpha_contribution: float
    beta_contribution: float
    synergy_factor: float
    total_efficiency: float
    deletion_rate: float
    integration_mode: IntegrationMode
    stability_score: float


@dataclass
class SynergyEffect:
    """相乗効果"""

    synergy_type: SynergyType
    magnitude: float
    confidence: float
    contributors: List[str]
    duration: float
    sustainability: float


class AlphaBetaCoordinator:
    """Alpha-Beta協調制御"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config

        # Alpha基盤参照
        self.alpha_system: Optional[BasicMLSystem] = None

        # Beta拡張参照
        self.prediction_engine: Optional[PredictionEngine] = None
        self.learning_system: Optional[LearningSystem] = None
        self.autonomous_controller: Optional[AutonomousController] = None

        # 協調状態
        self.coordination_active = False
        self.coordination_mode = IntegrationMode.ALPHA_ONLY

        # 協調履歴
        self.coordination_history: deque = deque(
            maxlen=config.get("history_size", 1000)
        )

        # 効果測定
        self.synergy_effects: Dict[SynergyType, List[SynergyEffect]] = defaultdict(list)

    def initialize_systems(
        self,
        alpha_system: BasicMLSystem,
        prediction_engine: Optional[PredictionEngine] = None,
        learning_system: Optional[LearningSystem] = None,
        autonomous_controller: Optional[AutonomousController] = None,
    ) -> None:
        """システム初期化"""
        try:
            # Alpha基盤設定
            self.alpha_system = alpha_system

            # Beta拡張設定
            if prediction_engine:
                self.prediction_engine = prediction_engine
            if learning_system:
                self.learning_system = learning_system
            if autonomous_controller:
                self.autonomous_controller = autonomous_controller

            # 統合モード判定
            self._determine_integration_mode()

            self.logger.info(
                f"Systems initialized with integration mode: {self.coordination_mode.value}"
            )

        except Exception as e:
            self.logger.error(f"Systems initialization failed: {e}")
            raise

    def _determine_integration_mode(self) -> None:
        """統合モード判定"""
        try:
            # 利用可能システム確認
            alpha_available = self.alpha_system is not None
            prediction_available = self.prediction_engine is not None
            learning_available = self.learning_system is not None
            autonomous_available = self.autonomous_controller is not None

            # Beta完全性チェック
            beta_complete = all(
                [prediction_available, learning_available, autonomous_available]
            )

            if alpha_available and beta_complete:
                self.coordination_mode = IntegrationMode.FULL_INTEGRATION
            elif alpha_available and (prediction_available or learning_available):
                self.coordination_mode = IntegrationMode.BETA_ENHANCED
            elif alpha_available:
                self.coordination_mode = IntegrationMode.ALPHA_ONLY
            else:
                self.coordination_mode = IntegrationMode.EMERGENCY_FALLBACK

        except Exception as e:
            self.logger.error(f"Integration mode determination failed: {e}")
            self.coordination_mode = IntegrationMode.EMERGENCY_FALLBACK

    def coordinate_optimization(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """協調最適化実行"""
        try:
            coordination_start = time.time()

            # Alpha基盤実行
            alpha_result = self._execute_alpha_optimization(context_data)

            # Beta拡張実行
            beta_result = self._execute_beta_optimization(context_data, alpha_result)

            # 統合最適化
            integrated_result = self._integrate_optimization_results(
                alpha_result, beta_result, context_data
            )

            # 相乗効果計算
            synergy_effects = self._calculate_synergy_effects(
                alpha_result, beta_result, integrated_result
            )

            coordination_time = time.time() - coordination_start

            # 結果構築
            final_result = {
                "coordination_success": True,
                "alpha_result": alpha_result,
                "beta_result": beta_result,
                "integrated_result": integrated_result,
                "synergy_effects": synergy_effects,
                "coordination_time": coordination_time,
                "integration_mode": self.coordination_mode.value,
            }

            # 履歴記録
            self._record_coordination_result(final_result)

            self.logger.debug(
                f"Coordination completed in {coordination_time:.3f}s "
                f"with mode {self.coordination_mode.value}"
            )
            return final_result
        except Exception as e:
            self.logger.error(f"Coordinate optimization failed: {e}")
            return self._get_fallback_coordination_result(context_data)

    def _execute_alpha_optimization(
        self, context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Alpha基盤最適化実行"""
        try:
            if not self.alpha_system:
                return {"success": False, "reason": "alpha_system_not_available"}

            # Alpha最適化実行（簡略化）
            optimization_result = getattr(
                self.alpha_system, "optimize", lambda: {"result": "default"}
            )()  # optimize属性安全呼び出し

            return {"success": True, "optimization_result": optimization_result}

        except Exception as e:
            self.logger.error(f"Alpha optimization execution failed: {e}")
            return {"success": False, "error": str(e)}

    def _execute_beta_optimization(
        self, context_data: Dict[str, Any], alpha_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Beta拡張最適化実行"""
        try:
            beta_results = {}

            # 予測エンジン実行
            if self.prediction_engine:
                prediction_result = self.prediction_engine.predict_next_operations(
                    context_data
                )
                beta_results["prediction"] = prediction_result

            # 学習システム実行（必要時）
            if self.learning_system and self._should_trigger_learning(alpha_result):
                learning_result = self._trigger_learning_system(
                    context_data, alpha_result
                )
                beta_results["learning"] = (
                    [learning_result]
                    if isinstance(learning_result, dict)
                    else learning_result
                )

            # 自律制御システム実行
            if self.autonomous_controller:
                control_result = self.autonomous_controller.monitor_system_efficiency()
                beta_results["autonomous"] = (
                    [control_result]
                    if isinstance(control_result, dict)
                    else control_result
                )

            # Beta統合効果計算
            beta_contribution = self._calculate_beta_contribution(beta_results)

            return {
                "success": len(beta_results) > 0,
                "results": beta_results,
                "contribution": beta_contribution,
                "systems_active": list(beta_results.keys()),
            }

        except Exception as e:
            self.logger.error(f"Beta optimization execution failed: {e}")
            return {"success": False, "error": str(e)}

    def _integrate_optimization_results(
        self,
        alpha_result: Dict[str, Any],
        beta_result: Dict[str, Any],
        context_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """最適化結果統合"""
        try:
            # Alpha貢献度
            alpha_contribution = alpha_result.get("contribution", 0.0)
            alpha_confidence = alpha_result.get("confidence", 0.0)

            # Beta貢献度
            beta_contribution = beta_result.get("contribution", 0.0)

            # 統合効果計算
            if self.coordination_mode == IntegrationMode.FULL_INTEGRATION:
                # 完全統合：相乗効果込み
                synergy_multiplier = self._calculate_synergy_multiplier(
                    alpha_result, beta_result
                )
                integrated_contribution = (
                    alpha_contribution + beta_contribution
                ) * synergy_multiplier
                integrated_confidence = (
                    alpha_confidence * 0.6 + 0.8 * 0.4
                ) * synergy_multiplier

            elif self.coordination_mode == IntegrationMode.BETA_ENHANCED:
                # Beta強化：加算的効果
                integrated_contribution = alpha_contribution + beta_contribution * 0.8
                integrated_confidence = alpha_confidence * 0.7 + 0.6 * 0.3

            else:
                # Alpha単独：基盤効果のみ
                integrated_contribution = alpha_contribution
                integrated_confidence = alpha_confidence

            # 効果上限制御
            integrated_contribution = min(5.0, max(0.0, integrated_contribution))
            integrated_confidence = min(1.0, max(0.0, integrated_confidence))

            return {
                "integrated_contribution": integrated_contribution,
                "integrated_confidence": integrated_confidence,
                "alpha_contribution": alpha_contribution,
                "beta_contribution": beta_contribution,
                "synergy_factor": self._calculate_current_synergy_factor(),
                "integration_effectiveness": self._calculate_integration_effectiveness(
                    alpha_result, beta_result
                ),
                "recommended_actions": self._generate_integrated_recommendations(
                    alpha_result, beta_result
                ),
            }

        except Exception as e:
            self.logger.error(f"Optimization results integration failed: {e}")
            return {
                "integrated_contribution": 0.0,
                "integrated_confidence": 0.0,
                "error": str(e),
            }

    def _calculate_synergy_effects(
        self,
        alpha_result: Dict[str, Any],
        beta_result: Dict[str, Any],
        integrated_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """相乗効果計算"""
        try:
            synergy_effects = {}

            # 予測強化相乗効果
            if beta_result.get("success", False) and "prediction" in beta_result.get(
                "results", {}
            ):
                prediction_synergy = self._calculate_prediction_synergy(
                    alpha_result, beta_result
                )
                synergy_effects[SynergyType.PREDICTION_ENHANCEMENT.value] = (
                    prediction_synergy
                )

            # 学習加速相乗効果
            if "learning" in beta_result.get("results", {}):
                learning_synergy = self._calculate_learning_synergy(
                    alpha_result, beta_result
                )
                synergy_effects[SynergyType.LEARNING_ACCELERATION.value] = (
                    learning_synergy
                )

            # 効率性増幅相乗効果
            efficiency_synergy = self._calculate_efficiency_synergy(
                alpha_result, beta_result, integrated_result
            )
            synergy_effects[SynergyType.EFFICIENCY_AMPLIFICATION.value] = (
                efficiency_synergy
            )

            # 安定性向上相乗効果
            if "autonomous" in beta_result.get("results", {}):
                stability_synergy = self._calculate_stability_synergy(beta_result)
                synergy_effects[SynergyType.STABILITY_IMPROVEMENT.value] = (
                    stability_synergy
                )

            # 総合相乗効果
            total_synergy_magnitude = sum(
                effect.get("magnitude", 0.0) for effect in synergy_effects.values()
            )

            return {
                "individual_effects": synergy_effects,
                "total_synergy_magnitude": total_synergy_magnitude,
                "synergy_count": len(synergy_effects),
                "dominant_synergy": (
                    max(
                        synergy_effects.items(),
                        key=lambda x: x[1].get("magnitude", 0.0),
                    )[0]
                    if synergy_effects
                    else None
                ),
            }

        except Exception as e:
            self.logger.error(f"Synergy effects calculation failed: {e}")
            return {"total_synergy_magnitude": 0.0, "synergy_count": 0}

    def _calculate_prediction_synergy(
        self, alpha_result: Dict[str, Any], beta_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """予測強化相乗効果計算"""
        try:
            alpha_confidence = alpha_result.get("confidence", 0.0)
            beta_prediction = beta_result.get("results", {}).get("prediction", {})
            beta_confidence = beta_prediction.get("prediction_confidence", 0.0)

            # 相乗効果計算
            prediction_synergy_magnitude = (alpha_confidence * beta_confidence) * 0.5

            return {
                "magnitude": prediction_synergy_magnitude,
                "confidence": min(alpha_confidence, beta_confidence),
                "contributors": ["alpha_predictions", "beta_prediction_engine"],
                "duration": 300.0,  # 5分間持続
                "sustainability": 0.8,
            }

        except Exception:
            return {"magnitude": 0.0, "confidence": 0.0}

    def _calculate_learning_synergy(
        self, alpha_result: Dict[str, Any], beta_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """学習加速相乗効果計算"""
        try:
            learning_result = beta_result.get("results", {}).get("learning", {})
            learning_effectiveness = learning_result.get(
                "learning_effectiveness", {}
            ).get("effectiveness_score", 0.0)

            alpha_contribution = alpha_result.get("contribution", 0.0)

            # 学習相乗効果
            learning_synergy_magnitude = (
                alpha_contribution * learning_effectiveness * 0.3
            )

            return {
                "magnitude": learning_synergy_magnitude,
                "confidence": learning_effectiveness,
                "contributors": ["alpha_training_data", "beta_learning_system"],
                "duration": 1800.0,  # 30分間持続
                "sustainability": 0.9,
            }

        except Exception:
            return {"magnitude": 0.0, "confidence": 0.0}

    def _calculate_efficiency_synergy(
        self,
        alpha_result: Dict[str, Any],
        beta_result: Dict[str, Any],
        integrated_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """効率性増幅相乗効果計算"""
        try:
            alpha_contribution = alpha_result.get("contribution", 0.0)
            beta_contribution = beta_result.get("contribution", 0.0)
            integrated_contribution = integrated_result.get(
                "integrated_contribution", 0.0
            )

            # 効率性相乗効果（統合効果 - 単純加算）
            efficiency_synergy_magnitude = max(
                0.0, integrated_contribution - (alpha_contribution + beta_contribution)
            )

            return {
                "magnitude": efficiency_synergy_magnitude,
                "confidence": integrated_result.get("integrated_confidence", 0.0),
                "contributors": ["alpha_beta_integration", "optimization_coordination"],
                "duration": 600.0,  # 10分間持続
                "sustainability": 0.7,
            }

        except Exception:
            return {"magnitude": 0.0, "confidence": 0.0}

    def _calculate_stability_synergy(
        self, beta_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """安定性向上相乗効果計算"""
        try:
            autonomous_result = beta_result.get("results", {}).get("autonomous", {})
            efficiency_assessment = autonomous_result.get("efficiency_assessment", {})
            overall_efficiency = efficiency_assessment.get("overall_efficiency", 0.0)

            # 安定性相乗効果
            stability_synergy_magnitude = overall_efficiency * 0.2

            return {
                "magnitude": stability_synergy_magnitude,
                "confidence": overall_efficiency,
                "contributors": ["autonomous_controller", "system_monitoring"],
                "duration": 3600.0,  # 1時間持続
                "sustainability": 0.95,
            }

        except Exception:
            return {"magnitude": 0.0, "confidence": 0.0}

    def _should_trigger_learning(self, alpha_result: Dict[str, Any]) -> bool:
        """学習トリガー判定"""
        try:
            # Alpha結果に基づく学習必要性判定
            alpha_confidence = alpha_result.get("confidence", 0.0)
            return bool(alpha_confidence < 0.8)  # 信頼度80%未満で学習トリガー
        except Exception:
            return False

    def _trigger_learning_system(
        self, context_data: Dict[str, Any], alpha_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """学習システムトリガー"""
        try:
            if not self.learning_system:
                return {"triggered": False, "reason": "learning_system_not_available"}

            # 学習システム実行（簡略化）
            learning_result = getattr(
                self.learning_system, "adapt_from_data", lambda x: {"adapted": False}
            )(
                context_data
            )  # adapt_from_data属性安全呼び出し

            return learning_result
        except Exception as e:
            self.logger.error(f"Learning system trigger failed: {e}")
            return {"triggered": False, "error": str(e)}

    def _calculate_beta_contribution(self, beta_results: Dict[str, Any]) -> float:
        """Beta貢献度計算"""
        try:
            total_contribution = 0.0

            # 予測エンジン貢献
            if "prediction" in beta_results:
                prediction_result = beta_results["prediction"]
                prediction_contribution = prediction_result.get(
                    "expected_efficiency_gain", 0.0
                )
                total_contribution += prediction_contribution * 0.5

            # 学習システム貢献
            if "learning" in beta_results:
                learning_result = beta_results["learning"]
                learning_effectiveness = learning_result.get(
                    "learning_effectiveness", {}
                ).get("effectiveness_score", 0.0)
                total_contribution += learning_effectiveness * 0.3

            # 自律制御貢献
            if "autonomous" in beta_results:
                autonomous_result = beta_results["autonomous"]
                efficiency_assessment = autonomous_result.get(
                    "efficiency_assessment", {}
                )
                efficiency_score = efficiency_assessment.get("overall_efficiency", 0.0)
                total_contribution += (efficiency_score - 0.8) * 0.2  # 80%以上で貢献

            return max(0.0, total_contribution)
        except Exception as e:
            self.logger.error(f"Beta contribution calculation failed: {e}")
            return 0.0

    def _calculate_synergy_multiplier(
        self, alpha_result: Dict[str, Any], beta_result: Dict[str, Any]
    ) -> float:
        """相乗効果倍率計算"""
        try:
            alpha_confidence = alpha_result.get("confidence", 0.0)
            beta_success = beta_result.get("success", False)
            beta_systems_count = len(beta_result.get("systems_active", []))

            # 基本倍率
            base_multiplier = 1.0

            # Alpha信頼度による増幅
            if alpha_confidence > 0.8:
                base_multiplier += 0.1

            # Beta完全性による増幅
            if beta_success and beta_systems_count >= 3:
                base_multiplier += 0.15
            elif beta_success and beta_systems_count >= 2:
                base_multiplier += 0.1
            elif beta_success:
                base_multiplier += 0.05

            return min(1.3, base_multiplier)  # 最大30%増幅
        except Exception as e:
            self.logger.error(f"Synergy multiplier calculation failed: {e}")
            return 1.0

    def _calculate_current_synergy_factor(self) -> float:
        """現在の相乗効果係数計算"""
        try:
            # 最近の相乗効果から計算
            recent_effects = []
            for synergy_type, effects in self.synergy_effects.items():
                recent_effects.extend(
                    [effect.magnitude for effect in effects[-5:]]
                )  # 最新5件

            if recent_effects:
                return float(np.mean(recent_effects))
            return 0.0
        except Exception as e:
            self.logger.error(f"Current synergy factor calculation failed: {e}")
            return 0.0

    def _calculate_integration_effectiveness(
        self, alpha_result: Dict[str, Any], beta_result: Dict[str, Any]
    ) -> float:
        """統合効果性計算"""
        try:
            alpha_success = alpha_result.get("success", False)
            beta_success = beta_result.get("success", False)

            if alpha_success and beta_success:
                return 0.9  # 両方成功
            elif alpha_success or beta_success:
                return 0.7  # いずれか成功
            else:
                return 0.3  # どちらも失敗
        except Exception as e:
            self.logger.error(f"Integration effectiveness calculation failed: {e}")
            return 0.0

    def _generate_integrated_recommendations(
        self, alpha_result: Dict[str, Any], beta_result: Dict[str, Any]
    ) -> List[str]:
        """統合推奨事項生成"""
        recommendations = []

        try:
            # Alpha推奨事項
            alpha_predictions = alpha_result.get("predictions", {})
            alpha_opportunities = alpha_predictions.get(
                "optimization_opportunities", []
            )
            recommendations.extend(alpha_opportunities[:3])  # 上位3つ

            # Beta推奨事項
            if beta_result.get("success", False):
                beta_results = beta_result.get("results", {})

                if "prediction" in beta_results:
                    prediction_ops = beta_results["prediction"].get(
                        "predicted_operations", []
                    )
                    recommendations.extend(prediction_ops[:2])  # 上位2つ

                if "autonomous" in beta_results:
                    recommendations.append("maintain_autonomous_monitoring")

            # 統合特有推奨事項
            if self.coordination_mode == IntegrationMode.FULL_INTEGRATION:
                recommendations.extend(
                    ["leverage_full_integration", "maximize_synergy_effects"]
                )

            # 重複除去
            return list(dict.fromkeys(recommendations))[:7]  # 最大7つ
        except Exception as e:
            self.logger.error(f"Integrated recommendations generation failed: {e}")
            return []

    def _record_coordination_result(self, result: Dict[str, Any]) -> None:
        """協調結果記録"""
        try:
            coordination_record = {
                "timestamp": time.time(),
                "integration_mode": self.coordination_mode.value,
                "coordination_success": result.get("coordination_success", False),
                "alpha_contribution": result.get("alpha_result", {}).get(
                    "contribution", 0.0
                ),
                "beta_contribution": result.get("beta_result", {}).get(
                    "contribution", 0.0
                ),
                "integrated_contribution": result.get("integrated_result", {}).get(
                    "integrated_contribution", 0.0
                ),
                "synergy_magnitude": result.get("synergy_effects", {}).get(
                    "total_synergy_magnitude", 0.0
                ),
                "coordination_time": result.get("coordination_time", 0.0),
            }

            self.coordination_history.append(coordination_record)

        except Exception as e:
            self.logger.warning(f"Coordination result recording failed: {e}")

    def _get_fallback_coordination_result(
        self, context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """フォールバック協調結果"""
        return {
            "coordination_success": False,
            "alpha_result": {"success": False, "contribution": 0.0},
            "beta_result": {"success": False, "contribution": 0.0},
            "integrated_result": {
                "integrated_contribution": 0.0,
                "integrated_confidence": 0.0,
            },
            "synergy_effects": {"total_synergy_magnitude": 0.0},
            "coordination_time": 0.0,
            "integration_mode": IntegrationMode.EMERGENCY_FALLBACK.value,
            "fallback": True,
        }
