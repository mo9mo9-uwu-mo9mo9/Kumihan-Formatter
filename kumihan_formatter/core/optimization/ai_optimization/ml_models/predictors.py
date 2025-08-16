"""
ML Models Predictors - 予測モデル群

Token効率性予測、使用パターン分類、最適化推奨システム
"""

import time
from typing import TYPE_CHECKING

import numpy as np

from .base import BaseMLModel, PredictionResponse, TrainingData

if TYPE_CHECKING:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


class TokenEfficiencyPredictor(BaseMLModel):
    """Token効率性予測モデル"""

    def create_model(self) -> "RandomForestRegressor":
        """RandomForest回帰モデル作成"""
        from sklearn.ensemble import RandomForestRegressor

        return RandomForestRegressor(
            n_estimators=self.config.get("n_estimators", 50),
            max_depth=self.config.get("max_depth", 10),
            random_state=42,
            n_jobs=-1,
        )

    def train(self, data: TrainingData) -> bool:
        """Token効率性予測モデル訓練"""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import StandardScaler

            training_start = time.time()

            # モデル・スケーラー初期化
            self.model = self.create_model()
            self.scaler = StandardScaler()

            # 特徴量正規化
            X_scaled = self.scaler.fit_transform(data.features)

            # 学習実行
            self.model.fit(X_scaled, data.targets)

            # 性能評価
            cv_scores = cross_val_score(
                self.model, X_scaled, data.targets, cv=5, scoring="r2"
            )

            # 性能記録
            training_time = time.time() - training_start
            self.performance_metrics = {
                "r2_score": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "training_time": training_time,
                "feature_count": data.features.shape[1],
                "sample_count": data.features.shape[0],
            }

            self.feature_names = data.feature_names
            self.is_trained = True

            self.logger.info(
                f"Token efficiency predictor trained: "
                f"R²={cv_scores.mean():.3f}±{cv_scores.std():.3f}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Token efficiency training failed: {e}")
            return False

    def predict(self, features: np.ndarray) -> PredictionResponse:
        """Token効率性予測"""
        # 前提条件確認
        if not self.is_trained:
            return PredictionResponse(
                prediction=0.0, confidence=0.0, processing_time=0.0
            )

        try:
            prediction_start = time.time()

            # 特徴量正規化
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # 予測実行
            prediction = self.model.predict(features_scaled)[0]

            # 信頼度計算
            if hasattr(self.model, "estimators_"):
                # Random Forestの場合、各木の予測分散から信頼度計算
                tree_predictions = [
                    tree.predict(features_scaled)[0] for tree in self.model.estimators_
                ]
                confidence = 1.0 - (
                    np.std(tree_predictions) / max(np.mean(tree_predictions), 0.1)
                )
                confidence = max(0.0, min(1.0, confidence))
            else:
                confidence = 0.8  # デフォルト信頼度

            # 特徴量重要度
            feature_importance = None
            if hasattr(self.model, "feature_importances_") and self.feature_names:
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )

            processing_time = time.time() - prediction_start

            return PredictionResponse(
                prediction=float(prediction),
                confidence=confidence,
                feature_importance=feature_importance,
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Token efficiency prediction failed: {e}")
            return PredictionResponse(
                prediction=0.0, confidence=0.0, processing_time=0.0
            )


class UsagePatternClassifier(BaseMLModel):
    """使用パターン分類モデル"""

    def create_model(self) -> "RandomForestClassifier":
        """RandomForest分類モデル作成"""
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=self.config.get("n_estimators", 30),
            max_depth=self.config.get("max_depth", 8),
            random_state=42,
            n_jobs=-1,
        )

    def train(self, data: TrainingData) -> bool:
        """使用パターン分類モデル訓練"""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import LabelEncoder, StandardScaler

            training_start = time.time()

            # モデル・スケーラー・エンコーダー初期化
            self.model = self.create_model()
            self.scaler = StandardScaler()
            self.label_encoder = LabelEncoder()

            # 特徴量正規化
            X_scaled = self.scaler.fit_transform(data.features)

            # ラベルエンコーディング
            y_encoded = self.label_encoder.fit_transform(data.targets)

            # 学習実行
            self.model.fit(X_scaled, y_encoded)

            # 性能評価
            cv_scores = cross_val_score(
                self.model, X_scaled, y_encoded, cv=5, scoring="accuracy"
            )

            # 性能記録
            training_time = time.time() - training_start
            self.performance_metrics = {
                "accuracy": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "training_time": training_time,
                "feature_count": data.features.shape[1],
                "sample_count": data.features.shape[0],
                "class_count": len(self.label_encoder.classes_),
            }

            self.feature_names = data.feature_names
            self.is_trained = True

            self.logger.info(
                f"Usage pattern classifier trained: "
                f"Accuracy={cv_scores.mean():.3f}±{cv_scores.std():.3f}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Usage pattern training failed: {e}")
            return False

    def predict(self, features: np.ndarray) -> PredictionResponse:
        """使用パターン分類予測"""
        # 前提条件確認
        if not self.is_trained:
            return PredictionResponse(
                prediction="unknown", confidence=0.0, processing_time=0.0
            )

        try:
            prediction_start = time.time()

            # 特徴量正規化
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # 予測実行
            prediction_encoded = self.model.predict(features_scaled)[0]
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]

            # 予測確率・信頼度
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = float(np.max(probabilities))

            # 特徴量重要度
            feature_importance = None
            if hasattr(self.model, "feature_importances_") and self.feature_names:
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )

            processing_time = time.time() - prediction_start

            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                probabilities=probabilities,
                feature_importance=feature_importance,
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Usage pattern prediction failed: {e}")
            return PredictionResponse(
                prediction="unknown", confidence=0.0, processing_time=0.0
            )


class OptimizationRecommender(BaseMLModel):
    """最適化推奨システム"""

    def create_model(self) -> "RandomForestClassifier":
        """最適化推奨分類モデル作成"""
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=self.config.get("n_estimators", 40),
            max_depth=self.config.get("max_depth", 12),
            random_state=42,
            n_jobs=-1,
        )

    def train(self, data: TrainingData) -> bool:
        """最適化推奨モデル訓練"""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import LabelEncoder, StandardScaler

            training_start = time.time()

            # モデル・前処理器初期化
            self.model = self.create_model()
            self.scaler = StandardScaler()
            self.label_encoder = LabelEncoder()

            # データ前処理
            X_scaled = self.scaler.fit_transform(data.features)
            y_encoded = self.label_encoder.fit_transform(data.targets)

            # 学習実行
            self.model.fit(X_scaled, y_encoded)

            # 性能評価
            cv_scores = cross_val_score(
                self.model, X_scaled, y_encoded, cv=5, scoring="accuracy"
            )

            # 性能記録
            training_time = time.time() - training_start
            self.performance_metrics = {
                "accuracy": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "training_time": training_time,
                "feature_count": data.features.shape[1],
                "sample_count": data.features.shape[0],
                "optimization_types": len(self.label_encoder.classes_),
            }

            self.feature_names = data.feature_names
            self.is_trained = True

            self.logger.info(
                f"Optimization recommender trained: "
                f"Accuracy={cv_scores.mean():.3f}±{cv_scores.std():.3f}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Optimization recommender training failed: {e}")
            return False

    def predict(self, features: np.ndarray) -> PredictionResponse:
        """最適化推奨予測"""
        if not self.is_trained:
            return PredictionResponse(
                prediction="basic_optimization", confidence=0.0, processing_time=0.0
            )

        try:
            prediction_start = time.time()

            # 特徴量正規化
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # 予測実行
            prediction_encoded = self.model.predict(features_scaled)[0]
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]

            # 予測確率・信頼度
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = float(np.max(probabilities))

            # 特徴量重要度
            feature_importance = None
            if hasattr(self.model, "feature_importances_") and self.feature_names:
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )

            processing_time = time.time() - prediction_start

            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                probabilities=probabilities,
                feature_importance=feature_importance,
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Optimization recommender prediction failed: {e}")
            return PredictionResponse(
                prediction="basic_optimization", confidence=0.0, processing_time=0.0
            )
