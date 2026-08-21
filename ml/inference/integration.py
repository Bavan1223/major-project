"""
Core Integration Adapter — Bridges feature extractor output to ML inference.

This adapter:
    1. Receives the 12-feature dict from core/feature_extractor.extract_features()
    2. Selects the 10 ML features (excludes file_events, suspicious_indicators)
    3. Calls the ML predictor
    4. Returns a structured ML signal for the Central Risk Engine

ARCHITECTURE POSITION:
    core/feature_extractor.extract_features()
        ↓ (12 features)
    integration.get_ml_prediction()
        ↓ (selects 10, validates, predicts)
    ML Result
        ↓
    Central Risk Engine (combines with rule signals)

This module does NOT:
    - Modify core feature extraction
    - Make final risk decisions
    - Take protective action
    - Replace the rule-based detection

USAGE:
    from ml.inference.integration import get_ml_prediction, MLIntegration
    
    # Simple function interface:
    features_from_extractor = extract_features(events)
    ml_result = get_ml_prediction(features_from_extractor)
    
    # Or class-based interface:
    ml = MLIntegration()
    ml_result = ml.predict(features_from_extractor)
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import ML_FEATURE_COLUMNS, EXCLUDED_FEATURES
from ml.inference.predictor import (
    RansomwarePredictor,
    ModelNotLoadedError,
    FeatureValidationError,
)


class MLIntegration:
    """
    Integration adapter between core feature extractor and ML inference.
    
    Handles the mapping from 12-feature extractor output to 10-feature ML input.
    """

    def __init__(self, model_dir=None, auto_load=True):
        """
        Initialize the integration adapter.
        
        Args:
            model_dir: Path to model artifacts directory
            auto_load: Load model immediately
        """
        self.predictor = RansomwarePredictor(model_dir=model_dir, auto_load=auto_load)

    @property
    def is_ready(self):
        """Check if the ML module is ready for inference."""
        return self.predictor.is_loaded

    def predict(self, extractor_output):
        """
        Process feature extractor output and return ML prediction.
        
        Args:
            extractor_output: dict — the 12-feature dict from
                              core/feature_extractor.extract_features()
                              
        Returns:
            dict: ML prediction result, or error dict if prediction fails.
            
            Success:
            {
                "status": "success",
                "prediction": 0 or 1,
                "label": "NORMAL" or "RANSOMWARE_LIKE",
                "probability": float,
                "above_threshold": bool,
                "threshold": float,
                "model_version": str,
                "feature_version": str,
                "important_features": [...],
                "inference_time_ms": float,
            }
            
            Error:
            {
                "status": "error",
                "error_type": str,
                "error_message": str,
                "prediction": None,
                "label": None,
                "probability": None,
            }
        """
        try:
            # Select only the 10 ML features from the 12-feature extractor output
            ml_features = self._select_ml_features(extractor_output)

            # Run inference
            result = self.predictor.predict(ml_features)
            result["status"] = "success"
            return result

        except FeatureValidationError as e:
            return {
                "status": "error",
                "error_type": "feature_validation",
                "error_message": str(e),
                "prediction": None,
                "label": None,
                "probability": None,
            }
        except ModelNotLoadedError as e:
            return {
                "status": "error",
                "error_type": "model_not_loaded",
                "error_message": str(e),
                "prediction": None,
                "label": None,
                "probability": None,
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "unexpected",
                "error_message": str(e),
                "prediction": None,
                "label": None,
                "probability": None,
            }

    def _select_ml_features(self, extractor_output):
        """
        Select the 10 ML features from the 12-feature extractor output.
        Explicitly excludes file_events and suspicious_indicators.
        
        Args:
            extractor_output: dict with 12 feature keys
            
        Returns:
            dict with 10 ML feature keys
            
        Raises:
            FeatureValidationError: If required features are missing
        """
        if not isinstance(extractor_output, dict):
            raise FeatureValidationError(
                f"Expected dict from feature extractor, got {type(extractor_output)}"
            )

        # Check that required ML features are present
        missing = [col for col in ML_FEATURE_COLUMNS if col not in extractor_output]
        if missing:
            raise FeatureValidationError(
                f"Feature extractor output missing required ML features: {missing}"
            )

        # Select only ML features (exclude file_events, suspicious_indicators)
        ml_features = {col: extractor_output[col] for col in ML_FEATURE_COLUMNS}
        return ml_features

    def get_status(self):
        """Return the current status of the ML integration."""
        return {
            "ready": self.is_ready,
            "model_info": self.predictor.get_model_info() if self.is_ready else None,
        }


# =============================================================================
# SIMPLE FUNCTION INTERFACE
# =============================================================================

# Module-level singleton predictor (lazy-loaded)
_predictor_instance = None


def get_ml_prediction(extractor_output):
    """
    Simple function interface for ML prediction.
    
    Accepts the 12-feature dict from core/feature_extractor.extract_features()
    and returns a structured ML result.
    
    The predictor is loaded once on first call and reused thereafter.
    
    Args:
        extractor_output: dict from feature_extractor.extract_features()
        
    Returns:
        dict: ML prediction result (see MLIntegration.predict())
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MLIntegration(auto_load=True)
    return _predictor_instance.predict(extractor_output)


def is_ml_ready():
    """Check if the ML module is loaded and ready."""
    global _predictor_instance
    if _predictor_instance is None:
        try:
            _predictor_instance = MLIntegration(auto_load=True)
        except Exception:
            return False
    return _predictor_instance.is_ready
