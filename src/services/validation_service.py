from typing import Dict, Any
from src.agents.quality_validator import evaluate_plan_quality

class ValidationService:
    def evaluate(
        self,
        preferences: Dict[str, Any],
        destination_info: Dict[str, Any],
        budget_info: Dict[str, Any],
        activities_info: Dict[str, Any],
        itinerary_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        return evaluate_plan_quality(
            preferences=preferences,
            destination_info=destination_info,
            budget_info=budget_info,
            activities_info=activities_info,
            itinerary_info=itinerary_info
        )

validation_service = ValidationService()
