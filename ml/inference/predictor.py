"""
ML Inference Predictor — Ransomware Behavioral Detection.

Provides structured prediction output for the Central Risk Engine.
Loads the trained model and preprocessor, validates input features,
and returns a prediction with probability and explainability.

This module does NOT:
    - Kill processes
    - Block network connections
    - Delete or quarantine files
    - Make final severity decisions
    - Retrain the model

It ONLY produces a behavioral classification signal.

USAGE:
    from ml.inference.predictor import RansomwarePredictor

    predictor = RansomwarePredictor()
    result = predictor.predict(feature_dict)

    # result = {
    #     "prediction": 0 or 1,
    #     "label": "NORMAL" or "RANSOMWARE_LIKE",
    #     "probability": float,
    #     "above_threshold": bool,
    #     "threshold": float,
    #     "model_version": str,
    #     "feature_version": str,
    #     "important_features": [...],
    # }
"""

import os
import sys
import json
import time
import numpy as np

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import (
    FEATURE_VERSION,
    ML_FEATURE_COLUMNS,
    LABEL_MAP,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
    MODEL_DIR,
    MODEL_FILENAME,
    PREPROCESSOR_FILENAME,
    DEFAULT_SCORE_THRESHOLD,
)


class PredictorError(Exception):
    """Base exception for predictor errors."""
    pass


class ModelNotLoadedError(PredictorError):
    """Model artifacts not loaded."""
    pass


class FeatureValidationError(PredictorError):
    """Input features failed validation."""
    pass


class RansomwarePredictor:
    """
    ML predictor for ransomware-like behavioral detection.
    
    Loads the trained model and preprocessor, validates input features,
    and returns structured prediction results.
    """

    def __init__(self, model_dir=None, auto_load=True):
        """
        Initialize the predictor.
        
        Args:
            model_dir: Directory containing model artifacts.
                       Defaults to ml/models/
            auto_load: If True, load model on initialization.
        """
        self.model_dir = model_dir or os.path.join(ML_ROOT, MODEL_DIR)
        self.model = None
        self.preprocessor = None
        self.metadata = None
        self.threshold = DEFAULT_SCORE_THRESHOLD
        self._loaded = False

        if auto_load:
            self.load()

    def load(self):
        """
        Load model, preprocessor, and metadata from disk.
        
        Raises:
            ModelNotLoadedError: If artifacts are missing or corrupted.
        """
        import joblib

        model_path = os.path.join(self.model_dir, MODEL_FILENAME)
        preprocessor_path = os.path.join(self.model_dir, PREPROCESSOR_FILENAME)
        metadata_path = os.path.join(self.model_dir, "model_metadata.json")

        # Check files exist
        if not os.path.isfile(model_path):
            raise ModelNotLoadedError(
                f"Model file not found: {model_path}"
            )
        if not os.path.isfile(preprocessor_path):
            raise ModelNotLoadedError(
                f"Preprocessor file not found: {preprocessor_path}"
            )

        # Load model
        try:
            self.model = joblib.load(model_path)
        except Exception as e:
            raise ModelNotLoadedError(f"Failed to load model: {e}")

        # Load preprocessor
        try:
            self.preprocessor = joblib.load(preprocessor_path)
        except Exception as e:
            raise ModelNotLoadedError(f"Failed to load preprocessor: {e}")

        # Load metadata (optional but expected)
        if os.path.isfile(metadata_path):
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
            # Use threshold from metadata if available
            if "threshold" in self.metadata:
                self.threshold = self.metadata["threshold"]

        self._loaded = True

    @property
    def is_loaded(self):
        """Check if model is loaded and ready for inference."""
        return self._loaded and self.model is not None and self.preprocessor is not None

    @property
    def model_version(self):
        """Get the model version string."""
        if self.metadata:
            return self.metadata.get("model_version", "unknown")
        return "unknown"

    @property
    def feature_version(self):
        """Get the feature version this model expects."""
        return FEATURE_VERSION

    def validate_features(self, features):
        """
        Validate a feature input dictionary or list.
        
        Args:
            features: dict with feature names as keys, or list/array of 10 values
            
        Returns:
            numpy array of shape (1, 10) ready for prediction
            
        Raises:
            FeatureValidationError: If features are invalid
        """
        if not self.is_loaded:
            raise ModelNotLoadedError("Model not loaded. Call load() first.")

        # Accept dict or list/array
        if isinstance(features, dict):
            # Validate all required features are present
            missing = [col for col in ML_FEATURE_COLUMNS if col not in features]
            if missing:
                raise FeatureValidationError(
                    f"Missing required features: {missing}"
                )

            # Check for excluded features being passed (warn but don't fail)
            # The predictor simply ignores them
            
            # Extract in correct order
            values = [features[col] for col in ML_FEATURE_COLUMNS]

        elif isinstance(features, (list, tuple, np.ndarray)):
            values = list(features)
            if len(values) != len(ML_FEATURE_COLUMNS):
                raise FeatureValidationError(
                    f"Expected {len(ML_FEATURE_COLUMNS)} features, got {len(values)}. "
                    f"Required features (in order): {list(ML_FEATURE_COLUMNS)}"
                )
        else:
            raise FeatureValidationError(
                f"Features must be a dict, list, or numpy array. Got: {type(features)}"
            )

        # Validate values
        for i, (col, val) in enumerate(zip(ML_FEATURE_COLUMNS, values)):
            if val is None:
                raise FeatureValidationError(
                    f"Feature '{col}' is None (missing value not allowed)"
                )
            try:
                numeric_val = float(val)
            except (TypeError, ValueError):
                raise FeatureValidationError(
                    f"Feature '{col}' has non-numeric value: {val}"
                )
            if numeric_val < 0:
                raise FeatureValidationError(
                    f"Feature '{col}' has negative value: {val} (all features must be >= 0)"
                )
            values[i] = numeric_val

        return np.array(values).reshape(1, -1)

    def predict(self, features):
        """
        Generate a structured prediction from behavioral features.
        
        Args:
            features: dict with 10 ML feature names as keys and integer counts as values,
                      OR a list/array of 10 values in ML_FEATURE_COLUMNS order.
                      
        Returns:
            dict: Structured prediction result:
                {
                    "prediction": int (0 or 1),
                    "label": str ("NORMAL" or "RANSOMWARE_LIKE"),
                    "probability": float (model's estimated probability of RANSOMWARE_LIKE),
                    "above_threshold": bool (probability >= threshold),
                    "threshold": float (configured decision threshold),
                    "model_version": str,
                    "feature_version": str,
                    "important_features": list (top contributing features),
                }
                
        Raises:
            ModelNotLoadedError: If model is not loaded
            FeatureValidationError: If features are invalid
        """
        if not self.is_loaded:
            raise ModelNotLoadedError("Model not loaded. Call load() first.")

        # Validate and extract feature vector
        X = self.validate_features(features)

        # Preprocess (apply same scaler used during training)
        X_scaled = self.preprocessor.transform(X)

        # Predict
        start_time = time.perf_counter()
        prediction = int(self.model.predict(X_scaled)[0])
        
        # Get probability
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(X_scaled)[0]
            prob_ransomware = float(probabilities[1])
        else:
            prob_ransomware = float(prediction)

        inference_time_ms = (time.perf_counter() - start_time) * 1000

        # Apply threshold
        above_threshold = prob_ransomware >= self.threshold

        # Get feature importance for this prediction
        important_features = self._get_prediction_explanation(X[0])

        # Build result
        result = {
            "prediction": prediction,
            "label": LABEL_MAP[prediction],
            "probability": round(prob_ransomware, 4),
            "above_threshold": above_threshold,
            "threshold": self.threshold,
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "important_features": important_features,
            "inference_time_ms": round(inference_time_ms, 3),
        }

        return result

    def predict_batch(self, feature_list):
        """
        Predict on multiple feature vectors.
        
        Args:
            feature_list: List of feature dicts or arrays
            
        Returns:
            list of prediction result dicts
        """
        return [self.predict(f) for f in feature_list]

    def _get_prediction_explanation(self, feature_values):
        """
        Generate feature-level explanation for a prediction.
        
        For Logistic Regression: uses coefficient magnitudes weighted by feature values.
        For tree-based models: uses feature_importances_ weighted by feature values.
        Shows which features contributed most to THIS specific prediction.
        """
        if hasattr(self.model, "coef_"):
            # Linear model: contribution = coefficient * scaled_value
            coefficients = self.model.coef_[0]
            scaled_values = (feature_values - self.preprocessor.mean_) / self.preprocessor.scale_
            contributions = coefficients * scaled_values
        elif hasattr(self.model, "feature_importances_"):
            # Tree-based model: approximate contribution = importance * (scaled_value sign)
            importances = self.model.feature_importances_
            scaled_values = (feature_values - self.preprocessor.mean_) / self.preprocessor.scale_
            # For tree models, contribution direction approximated by whether value is above/below mean
            contributions = importances * scaled_values
        else:
            return []

        # Build explanation
        explanation = []
        for i, (name, contrib, raw_val) in enumerate(
            zip(ML_FEATURE_COLUMNS, contributions, feature_values)
        ):
            explanation.append({
                "feature": name,
                "value": int(raw_val),
                "contribution": round(float(contrib), 4),
                "direction": "ransomware" if contrib > 0 else "normal",
            })

        # Sort by absolute contribution (most impactful first)
        explanation.sort(key=lambda x: abs(x["contribution"]), reverse=True)

        # Return top 5 contributing features
        return explanation[:5]

    def get_model_info(self):
        """Return model metadata for inspection."""
        return {
            "loaded": self.is_loaded,
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "threshold": self.threshold,
            "algorithm": type(self.model).__name__ if self.model else None,
            "feature_columns": list(ML_FEATURE_COLUMNS),
            "feature_count": len(ML_FEATURE_COLUMNS),
            "limitations": [
                "Baseline model trained on 76-sample controlled dataset",
                "NOT production-ready — requires Ubuntu lab retraining",
                "Probability is not calibrated — do not interpret as true probability",
            ],
        }
