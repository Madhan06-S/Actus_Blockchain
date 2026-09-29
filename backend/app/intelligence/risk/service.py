"""Risk prediction service orchestrating feature extraction and model prediction."""

from app.intelligence.context_builder import build_contract_intelligence_context
from app.intelligence.risk.feature_extractor import FeatureExtractor
from app.intelligence.risk.model_adapter import RiskModelAdapter
from app.intelligence.risk.schemas import FeatureImportanceItem, RiskPredictionResponse


class RiskPredictionService:
    """Business service evaluating contract risk via extracted quantitative features and ML adapter."""

    def evaluate_contract_risk(self, contract_id: str) -> RiskPredictionResponse:
        """Extract contract features and run risk evaluation."""
        ctx = build_contract_intelligence_context(contract_id)
        features_dict, metadata_list = FeatureExtractor.extract_features(ctx)
        principal = float(ctx["contract"]["principal"])

        prediction = RiskModelAdapter.predict_risk(features_dict, principal)

        feature_items = [
            FeatureImportanceItem(
                name=m["name"],
                value=m["value"],
                description=m["description"],
            )
            for m in metadata_list
        ]

        return RiskPredictionResponse(
            contract_id=contract_id,
            default_probability=prediction.get("default_probability"),
            default_probability_percent=prediction.get("default_probability_percent"),
            risk_category=prediction["risk_category"],
            expected_loss=prediction.get("expected_loss"),
            recommendation=prediction["recommendation"],
            model_available=prediction["model_available"],
            estimator_type=prediction["estimator_type"],
            features_used=feature_items,
            message=prediction.get("message"),
        )


risk_prediction_service = RiskPredictionService()
