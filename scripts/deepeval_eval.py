"""DeepEval judge for the existing planner.

Run this on purpose. It does not start with the API, the React app, or
scripts/evaluate.py, and it writes a separate results file.
"""
import json
import os
import sys

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "1")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from deepeval.evaluate.configs import AsyncConfig, DisplayConfig, ErrorConfig
from deepeval.metrics import AnswerRelevancyMetric, ContextualRelevancyMetric, FaithfulnessMetric
from deepeval.models import OpenAIModel
from deepeval.test_case import LLMTestCase

from src.utils.config import settings

# The same four cases scripts/evaluate.py already uses.
BENCHMARK_QUERIES = [
    {
        "query_id": "Q1",
        "query": "I have 5 days and around INR 40,000. I'm travelling with friends and want beaches, good food, nightlife and some adventure.",
        "expected_destination": "Goa",
    },
    {
        "query_id": "Q2",
        "query": "4 days mountain adventure with friends for paragliding, river rafting, and scenic trekking under INR 30,000.",
        "expected_destination": "Manali",
    },
    {
        "query_id": "Q3",
        "query": "3 days family heritage tour exploring royal forts, palace architecture, and traditional Rajasthani dining for INR 35,000.",
        "expected_destination": "Jaipur",
    },
    {
        "query_id": "Q4",
        "query": "7 days romantic couple trip in Bali with yoga retreats, rice terrace walks, and sunset beach clubs with INR 120,000 budget.",
        "expected_destination": "Bali",
    },
]


def judge_model() -> OpenAIModel:
    api_key = settings.LLM_API_KEY or os.environ.get("LLM_API_KEY", "")
    if not api_key:
        raise RuntimeError("Set LLM_API_KEY before running the DeepEval judge.")
    return OpenAIModel(
        model=settings.LLM_MODEL or "gpt-5-nano",
        api_key=api_key,
        base_url=(settings.LLM_BASE_URL or "https://aicredits.in/v1").rstrip("/"),
        generation_kwargs={
            "max_completion_tokens": 8000,
            "reasoning_effort": "low",
        },
    )


def itinerary_text(workflow_res: dict) -> str:
    itinerary = workflow_res.get("itinerary") or {}
    destination = (workflow_res.get("destinations") or {}).get("primary_recommendation") or ""
    lines = [itinerary.get("trip_title") or "", f"Destination: {destination}"]
    for day in itinerary.get("daily_itinerary") or []:
        lines.append(f"Day {day.get('day_number')}: {day.get('theme')}")
        for slot in ("morning", "afternoon", "evening"):
            block = day.get(slot) or {}
            activity = block.get("activity") or ""
            if activity:
                lines.append(f"{slot}: {activity}")
    return "\n".join(line for line in lines if line).strip()


def build_test_case(query: str, expected_destination: str, workflow_res: dict, documents: list) -> LLMTestCase:
    context = []
    for doc in documents[:5]:
        text = (doc.get("text") or "").strip()
        if text:
            context.append(text[:1200])
    if not context:
        context = ["No retrieval context was returned for this query."]
    return LLMTestCase(
        input=query,
        actual_output=itinerary_text(workflow_res) or f"Destination: {expected_destination}",
        expected_output=expected_destination,
        retrieval_context=context,
    )


def _metric_row(metric) -> dict:
    return {
        "name": getattr(metric, "name", metric.__class__.__name__),
        "score": getattr(metric, "score", None),
        "success": getattr(metric, "success", None),
        "reason": getattr(metric, "reason", None),
    }


def run_deepeval():
    from deepeval import evaluate

    from src.rag.hybrid_retriever import hybrid_retriever
    from src.services.langgraph_workflow import travel_graph

    model = judge_model()
    metrics = [
        AnswerRelevancyMetric(threshold=0.5, model=model, async_mode=False),
        FaithfulnessMetric(threshold=0.5, model=model, async_mode=False),
        ContextualRelevancyMetric(threshold=0.5, model=model, async_mode=False),
    ]
    cases = []
    for test in BENCHMARK_QUERIES:
        print(f"[*] Planning {test['query_id']} for DeepEval...")
        documents = hybrid_retriever.retrieve(test["query"], n_results=5)
        state = {
            "user_query": test["query"],
            "sanitized_query": "",
            "guardrail_status": {},
            "preferences": {},
            "retrieved_documents": [],
            "destinations": {},
            "budget_analysis": {},
            "activities": {},
            "accommodations": {},
            "itinerary": {},
            "validation": {},
            "refinement_count": 0,
            "refinement_feedback": "",
            "agent_traces": [],
            "errors": [],
        }
        workflow_res = travel_graph.invoke(state)
        cases.append(build_test_case(test["query"], test["expected_destination"], workflow_res, documents))

    result = evaluate(
        test_cases=cases,
        metrics=metrics,
        async_config=AsyncConfig(run_async=False, max_concurrent=1),
        display_config=DisplayConfig(print_results=True, inspect_after_run=False),
        error_config=ErrorConfig(ignore_errors=True),
    )
    rows = []
    for test_result in result.test_results or []:
        rows.append({
            "input": getattr(test_result, "input", ""),
            "success": getattr(test_result, "success", None),
            "metrics": [_metric_row(metric) for metric in (getattr(test_result, "metrics_data", None) or [])],
        })
    summary = {"cases": rows, "test_run_id": getattr(result, "test_run_id", None)}
    os.makedirs("./docs", exist_ok=True)
    out_path = "./docs/deepeval_summary.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Wrote {out_path}")
    return summary


if __name__ == "__main__":
    run_deepeval()
