"""
協調最適化ロジック

Phase B + AI協調最適化の実行管理
"""

import time
from typing import Any, Dict, cast

from kumihan_formatter.core.utilities.logger import get_logger

from .integration_data import CoordinatedResult


class OptimizationCoordinator:
    """最適化協調システム"""

    def __init__(self, integration_manager_ref: Any) -> None:
        """協調システム初期化"""
        self.logger = get_logger(__name__)
        self.manager = integration_manager_ref

    def coordinate_optimization(
        self, optimization_context: Dict[str, Any]
    ) -> CoordinatedResult:
        """Phase B + AI協調最適化"""
        with self.manager._coordination_lock:
            coordination_start = time.time()

            try:
                # 協調最適化実行
                coordinated_result = self._execute_coordinated_optimization(
                    optimization_context
                )

                # 相乗効果計算
                synergy_effect = self._calculate_synergy_effect(coordinated_result)

                # 統合結果構築
                final_result = CoordinatedResult(
                    phase_b_contribution=coordinated_result.get(
                        "phase_b_efficiency", 66.8
                    ),
                    ai_contribution=coordinated_result.get("ai_improvement", 0.0),
                    synergy_effect=synergy_effect,
                    total_improvement=coordinated_result.get("total_efficiency", 66.8),
                    integration_success=coordinated_result.get("success", False),
                    execution_time=time.time() - coordination_start,
                    coordination_quality=coordinated_result.get(
                        "coordination_quality", 0.0
                    ),
                )

                # 統計更新
                self.manager._update_coordination_metrics(final_result)

                self.logger.info(
                    f"Coordinated optimization completed: "
                    f"{final_result.total_improvement:.2f}% efficiency"
                )
                return final_result
            except Exception as e:
                self.logger.error(f"Coordinated optimization failed: {e}")
                return CoordinatedResult(
                    phase_b_contribution=66.8,
                    ai_contribution=0.0,
                    synergy_effect=0.0,
                    total_improvement=66.8,
                    integration_success=False,
                    execution_time=time.time() - coordination_start,
                    coordination_quality=0.0,
                )

    def _execute_coordinated_optimization(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """協調最適化実行"""
        try:
            # Phase B最適化実行
            phase_b_result = self._execute_phase_b_optimization(context)

            # AI最適化実行
            ai_result = self._execute_ai_optimization(context)

            # 結果統合
            merged_result = self._merge_optimization_results(
                phase_b_result, ai_result, context
            )

            # 協調品質評価
            coordination_quality = self._assess_coordination_quality(merged_result)

            # 最終結果構築
            final_result = {
                "phase_b_efficiency": phase_b_result.get("efficiency", 66.8),
                "ai_improvement": ai_result.get("improvement", 0.0),
                "total_efficiency": merged_result.get("total_efficiency", 66.8),
                "coordination_quality": coordination_quality,
                "success": merged_result.get("success", False),
                "metadata": {
                    "phase_b_metadata": phase_b_result.get("metadata", {}),
                    "ai_metadata": ai_result.get("metadata", {}),
                    "merge_metadata": merged_result.get("metadata", {}),
                },
            }

            return final_result
        except Exception as e:
            self.logger.error(f"Coordinated optimization execution failed: {e}")
            return {
                "phase_b_efficiency": 66.8,
                "ai_improvement": 0.0,
                "total_efficiency": 66.8,
                "coordination_quality": 0.0,
                "success": False,
                "error": str(e),
            }

    def _execute_phase_b_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase B最適化実行"""
        try:
            phase_b_start = time.time()

            # AdaptiveSettingsManager最適化
            settings_result = self.manager._adaptive_settings_manager.optimize_settings(
                context
            )

            # OptimizationIntegrator実行
            if (
                hasattr(self.manager, "_optimization_integrator")
                and self.manager._optimization_integrator
            ):
                integration_result = (
                    self.manager._optimization_integrator.execute_integration(
                        settings_result
                    )
                )
            else:
                integration_result = {"efficiency": 66.8, "success": True}

            # Phase B効果集約
            phase_b_efficiency = max(
                settings_result.get("efficiency", 66.8),
                integration_result.get("efficiency", 66.8),
            )

            execution_time = time.time() - phase_b_start

            return {
                "efficiency": phase_b_efficiency,
                "execution_time": execution_time,
                "success": True,
                "metadata": {
                    "settings_result": settings_result,
                    "integration_result": integration_result,
                    "optimization_context": context,
                },
            }
        except Exception as e:
            self.logger.error(f"Phase B optimization failed: {e}")
            return {
                "efficiency": 66.8,  # フォールバック値
                "execution_time": 0.0,
                "success": False,
                "error": str(e),
            }

    def _execute_ai_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI最適化実行"""
        try:
            ai_start = time.time()

            # BasicMLSystem予測
            if (
                hasattr(self.manager, "_basic_ml_system")
                and self.manager._basic_ml_system
            ):
                ml_prediction = self.manager._basic_ml_system.predict_token_efficiency(
                    context
                )
                ai_improvement = ml_prediction.efficiency_prediction
            else:
                ai_improvement = 0.0

            # AI最適化実行（追加の最適化があれば）
            optimization_improvement = 0.0  # 現時点では基本実装

            total_ai_improvement = ai_improvement + optimization_improvement
            execution_time = time.time() - ai_start

            return {
                "improvement": total_ai_improvement,
                "execution_time": execution_time,
                "success": total_ai_improvement > 0.0,
                "metadata": {
                    "ml_prediction": ai_improvement,
                    "optimization_improvement": optimization_improvement,
                    "prediction_confidence": 0.8,  # デフォルト信頼度
                },
            }
        except Exception as e:
            self.logger.error(f"AI optimization failed: {e}")
            return {
                "improvement": 0.0,  # フォールバック値
                "execution_time": 0.0,
                "success": False,
                "error": str(e),
            }

    def _merge_optimization_results(
        self,
        phase_b_result: Dict[str, Any],
        ai_result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """最適化結果統合"""
        try:
            # 基本効果抽出
            phase_b_efficiency = phase_b_result.get("efficiency", 66.8)
            ai_improvement = ai_result.get("improvement", 0.0)

            # 相乗効果計算（Phase B基盤とAIの相互作用）
            synergy_factor = self._calculate_synergy_factor(
                phase_b_efficiency, ai_improvement, context
            )

            # 総合効果計算
            total_efficiency = phase_b_efficiency + ai_improvement * synergy_factor

            # 成功判定
            success = (
                phase_b_result.get("success", False)
                and ai_result.get("success", False)
                and total_efficiency >= 66.8  # Phase B基盤維持
            )

            return {
                "total_efficiency": total_efficiency,
                "synergy_factor": synergy_factor,
                "success": success,
                "metadata": {
                    "phase_b_efficiency": phase_b_efficiency,
                    "ai_improvement": ai_improvement,
                    "synergy_calculation": {
                        "factor": synergy_factor,
                        "base_efficiency": phase_b_efficiency,
                        "ai_contribution": ai_improvement,
                    },
                },
            }
        except Exception as e:
            self.logger.error(f"Optimization result merge failed: {e}")
            return {
                "total_efficiency": 66.8,  # 安全なフォールバック
                "synergy_factor": 1.0,
                "success": False,
                "error": str(e),
            }

    def _assess_coordination_quality(self, merged_result: Dict[str, Any]) -> float:
        """協調品質評価"""
        try:
            # 品質要素評価
            efficiency_quality = min(
                1.0, merged_result.get("total_efficiency", 66.8) / 68.8
            )
            synergy_quality = min(1.0, merged_result.get("synergy_factor", 1.0))
            success_quality = 1.0 if merged_result.get("success", False) else 0.0

            # 重み付け品質スコア
            coordination_quality = (
                efficiency_quality * 0.5 + synergy_quality * 0.3 + success_quality * 0.2
            )

            return cast(float, max(0.0, min(1.0, coordination_quality)))
        except Exception as e:
            self.logger.error(f"Coordination quality assessment failed: {e}")
            return 0.5  # 中性的品質スコア

    def _calculate_synergy_effect(self, coordinated_result: Dict[str, Any]) -> float:
        """相乗効果計算"""
        try:
            phase_b_efficiency = coordinated_result.get("phase_b_efficiency", 66.8)
            ai_improvement = coordinated_result.get("ai_improvement", 0.0)
            total_efficiency = coordinated_result.get("total_efficiency", 66.8)

            # 単純加算との差分（相乗効果）
            expected_sum = phase_b_efficiency + ai_improvement
            actual_synergy = total_efficiency - expected_sum

            return cast(float, max(0.0, actual_synergy))  # 負の相乗効果は0とする
        except Exception as e:
            self.logger.error(f"Synergy effect calculation failed: {e}")
            return 0.0

    def _calculate_synergy_factor(
        self, phase_b_efficiency: float, ai_improvement: float, context: Dict[str, Any]
    ) -> float:
        """相乗効果係数計算"""
        try:
            # 基本相乗効果係数
            base_synergy = 1.0

            # Phase B基盤強度による相乗効果増強
            if phase_b_efficiency > 66.8:
                efficiency_bonus = (phase_b_efficiency - 66.8) * 0.1
                base_synergy += efficiency_bonus

            # AI改善度による相乗効果
            if ai_improvement > 0:
                ai_bonus = min(0.2, ai_improvement * 0.05)  # 最大20%のボーナス
                base_synergy += ai_bonus

            # コンテキスト要因による調整
            context_factor = context.get("synergy_context", 1.0)
            final_synergy = base_synergy * context_factor

            return cast(float, max(0.5, min(2.0, final_synergy)))  # 0.5-2.0の範囲に制限
        except Exception as e:
            self.logger.error(f"Synergy factor calculation failed: {e}")
            return 1.0  # 中性的係数
