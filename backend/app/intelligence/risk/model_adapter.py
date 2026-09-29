"""Adapter for loading scikit-learn risk model or providing prototype fallback."""

import json
from pathlib import Path
import pickle
from typing import Any, Dict, Optional, Tuple

MODEL_FILE_LOCATIONS = [
    Path("backend/app/intelligence/risk/actus_risk_model.pkl"),
    Path("storage/models/actus_risk_model.pkl"),
    Path("actus_risk_model.pkl"),
]

FEATURE_COLS_LOCATIONS = [
    Path("backend/app/intelligence/risk/feature_cols.json"),
    Path("storage/models/feature_cols.json"),
    Path("feature_cols.json"),
]


class RiskModelAdapter:
    """Model loader and predictor adapter."""

    _model: Optional[Any] = None
    _feature_cols: Optional[list] = None
    _model_loaded: bool = False

    @classmethod
    def load_model(cls) -> bool:
        """Attempt to locate and load trained scikit-learn model and feature_cols.json."""
        if cls._model_loaded:
            return cls._model is not None

        model_path = next((p for p in MODEL_FILE_LOCATIONS if p.exists()), None)
        cols_path = next((p for p in FEATURE_COLS_LOCATIONS if p.exists()), None)

        if model_path and cols_path:
            try:
                with open(model_path, "rb") as f:
                    cls._model = pickle.load(f)
                with open(cols_path, "r", encoding="utf-8") as f:
                    cls._feature_cols = json.load(f)
                cls._model_loaded = True
                return True
            except Exception:
                cls._model = None
                cls._feature_cols = None
                cls._model_loaded = True
                return False

        cls._model_loaded = True
        return False

    @classmethod
    def predict_risk(
        cls, features_dict: Dict[str, float], principal: float
    ) -> Dict[str, Any]:
        """Predict contract default probability, category, expected loss, and recommendation."""
        has_ml = cls.load_model()

        if has_ml and cls._model and cls._feature_cols:
            try:
                # Order features strictly by feature_cols.json
                input_vector = [features_dict.get(col, 0.0) for col in cls._feature_cols]
                prob = float(cls._model.predict_proba([input_vector])[0][1])
                prob_pct = round(prob * 100.0, 1)

                if prob <= 0.20:
                    category = "LOW"
                    rec = "APPROVE"
                elif prob <= 0.50:
                    category = "MEDIUM"
                    rec = "APPROVE WITH CONDITIONS"
                else:
                    category = "HIGH"
                    rec = "REJECT"

                ead = principal
                expected_loss = round(prob * ead, 2)

                return {
                    "model_available": True,
                    "estimator_type": "Trained ML Risk Model (RandomForest/XGBoost)",
                    "default_probability": round(prob, 4),
                    "default_probability_percent": prob_pct,
                    "risk_category": category,
                    "expected_loss": expected_loss,
                    "recommendation": rec,
                    "message": "Risk prediction evaluated using trained ML model.",
                }
            except Exception as e:
                pass

        # Transparent Fallback when ML model file is not configured
        # Calculate prototype score for demonstration
        rate = features_dict.get("annual_interest_rate", 10.0)
        overdue = features_dict.get("overdue_payment_count", 0.0)
        duration = features_dict.get("loan_duration_months", 24.0)

        # Baseline probability estimate
        base_prob = 0.05 + (rate / 100.0) * 0.8 + (overdue * 0.15) + (duration / 120.0) * 0.05
        proto_prob = min(0.95, max(0.02, round(base_prob, 4)))
        proto_pct = round(proto_prob * 100.0, 1)

        if proto_prob <= 0.20:
            category = "LOW"
            rec = "APPROVE"
        elif proto_prob <= 0.50:
            category = "MEDIUM"
            rec = "APPROVE WITH CONDITIONS"
        else:
            category = "HIGH"
            rec = "REJECT"

        expected_loss = round(proto_prob * principal, 2)

        return {
            "model_available": False,
            "estimator_type": "Prototype risk estimator",
            "default_probability": proto_prob,
            "default_probability_percent": proto_pct,
            "risk_category": category,
            "expected_loss": expected_loss,
            "recommendation": rec,
            "message": "ML risk model is not configured; using prototype risk estimator.",
        }
