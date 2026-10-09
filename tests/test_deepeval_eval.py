import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.deepeval_eval import build_test_case, itinerary_text


def test_itinerary_text_includes_day_and_destination():
    text = itinerary_text({
        "destinations": {"primary_recommendation": "Goa"},
        "itinerary": {
            "trip_title": "Goa with friends",
            "daily_itinerary": [
                {
                    "day_number": 1,
                    "theme": "Beaches",
                    "morning": {"activity": "Baga beach"},
                    "afternoon": {"activity": "Fort"},
                    "evening": {"activity": "Dinner, then the night at the hotel"},
                }
            ],
        },
    })
    assert "Goa" in text
    assert "Baga beach" in text
    assert "Day 1" in text


def test_build_test_case_keeps_retrieval_context():
    case = build_test_case(
        "5 days in Goa",
        "Goa",
        {"destinations": {"primary_recommendation": "Goa"}, "itinerary": {"trip_title": "Goa"}},
        [{"text": "UCI feedback for Goa beaches."}],
    )
    assert case.input == "5 days in Goa"
    assert case.expected_output == "Goa"
    assert case.retrieval_context == ["UCI feedback for Goa beaches."]
    assert "Goa" in case.actual_output
