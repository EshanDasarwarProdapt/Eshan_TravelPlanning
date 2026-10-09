from typing import Dict, Any
from src.agents.budget_analyst import calculate_budget_feasibility

class BudgetService:
    def evaluate(self, preferences: Dict[str, Any], destination_info: Dict[str, Any]) -> Dict[str, Any]:
        return calculate_budget_feasibility(preferences, destination_info)

budget_service = BudgetService()
