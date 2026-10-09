"""Destination discovery from stored traveler ratings.

Ratings, traveler counts, and category scores are averages of the processed
review records. A destination with no records is listed without a score.
"""
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA_PATH = Path("./data/processed/processed_travel_reviews.json")

# The names on the left are the ones shown on the page. The names on the right
# are the destination labels stored on the traveler records.
THEMES = [
    {
        "id": "beaches",
        "title": "Beaches & Scuba Diving",
        "places": [
            ("Bali", "Bali"),
            ("Phuket", "Phuket"),
            ("Andaman & Nicobar", "Andaman Islands"),
        ],
    },
    {
        "id": "mountains",
        "title": "Mountains & Adventure",
        "places": [
            ("Ladakh", "Leh Ladakh"),
            ("Manali", "Manali"),
            ("Kashmir", None),
        ],
    },
    {
        "id": "deserts",
        "title": "Deserts & Culture",
        "places": [
            ("Jaisalmer", None),
            ("Jaipur", "Jaipur"),
            ("Jodhpur", None),
        ],
    },
    {
        "id": "lakes",
        "title": "Lakes & Heritage",
        "places": [
            ("Udaipur", "Udaipur"),
            ("Srinagar", None),
            ("Kerala backwaters", "Kerala (Munnar & Alleppey)"),
        ],
    },
    {
        "id": "wildlife",
        "title": "Wildlife & Nature",
        "places": [
            ("Jim Corbett & Ranthambore", "Jim Corbett & Ranthambore"),
            ("Kerala wildlife", "Kerala (Periyar & Wayanad)"),
        ],
    },
    {
        "id": "spiritual",
        "title": "Spiritual & Cultural",
        "places": [
            ("Varanasi", "Varanasi"),
            ("Rishikesh", None),
            ("Amritsar", None),
        ],
    },
    {
        "id": "luxury",
        "title": "Relaxation & Luxury",
        "places": [
            ("Goa", "Goa"),
            ("Maldives", "Maldives"),
            ("Bali", "Bali"),
        ],
    },
]

# Words that should pick an Explore card. A mountains search stays on these
# trips instead of any record whose loose category tag happens to match.
PLACE_INTERESTS = {
    "Bali": ["beach", "scuba", "diving", "snorkel", "island", "bali", "luxury", "relax"],
    "Phuket": ["beach", "scuba", "diving", "snorkel", "island", "phuket"],
    "Andaman & Nicobar": ["beach", "scuba", "diving", "snorkel", "island", "andaman"],
    "Ladakh": ["mountain", "trek", "hiking", "snow", "ladakh", "leh", "hill", "adventure"],
    "Manali": ["mountain", "trek", "hiking", "snow", "manali", "hill", "adventure"],
    "Kashmir": ["mountain", "trek", "hiking", "snow", "kashmir", "hill", "valley", "adventure"],
    "Jaisalmer": ["desert", "sand", "fort", "jaisalmer", "heritage"],
    "Jaipur": ["heritage", "fort", "palace", "jaipur", "sightseeing", "culture"],
    "Jodhpur": ["desert", "fort", "palace", "jodhpur", "heritage"],
    "Udaipur": ["lake", "palace", "udaipur", "heritage", "sightseeing"],
    "Srinagar": ["lake", "houseboat", "srinagar", "dal"],
    "Kerala backwaters": ["lake", "backwater", "houseboat", "kerala", "munnar", "alleppey"],
    "Jim Corbett & Ranthambore": ["wildlife", "safari", "tiger", "jungle", "corbett", "ranthambore"],
    "Kerala wildlife": ["wildlife", "safari", "tiger", "jungle", "periyar", "wayanad"],
    "Varanasi": ["spiritual", "temple", "ghat", "varanasi", "culture"],
    "Rishikesh": ["spiritual", "temple", "yoga", "rishikesh", "rafting"],
    "Amritsar": ["spiritual", "temple", "amritsar", "heritage"],
    "Goa": ["beach", "nightlife", "goa", "relax", "luxury"],
    "Maldives": ["beach", "island", "maldives", "luxury", "relax", "scuba", "diving"],
}

INTEREST_WORDS = (
    ("scuba", "beaches"),
    ("diving", "beaches"),
    ("beach", "beaches"),
    ("snorkel", "beaches"),
    ("mountain", "adventure"),
    ("trek", "adventure"),
    ("adventure", "adventure"),
    ("wildlife", "wildlife"),
    ("safari", "wildlife"),
    ("tiger", "wildlife"),
    ("temple", "spiritual"),
    ("spiritual", "spiritual"),
    ("heritage", "heritage"),
    ("fort", "heritage"),
    ("palace", "heritage"),
    ("sightseeing", "heritage"),
    ("culture", "heritage"),
    ("food", "food"),
    ("cuisine", "food"),
    ("dining", "food"),
    ("lake", "nature"),
    ("nature", "nature"),
    ("luxury", "luxury"),
    ("relax", "wellness"),
    ("spa", "wellness"),
    ("desert", "heritage"),
)

_CACHE: Dict[str, Any] = {}


def _records() -> List[Dict[str, Any]]:
    if "records" not in _CACHE:
        with _DATA_PATH.open(encoding="utf-8") as handle:
            _CACHE["records"] = json.load(handle)
    return _CACHE["records"]


def _mean(values: List[float]) -> float:
    return round(sum(values) / len(values), 2)


def _plan_for(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    sample = rows[0]
    ratings = [float(row["rating"]) for row in rows]
    highlights = [part.strip() for part in str(sample.get("highlights") or "").split(",") if part.strip()]
    stays = list(sample.get("stay_types") or [])
    days = min(7, max(5, len(highlights) or 5))
    by_category: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        by_category[str(row.get("category") or "other")].append(float(row["rating"]))
    category_ratings = [
        {
            "category": name,
            "average_rating": _mean(scores),
            "travelers": len(scores),
        }
        for name, scores in sorted(by_category.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    food_scores = by_category.get("food") or []
    outline = []
    for index in range(days):
        sight = highlights[index % len(highlights)] if highlights else "Time in the destination"
        if food_scores:
            food = (
                f"Travelers who rated food here gave it {_mean(food_scores)}/5 "
                f"across {len(food_scores)} record{'' if len(food_scores) == 1 else 's'}."
            )
        else:
            food = "No food-category ratings are stored for this destination."
        stay = stays[index % len(stays)] if stays else "Stay recorded with the traveler profile"
        outline.append({
            "day_number": index + 1,
            "sightseeing": sight,
            "food": food,
            "stay": stay,
        })
    daily = int(round(sum(int(row.get("estimated_daily_cost_inr") or 0) for row in rows) / len(rows)))
    return {
        "country": sample.get("country") or "",
        "traveler_count": len(rows),
        "average_rating": _mean(ratings),
        "daily_cost_inr": daily,
        "days": days,
        "trip_cost_inr": daily * days,
        "highlights": highlights,
        "stay_types": stays,
        "category_ratings": category_ratings,
        "outline": outline,
        "best_season": sample.get("best_season") or "",
        "categories_present": sorted(by_category),
    }


def _plans_by_destination() -> Dict[str, Dict[str, Any]]:
    if "plans" in _CACHE:
        return _CACHE["plans"]
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in _records():
        grouped[row["destination"]].append(row)
    _CACHE["plans"] = {name: _plan_for(rows) for name, rows in grouped.items()}
    return _CACHE["plans"]


def _with_stored_price(place: Dict[str, Any], *names: Optional[str]) -> Dict[str, Any]:
    from src.knowledge.stored_prices import price_for
    stored = None
    for name in names:
        stored = price_for(name) if name else None
        if stored:
            break
    if not stored:
        return place
    priced = dict(place)
    priced["days"] = priced.get("days") or stored["days"]
    priced["trip_cost_inr"] = int(stored["trip_per_person"])
    ground_days = int(priced["days"] or stored["days"])
    flight = 0
    for mode in stored.get("modes") or []:
        if mode["mode"] == stored.get("included_mode"):
            flight = int(mode["per_person_price"])
            break
    priced["daily_cost_inr"] = max(0, int(round((priced["trip_cost_inr"] - flight) / ground_days)))
    priced["price_note"] = stored["note"]
    return priced


def _public_place(label: str, stored_name: Optional[str]) -> Dict[str, Any]:
    if not stored_name:
        return _with_stored_price({
            "destination": label,
            "country": "",
            "available": False,
            "traveler_count": 0,
            "note": "No traveler records in the database, so this place is not rated.",
        }, label)
    plan = _plans_by_destination().get(stored_name)
    if not plan:
        return _with_stored_price({
            "destination": label,
            "country": "",
            "available": False,
            "traveler_count": 0,
            "note": f"No traveler records are stored for {stored_name}.",
        }, label, stored_name)
    return _with_stored_price({
        "destination": stored_name,
        "display_name": label,
        "available": True,
        "note": f"Rating is the mean of {plan['traveler_count']} stored traveler scores.",
        **plan,
    }, stored_name, label)


def explore_catalog() -> Dict[str, Any]:
    themes = []
    for theme in THEMES:
        themes.append({
            "id": theme["id"],
            "title": theme["title"],
            "places": [_public_place(label, stored) for label, stored in theme["places"]],
        })
    return {"themes": themes, "record_count": len(_records())}


def _interest_tags(text: str) -> List[str]:
    low = text.lower()
    found = []
    for word, tag in INTEREST_WORDS:
        if word in low and tag not in found:
            found.append(tag)
    return found


def _word_hit(text: str, word: str) -> bool:
    if len(word) <= 3:
        return re.search(rf"\b{re.escape(word)}\b", text) is not None
    return word in text


def _explore_place_list() -> List[Dict[str, Any]]:
    places = []
    seen = set()
    for theme in THEMES:
        for label, stored in theme["places"]:
            if label in seen:
                continue
            seen.add(label)
            places.append({
                "label": label,
                "stored": stored,
                "interests": PLACE_INTERESTS.get(label, []),
            })
    return places


def _matching_places(text: str) -> List[Dict[str, Any]]:
    low = text.lower()
    matched = []
    for place in _explore_place_list():
        hits = [word for word in place["interests"] if _word_hit(low, word)]
        if hits:
            chosen = dict(place)
            chosen["hits"] = hits
            matched.append(chosen)
    return matched


def _budget_amount(text: str, explicit: Optional[int]) -> Optional[int]:
    if explicit and explicit > 0:
        return int(explicit)
    amounts = []
    for match in re.finditer(r"(\d{4,7})", text.replace(",", "")):
        value = int(match.group(1))
        tail = text[match.end():match.end() + 8].lower()
        if "day" in tail or "night" in tail:
            continue
        amounts.append(value)
    return amounts[-1] if amounts else None


def _match_row(label: str, stored_name: Optional[str], cap: Optional[int], reasons: List[str]) -> Dict[str, Any]:
    public = _public_place(label, stored_name)
    trip_cost = int(public.get("trip_cost_inr") or 0)
    rating = public.get("average_rating")
    return {
        "destination": label,
        "country": public.get("country") or "",
        "average_rating": rating,
        "similar_travelers": int(public.get("traveler_count") or 0),
        "daily_cost_inr": int(public.get("daily_cost_inr") or 0),
        "days": int(public.get("days") or 0),
        "trip_cost_inr": trip_cost,
        "within_budget": True if cap is None else trip_cost <= cap,
        "matched_categories": reasons,
    }


def recommend_experiences(preferences: str, budget: Optional[int] = None) -> Dict[str, Any]:
    text = (preferences or "").strip()
    if len(text) < 2:
        raise ValueError("Describe the kind of trip you want.")
    tags = _interest_tags(text)
    cap = _budget_amount(text, budget)
    places = _matching_places(text)
    rows = []
    if places:
        tags = sorted({hit for place in places for hit in place["hits"]})
        for place in places:
            rows.append(_match_row(place["label"], place["stored"], cap, place["hits"]))
        rows.sort(key=lambda item: (
            item["average_rating"] is None,
            -(item["average_rating"] or 0),
            -item["similar_travelers"],
            item["trip_cost_inr"],
        ))
    else:
        explore_names = {place["stored"] for place in _explore_place_list() if place["stored"]}
        labels = {place["stored"]: place["label"] for place in _explore_place_list() if place["stored"]}
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in _records():
            if row["destination"] not in explore_names:
                continue
            if tags and row.get("category") not in tags:
                continue
            grouped[row["destination"]].append(row)
        for destination, matched in grouped.items():
            if len(matched) < 8:
                continue
            plan = _with_stored_price(dict(_plans_by_destination().get(destination) or {}), destination)
            if not plan or "daily_cost_inr" not in plan:
                continue
            rating = _mean([float(row["rating"]) for row in matched])
            trip_cost = int(plan.get("trip_cost_inr") or (plan["daily_cost_inr"] * plan["days"]))
            rows.append({
                "destination": labels.get(destination, destination),
                "country": plan["country"],
                "average_rating": rating,
                "similar_travelers": len(matched),
                "daily_cost_inr": plan["daily_cost_inr"],
                "days": plan["days"],
                "trip_cost_inr": trip_cost,
                "within_budget": True if cap is None else trip_cost <= cap,
                "matched_categories": tags or plan["categories_present"],
            })
        rows.sort(key=lambda item: (-(item["average_rating"] or 0), -item["similar_travelers"], item["trip_cost_inr"]))
    affordable = [item for item in rows if item["within_budget"]]
    recommended = (affordable or rows)[:1]
    recommended_row = recommended[0] if recommended else None
    best_value = None
    if affordable:
        best_value = sorted(
            affordable,
            key=lambda item: (item["average_rating"] is None, -(item["average_rating"] or 0), item["trip_cost_inr"]),
        )[0]

    def _score_phrase(row: Dict[str, Any]) -> str:
        if row.get("average_rating") is None:
            return f"{row['destination']} has no traveler scores"
        return (
            f"{row['destination']} averages {row['average_rating']}/5 "
            f"from {row['similar_travelers']} traveler records"
        )

    compared = ", ".join(item["destination"] for item in rows)
    if not rows:
        summary = "No Explore trip matches that. Try mountains, beaches, wildlife, desert, lakes, or a city name."
    elif cap is not None and recommended_row and recommended_row["within_budget"]:
        summary = (
            f"{_score_phrase(recommended_row)}, "
            f"and the stored {recommended_row['days']}-day cost is about Rs {recommended_row['trip_cost_inr']:,}, inside Rs {cap:,}. "
            f"Compared: {compared}."
        )
    elif cap is not None and recommended_row:
        summary = (
            f"Nothing in the stored costs fits Rs {cap:,}. "
            f"The closest match is {_score_phrase(recommended_row)}."
        )
    elif recommended_row:
        summary = f"{_score_phrase(recommended_row)}. Compared: {compared}."
    else:
        summary = "No stored traveler scores match those preferences."

    return {
        "preferences": text,
        "matched_categories": tags,
        "budget": cap,
        "summary": summary,
        "recommended": recommended_row,
        "comparison": rows[:6],
        "best_value": best_value,
    }
