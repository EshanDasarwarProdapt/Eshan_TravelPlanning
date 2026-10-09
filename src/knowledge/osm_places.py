"""Real place names from OpenStreetMap for cities that are not in the local catalog.

Nominatim finds the place. Photon, which searches OpenStreetMap, returns named
sights and hotels inside that area. Costs are not in the map, so callers keep
their own estimates. If either service fails, the caller keeps the generic list.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.utils.logging import get_logger

logger = get_logger("osm_places")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PHOTON_URL = "https://photon.komoot.io/api/"
HEADERS = {
    "User-Agent": "WaypointTravelPlanner/1.0 (local trip planner)",
    "Accept-Language": "en",
}
ABROAD = {"Paris", "Dubai", "Bali", "Kyoto", "Tokyo", "Rome", "London", "Bangkok", "Singapore"}
GENERIC_NAMES = {
    "museum", "temple", "fort", "palace", "park", "beach", "market", "hotel",
    "church", "viewpoint", "attraction", "national park", "waterfall", "monument",
}
SPOT_QUERIES = (
    ("museum", "tourism:museum", "heritage"),
    ("fort", "historic:fort", "heritage"),
    ("palace", "historic:palace", "heritage"),
    ("national park", "boundary:national_park", "nature"),
    ("beach", "natural:beach", "nature"),
    ("market", "amenity:marketplace", "shopping"),
    ("temple", "amenity:place_of_worship", "heritage"),
)
HOTEL_QUERY = ("hotel", "tourism:hotel")

_CACHE: Dict[str, Tuple[float, Dict[str, List[Dict[str, Any]]]]] = {}
_CACHE_TTL_SECONDS = 60 * 60


def clear_place_cache() -> None:
    _CACHE.clear()


def lookup_places(destination: str) -> List[Dict[str, Any]]:
    """Named sights for a city. Empty when OpenStreetMap cannot be reached."""
    return list(_lookup(destination).get("spots") or [])


def lookup_hotels(destination: str) -> List[Dict[str, Any]]:
    """Named hotels in the same area. Rates are not included."""
    return list(_lookup(destination).get("hotels") or [])


def _lookup(destination: str) -> Dict[str, List[Dict[str, Any]]]:
    key = destination.strip().lower()
    cached = _CACHE.get(key)
    now = time.time()
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    bundle: Dict[str, List[Dict[str, Any]]] = {"spots": [], "hotels": []}
    try:
        geo = _geocode(destination)
        if not geo:
            logger.info(f"OpenStreetMap has no match for {destination}")
        else:
            bundle = _search(geo)
            logger.info(
                f"OpenStreetMap returned {len(bundle['spots'])} places and {len(bundle['hotels'])} hotels for {destination}"
            )
    except requests.RequestException as exc:
        logger.warning(f"OpenStreetMap lookup failed for {destination}: {exc}")

    cached_at = now if bundle["spots"] or bundle["hotels"] else now - _CACHE_TTL_SECONDS + 60
    _CACHE[key] = (cached_at, bundle)
    return bundle


def _geocode(destination: str) -> Optional[Dict[str, Any]]:
    queries = [destination]
    if destination not in ABROAD:
        queries.insert(0, f"{destination}, India")
    for query in queries:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1},
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()
        if rows:
            row = rows[0]
            south, north, west, east = (float(value) for value in row["boundingbox"])
            address = row.get("address") or {}
            return {
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "south": south,
                "north": north,
                "west": west,
                "east": east,
                "name": row.get("name") or destination,
                "kind": row.get("addresstype") or row.get("type") or "",
                "state": address.get("state") or "",
                "country": address.get("country") or "",
            }
        time.sleep(1)
    return None


def _search(geo: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    jobs = [(term, tag, category) for term, tag, category in SPOT_QUERIES]
    jobs.append((HOTEL_QUERY[0], HOTEL_QUERY[1], "hotel"))
    found: List[Tuple[str, Dict[str, Any]]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_photon, term, tag, geo): category for term, tag, category in jobs}
        for future in as_completed(futures):
            category = futures[future]
            try:
                rows = future.result()
            except requests.RequestException as exc:
                logger.warning(f"OpenStreetMap place search failed: {exc}")
                continue
            for row in rows:
                found.append((category, row))

    spots = []
    hotels = []
    seen = set()
    for category, row in sorted(found, key=lambda item: item[1]["score"], reverse=True):
        name = row["name"]
        if name.casefold() in seen:
            continue
        seen.add(name.casefold())
        if category == "hotel":
            if len(hotels) < 4:
                hotels.append({"name": name, "area": row["area"]})
            continue
        if len(spots) < 8:
            spots.append({
                "name": name,
                "category": category,
                "time_slot": "Morning",
                "estimated_cost": _cost(category),
                "source": "openstreetmap",
            })
    for index, spot in enumerate(spots):
        spot["time_slot"] = ("Morning", "Afternoon", "Evening")[index % 3]
    return {"spots": spots, "hotels": hotels}


def _photon(term: str, osm_tag: str, geo: Dict[str, Any]) -> List[Dict[str, Any]]:
    response = requests.get(
        PHOTON_URL,
        params={
            "q": term,
            "lat": geo["lat"],
            "lon": geo["lon"],
            "bbox": f"{geo['west']},{geo['south']},{geo['east']},{geo['north']}",
            "osm_tag": osm_tag,
            "limit": 8,
            "lang": "en",
        },
        headers=HEADERS,
        timeout=12,
    )
    response.raise_for_status()
    rows = []
    for feature in response.json().get("features") or []:
        props = feature.get("properties") or {}
        name = (props.get("name") or "").strip()
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if not _usable_name(name) or not _in_place(props, coordinates, geo):
            continue
        area = props.get("district") or props.get("city") or props.get("county") or props.get("state") or ""
        rows.append({
            "name": name,
            "area": area,
            "score": _score(name, props.get("osm_value") or ""),
        })
    return rows


def _usable_name(name: str) -> bool:
    folded = " ".join(name.casefold().split())
    if folded in GENERIC_NAMES or len(folded) < 4:
        return False
    words = folded.split()
    filler = {"hotel", "the", "inn", "lodge", "guest", "house", "rupees", "rs"}
    proper = [
        word for word in words
        if word not in filler and len("".join(ch for ch in word if ch.isalpha())) >= 3
    ]
    if words and words[0] in {"hotel", "lodge"} and not proper:
        return False
    return True


def _in_place(props: Dict[str, str], coordinates: List[float], geo: Dict[str, Any]) -> bool:
    if len(coordinates) < 2:
        return False
    if geo["country"] and props.get("country") and props["country"] != geo["country"]:
        return False
    if not _inside(float(coordinates[0]), float(coordinates[1]), geo):
        return False
    feature_state = props.get("state") or ""
    if geo["kind"] in {"state", "region", "province"}:
        return bool(feature_state) and feature_state.casefold() == geo["state"].casefold()
    if geo["state"] and feature_state and feature_state.casefold() != geo["state"].casefold():
        return False
    return True


def _inside(lon: float, lat: float, geo: Dict[str, Any]) -> bool:
    pad = 0.05
    return geo["south"] - pad <= lat <= geo["north"] + pad and geo["west"] - pad <= lon <= geo["east"] + pad


def _score(name: str, osm_value: str) -> int:
    score = min(len(name), 48)
    if osm_value in {"museum", "national_park", "attraction", "beach", "fort", "palace", "marketplace"}:
        score += 12
    if len(name.split()) >= 2:
        score += 6
    return score


def _cost(category: str) -> int:
    return {"heritage": 200, "nature": 50, "shopping": 300, "sightseeing": 150}.get(category, 150)
