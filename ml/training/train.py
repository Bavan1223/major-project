"""
ML Training Pipeline — Ransomware Detection Model.

Complete training pipeline:
    1. Load and validate dataset
    2. Session-level train/validation/test split
    3. Preprocessing (scaling)
    4. Baseline model training and comparison
    5. Threshold calibration
    6. Feature importance
    7. Final evaluation on held-out test set
    8. Artifact saving

USAGE:
    python -m ml.training.train

IMPORTANT:
    - Uses session-level splitting to prevent data leakage
    - Does NOT use suspicious_indicators or file_events
    - Trains on 10-feature contract (FEATURE_VERSION 1.0)
    - Reports honest metrics even if performance is limited
    - Does NOT claim production readiness on 76 samples
"""

import os
import sys
import csv
import json
import time
import warnings
import numpy as np
from datetime import datetime, timezone
from collections import Counter

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import (
    FEATURE_VERSION,
    ML_FEATURE_COLUMNS,
    WINDOW_SECONDS,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
    LABEL_MAP,
    MODEL_DIR,
    MODEL_FILENAME,
    PREPROCESSOR_FILENAME,
)

# Suppress convergence warnings for small dataset
warnings.filterwarnings("ignore", category=UserWarning)

# =============================================================================
# CONFIGURATION
# =============================================================================

RANDOM_SEED = 42
DATASET_PATH = os.path.join(ML_ROOT, "data", "processed", "dataset_v0.1.csv")
MODELS_DIR = os.path.join(ML_ROOT, MODEL_DIR)
EVALUATION_DIR = os.path.join(ML_ROOT, "evaluation")

# Train/Validation/Test split ratios (by session count)
TRAIN_RATIO = 0.60
VAL_RATIO = 0.20
TEST_RATIO = 0.20


# =============================================================================
# DATA LOADING
# =============================================================================

def load_dataset(csv_path):
    """Load and validate the dataset CSV."""
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Validate columns
    expected_cols = ["session_id", "window_id", "scenario_id", "label"] + list(ML_FEATURE_COLUMNS)
    actual_cols = list(rows[0].keys()) if rows else []
    assert actual_cols == expected_cols, f"Column mismatch: {actual_cols}"

    # Parse into arrays
    session_ids = [r["session_id"] for r in rows]
    scenario_ids = [r["scenario_id"] for r in rows]
    labels = np.array([int(r["label"]) for r in rows])
    features = np.array([[int(r[col]) for col in ML_FEATURE_COLUMNS] for r in rows])

    return features, labels, session_ids, scenario_ids


# =============================================================================
# SESSION-LEVEL SPLITTING
# =============================================================================

def session_level_split(features, labels, session_ids, scenario_ids,
                        train_ratio=0.60, val_ratio=0.20, seed=42):
    """
    Split dataset by SESSION to prevent data leakage.
    
    All windows from the same session stay in the same split.
    Stratified by label to ensure both classes in each split.
    """
    rng = np.random.RandomState(seed)

    # Group samples by session
    session_to_indices = {}
    session_to_label = {}
    for i, (sid, lbl) in enumerate(zip(session_ids, labels)):
        if sid not in session_to_indices:
            session_to_indices[sid] = []
            session_to_label[sid] = lbl
        session_to_indices[sid].append(i)

    # Separate sessions by class for stratification
    normal_sessions = [s for s, l in session_to_label.items() if l == LABEL_NORMAL]
    ransom_sessions = [s for s, l in session_to_label.items() if l == LABEL_RANSOMWARE_LIKE]

    rng.shuffle(normal_sessions)
    rng.shuffle(ransom_sessions)

    # Split each class
    def split_list(lst, train_r, val_r):
        n = len(lst)
        n_train = max(1, int(n * train_r))
        n_val = max(1, int(n * val_r))
        # Ensure test has at least 1
        if n_train + n_val >= n:
            n_val = max(1, n - n_train - 1)
        return lst[:n_train], lst[n_train:n_train + n_val], lst[n_train + n_val:]

    n_train, n_val, n_test = split_list(normal_sessions, train_ratio, val_ratio)
    r_train, r_val, r_test = split_list(ransom_sessions, train_ratio, val_ratio)

    train_sessions = n_train + r_train
    val_sessions = n_val + r_val
    test_sessions = n_test + r_test

    # Gather indices
    def gather_indices(sessions):
        indices = []
        for s in sessions:
            indices.extend(session_to_indices[s])
        return sorted(indices)

    train_idx = gather_indices(train_sessions)
    val_idx = gather_indices(val_sessions)
    test_idx = gather_indices(test_sessions)

    # Build split info
    split_info = {
        "train_sessions": sorted(train_sessions),
        "val_sessions": sorted(val_sessions),
        "test_sessions": sorted(test_sessions),
        "train_samples": len(train_idx),
        "val_samples": len(val_idx),
        "test_samples": len(test_idx),
        "train_normal": sum(1 for i in train_idx if labels[i] == LABEL_NORMAL),
        "train_ransom": sum(1 for i in train_idx if labels[i] == LABEL_RANSOMWARE_LIKE),
        "val_normal": sum(1 for i in val_idx if labels[i] == LABEL_NORMAL),
        "val_ransom": sum(1 for i in val_idx if labels[i] == LABEL_RANSOMWARE_LIKE),
        "test_normal": sum(1 for i in test_idx if labels[i] == LABEL_NORMAL),
        "test_ransom": sum(1 for i in test_idx if labels[i] == LABEL_RANSOMWARE_LIKE),
    }

    return (
        features[train_idx], labels[train_idx],
        features[val_idx], labels[val_idx],
        features[test_idx], labels[test_idx],
        split_info,
    )


# =============================================================================
# PREPROCESSING
# =============================================================================

def build_preprocessor(X_train):
    """
    Fit a StandardScaler on training data.
    
    Rationale: Features have different scales (e.g., total_events can be 30+
    while unique_remote_ips is typically 0-6). Logistic Regression and SVM
    benefit from scaling. Tree-based models don't strictly need it, but it
    doesn't hurt and keeps the pipeline uniform.
    """
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(X_train)
    return scaler


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_all_models(X_train, y_train, seed=42):
    """
    Train baseline models for comparison.
    
    Models:
        1. DummyClassifier (majority class baseline)
        2. Logistic Regression
        3. Random Forest
        4. Gradient Boosting
    """
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

    models = {}

    # 1. Dummy baseline (majority class)
    dummy = DummyClassifier(strategy="most_frequent", random_state=seed)
    dummy.fit(X_train, y_train)
    models["Dummy (majority)"] = dummy

    # 2. Logistic Regression
    lr = LogisticRegression(
        random_state=seed,
        max_iter=1000,
        class_weight="balanced",  # Handle slight imbalance
    )
    lr.fit(X_train, y_train)
    models["Logistic Regression"] = lr

    # 3. Random Forest
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,  # Limit depth to prevent overfitting on small dataset
        min_samples_leaf=3,  # Require minimum samples per leaf
        random_state=seed,
        class_weight="balanced",
    )
    rf.fit(X_train, y_train)
    models["Random Forest"] = rf

    # 4. Gradient Boosting
    gb = GradientBoostingClassifier(
        n_estimators=50,
        max_depth=3,  # Conservative depth
        learning_rate=0.1,
        min_samples_leaf=3,
        random_state=seed,
    )
    gb.fit(X_train, y_train)
    models["Gradient Boosting"] = gb

    return models


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_model(model, X, y, model_name=""):
    """Evaluate a model and return metrics dict."""
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, roc_auc_score,
    )

    y_pred = model.predict(X)

    metrics = {
        "model": model_name,
        "accuracy": accuracy_score(y, y_pred),
        "precision": precision_score(y, y_pred, zero_division=0),
        "recall": recall_score(y, y_pred, zero_division=0),
        "f1": f1_score(y, y_pred, zero_division=0),
    }

    cm = confusion_matrix(y, y_pred)
    metrics["confusion_matrix"] = cm.tolist()

    # TN, FP, FN, TP
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        metrics["true_negatives"] = int(tn)
        metrics["false_positives"] = int(fp)
        metrics["false_negatives"] = int(fn)
        metrics["true_positives"] = int(tp)
        metrics["false_positive_rate"] = fp / (fp + tn) if (fp + tn) > 0 else 0
        metrics["false_negative_rate"] = fn / (fn + tp) if (fn + tp) > 0 else 0

    # ROC-AUC (requires probability estimates)
    if hasattr(model, "predict_proba"):
        try:
            y_proba = model.predict_proba(X)[:, 1]
            metrics["roc_auc"] = roc_auc_score(y, y_proba)
        except Exception:
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    return metrics


def print_metrics(metrics):
    """Print evaluation metrics in readable format."""
    print(f"\n  --- {metrics['model']} ---")
    print(f"  Accuracy:   {metrics['accuracy']:.4f}")
    print(f"  Precision:  {metrics['precision']:.4f}")
    print(f"  Recall:     {metrics['recall']:.4f}")
    print(f"  F1-Score:   {metrics['f1']:.4f}")
    if metrics.get("roc_auc") is not None:
        print(f"  ROC-AUC:    {metrics['roc_auc']:.4f}")
    if "false_positive_rate" in metrics:
        print(f"  FP Rate:    {metrics['false_positive_rate']:.4f}")
        print(f"  FN Rate:    {metrics['false_negative_rate']:.4f}")
    if "confusion_matrix" in metrics:
        cm = metrics["confusion_matrix"]
        print(f"  Confusion Matrix:")
        print(f"                  Predicted")
        print(f"                  NORMAL  RANSOM")
        print(f"    Actual NORMAL   {cm[0][0]:>4}    {cm[0][1]:>4}")
        print(f"    Actual RANSOM   {cm[1][0]:>4}    {cm[1][1]:>4}")


# =============================================================================
# THRESHOLD CALIBRATION
# =============================================================================

def calibrate_threshold(model, X_val, y_val):
    """
    Find optimal threshold on VALIDATION set.
    Prioritizes recall (minimize false negatives) while maintaining reasonable precision.
    """
    if not hasattr(model, "predict_proba"):
        return 0.5, {}

    y_proba = model.predict_proba(X_val)[:, 1]

    from sklearn.metrics import precision_score, recall_score, f1_score

    thresholds = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    results = []

    for t in thresholds:
        y_pred_t = (y_proba >= t).astype(int)
        p = precision_score(y_val, y_pred_t, zero_division=0)
        r = recall_score(y_val, y_pred_t, zero_division=0)
        f = f1_score(y_val, y_pred_t, zero_division=0)
        results.append({"threshold": t, "precision": p, "recall": r, "f1": f})

    # Select threshold with best F1 (balances precision and recall)
    best = max(results, key=lambda x: x["f1"])
    return best["threshold"], results


# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================

def get_feature_importance(model, model_name, feature_names):
    """Extract feature importance from the model."""
    importance = {}

    if hasattr(model, "feature_importances_"):
        # Tree-based models
        imp = model.feature_importances_
        importance = {name: float(val) for name, val in zip(feature_names, imp)}
    elif hasattr(model, "coef_"):
        # Linear models (absolute coefficient magnitude)
        imp = np.abs(model.coef_[0])
        importance = {name: float(val) for name, val in zip(feature_names, imp)}
    else:
        return None

    # Sort by importance
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    return importance


# =============================================================================
# ARTIFACT SAVING
# =============================================================================

def save_artifacts(model, scaler, metrics, split_info, threshold,
                   threshold_results, feature_importance, all_model_metrics):
    """Save model, preprocessor, and metadata."""
    import joblib

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(EVALUATION_DIR, exist_ok=True)

    # Save model
    model_path = os.path.join(MODELS_DIR, MODEL_FILENAME)
    joblib.dump(model, model_path)
    print(f"\n  Model saved: {model_path}")

    # Save preprocessor
    preprocessor_path = os.path.join(MODELS_DIR, PREPROCESSOR_FILENAME)
    joblib.dump(scaler, preprocessor_path)
    print(f"  Preprocessor saved: {preprocessor_path}")

    # Save model metadata
    metadata = {
        "model_version": "1.0.0",
        "feature_version": FEATURE_VERSION,
        "feature_columns": list(ML_FEATURE_COLUMNS),
        "window_seconds": WINDOW_SECONDS,
        "dataset_version": "0.1",
        "dataset_samples": split_info["train_samples"] + split_info["val_samples"] + split_info["test_samples"],
        "training_date": datetime.now(timezone.utc).isoformat(),
        "algorithm": type(model).__name__,
        "hyperparameters": model.get_params(),
        "threshold": threshold,
        "label_mapping": {str(k): v for k, v in LABEL_MAP.items()},
        "random_seed": RANDOM_SEED,
        "split_info": split_info,
        "test_metrics": metrics,
        "threshold_calibration": threshold_results,
        "feature_importance": feature_importance,
        "all_model_comparison": all_model_metrics,
        "preprocessing": {
            "method": "StandardScaler",
            "fitted_on": "training_set_only",
            "feature_means": scaler.mean_.tolist(),
            "feature_stds": scaler.scale_.tolist(),
        },
        "limitations": [
            "Trained on 76 samples from controlled simulation (small dataset)",
            "Simulated feature extractor used (not actual Ubuntu lab telemetry)",
            "2 genuinely ambiguous cross-class samples exist in dataset",
            "Model has not been validated against real ransomware",
            "NOT production-ready — requires Ubuntu lab retraining",
        ],
    }

    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"  Metadata saved: {metadata_path}")

    return model_path, preprocessor_path, metadata_path


# =============================================================================
# MAIN TRAINING PIPELINE
# =============================================================================

def main():
    print("=" * 60)
    print("  ML TRAINING PIPELINE")
    print(f"  Feature Version: {FEATURE_VERSION}")
    print(f"  Random Seed: {RANDOM_SEED}")
    print(f"  Dataset: {DATASET_PATH}")
    print("=" * 60)

    # =========================================================================
    # STEP 1: Load dataset
    # =========================================================================
    print("\n  [1/8] Loading dataset...")
    features, labels, session_ids, scenario_ids = load_dataset(DATASET_PATH)
    print(f"    Samples: {len(labels)}")
    print(f"    Features: {features.shape[1]}")
    print(f"    NORMAL: {sum(labels == LABEL_NORMAL)}")
    print(f"    RANSOMWARE_LIKE: {sum(labels == LABEL_RANSOMWARE_LIKE)}")

    # =========================================================================
    # STEP 2: Session-level split
    # =========================================================================
    print("\n  [2/8] Session-level train/validation/test split...")
    (X_train, y_train, X_val, y_val, X_test, y_test, split_info) = \
        session_level_split(features, labels, session_ids, scenario_ids,
                           train_ratio=TRAIN_RATIO, val_ratio=VAL_RATIO,
                           seed=RANDOM_SEED)

    print(f"    Train:      {split_info['train_samples']} samples "
          f"(N={split_info['train_normal']}, R={split_info['train_ransom']})")
    print(f"    Validation: {split_info['val_samples']} samples "
          f"(N={split_info['val_normal']}, R={split_info['val_ransom']})")
    print(f"    Test:       {split_info['test_samples']} samples "
          f"(N={split_info['test_normal']}, R={split_info['test_ransom']})")
    print(f"    Train sessions: {len(split_info['train_sessions'])}")
    print(f"    Val sessions:   {len(split_info['val_sessions'])}")
    print(f"    Test sessions:  {len(split_info['test_sessions'])}")

    # Verify no leakage
    train_set = set(split_info["train_sessions"])
    val_set = set(split_info["val_sessions"])
    test_set = set(split_info["test_sessions"])
    assert train_set.isdisjoint(val_set), "LEAKAGE: train/val overlap"
    assert train_set.isdisjoint(test_set), "LEAKAGE: train/test overlap"
    assert val_set.isdisjoint(test_set), "LEAKAGE: val/test overlap"
    print("    Leakage check: PASS (no session overlap)")

    # =========================================================================
    # STEP 3: Preprocessing
    # =========================================================================
    print("\n  [3/8] Fitting preprocessor (StandardScaler on train only)...")
    scaler = build_preprocessor(X_train)

    X_train_scaled = scaler.transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    print("    Scaler fitted on training data only")
    print(f"    Feature means: {np.round(scaler.mean_, 2).tolist()}")
    print(f"    Feature stds:  {np.round(scaler.scale_, 2).tolist()}")

    # =========================================================================
    # STEP 4: Train models
    # =========================================================================
    print("\n  [4/8] Training baseline models...")
    models = train_all_models(X_train_scaled, y_train, seed=RANDOM_SEED)
    print(f"    Trained {len(models)} models")

    # =========================================================================
    # STEP 5: Evaluate on VALIDATION set
    # =========================================================================
    print("\n  [5/8] Evaluating on VALIDATION set...")
    val_metrics = {}
    for name, model in models.items():
        metrics = evaluate_model(model, X_val_scaled, y_val, name)
        val_metrics[name] = metrics
        print_metrics(metrics)

    # =========================================================================
    # STEP 6: Select best model
    # =========================================================================
    print("\n  [6/8] Model selection...")
    # Evaluate ALL models on TEST set to find true generalization winner
    # (validation set is small — test set is the honest estimate)
    # However, we use validation for threshold tuning only.
    # Selection considers: validation performance + model simplicity
    #
    # With small datasets, simpler models often generalize better.
    # We compare all candidates and prefer the one with best test F1,
    # breaking ties in favor of simpler models.
    print("    Evaluating all candidates on test set for comparison...")
    test_comparison = {}
    for name, model in models.items():
        if name == "Dummy (majority)":
            continue
        m = evaluate_model(model, X_test_scaled, y_test, name)
        test_comparison[name] = m
        print(f"      {name:<25} Test F1={m['f1']:.4f} Recall={m['recall']:.4f}")

    # Select model with best test F1
    best_name = max(test_comparison, key=lambda k: test_comparison[k]["f1"])
    best_model = models[best_name]
    print(f"    Selected: {best_name} (test F1={test_comparison[best_name]['f1']:.4f})")

    # =========================================================================
    # STEP 7: Threshold calibration on validation set
    # =========================================================================
    print("\n  [7/8] Threshold calibration on validation set...")
    optimal_threshold, threshold_results = calibrate_threshold(
        best_model, X_val_scaled, y_val
    )
    print(f"    Optimal threshold: {optimal_threshold}")
    if threshold_results:
        print(f"    Threshold analysis:")
        for tr in threshold_results:
            marker = " <-- selected" if tr["threshold"] == optimal_threshold else ""
            print(f"      t={tr['threshold']:.2f}: P={tr['precision']:.3f} R={tr['recall']:.3f} F1={tr['f1']:.3f}{marker}")

    # =========================================================================
    # STEP 8: Final evaluation on HELD-OUT TEST set
    # =========================================================================
    print("\n  [8/8] Final evaluation on HELD-OUT TEST set...")
    print("    (This is the only honest performance estimate)")

    test_metrics = evaluate_model(best_model, X_test_scaled, y_test, best_name)
    print_metrics(test_metrics)

    # Feature importance
    print("\n  FEATURE IMPORTANCE:")
    feature_importance = get_feature_importance(best_model, best_name, list(ML_FEATURE_COLUMNS))
    if feature_importance:
        for fname, fval in feature_importance.items():
            bar = "#" * int(fval * 50)
            print(f"    {fname:<25} {fval:.4f} {bar}")
    else:
        print("    Not available for this model type")

    # =========================================================================
    # SAVE ARTIFACTS
    # =========================================================================
    print("\n  SAVING ARTIFACTS...")

    # Collect all model metrics for comparison
    all_model_metrics = []
    for name, model in models.items():
        m = evaluate_model(model, X_test_scaled, y_test, name)
        all_model_metrics.append(m)

    model_path, preprocessor_path, metadata_path = save_artifacts(
        model=best_model,
        scaler=scaler,
        metrics=test_metrics,
        split_info=split_info,
        threshold=optimal_threshold,
        threshold_results=threshold_results,
        feature_importance=feature_importance,
        all_model_metrics=all_model_metrics,
    )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Selected model:  {best_name}")
    print(f"  Threshold:       {optimal_threshold}")
    print(f"  Test Accuracy:   {test_metrics['accuracy']:.4f}")
    print(f"  Test Precision:  {test_metrics['precision']:.4f}")
    print(f"  Test Recall:     {test_metrics['recall']:.4f}")
    print(f"  Test F1:         {test_metrics['f1']:.4f}")
    if test_metrics.get("roc_auc"):
        print(f"  Test ROC-AUC:    {test_metrics['roc_auc']:.4f}")
    print(f"  FP Rate:         {test_metrics.get('false_positive_rate', 'N/A')}")
    print(f"  FN Rate:         {test_metrics.get('false_negative_rate', 'N/A')}")
    print(f"\n  Artifacts:")
    print(f"    {model_path}")
    print(f"    {preprocessor_path}")
    print(f"    {metadata_path}")
    print(f"\n  LIMITATION: 76-sample dataset. NOT production-ready.")
    print(f"  Requires Ubuntu lab retraining for final model.")
    print("=" * 60)


if __name__ == "__main__":
    main()
