"""Researched prices for the Explore destinations.

Delhi departures use this file. Any other origin, and any city that is not
listed here, still asks the travel model at runtime.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.knowledge.travel_facts import canonical_city

_PATH = Path("./data/stored_trip_prices.json")


def _key(name: str) -> str:
    return " ".join((name or "").lower().replace("&", " ").split())


@lru_cache(maxsize=1)
def _catalog() -> Dict[str, Dict[str, Any]]:
    payload = json.loads(_PATH.read_text(encoding="utf-8"))
    index: Dict[str, Dict[str, Any]] = {}
    for place in payload.get("places") or []:
        for name in place.get("names") or []:
            index[_key(name)] = place
            canon = canonical_city(name)
            if canon:
                index[_key(canon)] = place
    return index


def price_for(name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    found = _catalog().get(_key(name))
    if found:
        return found
    canon = canonical_city(name)
    if canon:
        return _catalog().get(_key(canon))
    return None


def fare_options(origin: Optional[str], destination: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """Round-trip choices when this destination was priced from the traveler's city."""
    if canonical_city(origin) != "Delhi":
        return None
    place = price_for(destination)
    if not place:
        return None
    origin_name = canonical_city(origin) or "Delhi"
    dest_name = canonical_city(destination) or destination
    options = []
    for mode in place.get("modes") or []:
        options.append({
            "mode": mode["mode"],
            "label": mode.get("label") or mode["mode"],
            "route": f"{origin_name} → {dest_name} → {origin_name}",
            "duration": mode.get("duration") or "",
            "stops": mode.get("stops") or "",
            "per_person_price": int(mode["per_person_price"]),
            "duration_minutes": int(mode.get("duration_minutes") or 9999),
            "fastest": False,
            "booking_tip": "Stored typical round-trip fare from Delhi for one adult. Confirm it before you book.",
        })
    options.sort(key=lambda item: (item["duration_minutes"], item["per_person_price"]))
    if options:
        options[0]["fastest"] = True
    return options
