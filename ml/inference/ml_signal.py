"""
ML Signal Adapter — Safe wrapper for risk engine integration.

This module provides a single entry point for the Central Risk Engine
to obtain an ML behavioral classification signal.

SAFETY GUARANTEES:
    - Never raises exceptions (catches all errors internally)
    - Returns None on any failure (ML unavailable = rule-only fallback)
    - Never performs protective actions (no kill, block, delete, quarantine)
    - Never modifies files, processes, or network state
    - Does not bypass DRY_RUN or containment gates

USAGE (by core/risk_engine.py):
    from ml.inference.ml_signal import get_ml_signal_safe
    
    ml_signal = get_ml_signal_safe(features_dict)
    # Returns structured dict on success, None on any failure
"""


def get_ml_signal_safe(feature_extractor_output):
    """
    Safely obtain ML prediction from feature extractor output.
    
    This is the ONLY function the risk engine should call.
    It wraps all ML inference in a try/except to guarantee
    that ML failures never crash or degrade the risk engine.
    
    Args:
        feature_extractor_output: dict — the 12-feature dict from
            core/feature_extractor.extract_features()
            
    Returns:
        dict on success:
            {
                "status": "success",
                "prediction": int (0 or 1),
                "label": str ("NORMAL" or "RANSOMWARE_LIKE"),
                "probability": float (0.0 to 1.0),
                "above_threshold": bool,
                "threshold": float,
                "model_version": str,
                "feature_version": str,
                "important_features": list,
                "inference_time_ms": float,
            }
            
        None on any failure:
            - ML module not installed
            - Model artifacts missing
            - sklearn not installed
            - Feature validation error
            - Model prediction error
            - Any unexpected exception
            
    When None is returned, the risk engine should continue
    with rule-only severity determination (existing behavior).
    """
    try:
        from ml.inference.integration import get_ml_prediction
        result = get_ml_prediction(feature_extractor_output)
        
        if result.get("status") == "success":
            return result
        
        # ML returned an error status — treat as unavailable
        return None
        
    except Exception:
        # Any failure at all — ML is unavailable
        # Risk engine continues with rule-only behavior
        return None


def is_ml_available():
    """
    Check if the ML module is loaded and ready for inference.
    Safe to call at any time — never raises.
    
    Returns:
        True if ML is ready, False otherwise.
    """
    try:
        from ml.inference.integration import is_ml_ready
        return is_ml_ready()
    except Exception:
        return False
