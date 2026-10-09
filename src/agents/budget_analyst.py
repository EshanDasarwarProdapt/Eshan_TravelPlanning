from typing import Dict, Any
from src.knowledge.travel_facts import allocate_budget
from src.utils.logging import log_agent_execution

def calculate_budget_feasibility(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agent 3 (Budget Analyst): Fits the plan to the budget the user actually stated.

    The stated amount is the ceiling. Round-trip flight, train, and bus estimates are
    compared first, and the mode that still leaves a realistic hotel and food budget wins.
    Stay, food, activities, local travel, and a buffer are then sized from the money left.
    """
    with log_agent_execution("budget_analyst"):
        merged = dict(preferences)
        if not merged.get("destination") and destination_info.get("destination"):
            merged["destination"] = destination_info.get("destination")
        return allocate_budget(merged, destination_info)
