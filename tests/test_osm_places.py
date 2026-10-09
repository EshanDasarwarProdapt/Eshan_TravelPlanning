from unittest.mock import patch

import requests

from src.knowledge.osm_places import clear_place_cache
from src.knowledge.travel_facts import hotels_for, spots_for


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _geo():
    return [{
        "lat": "9.9312",
        "lon": "76.2673",
        "boundingbox": ["9.90", "10.05", "76.20", "76.35"],
        "osm_type": "relation",
        "osm_id": 123,
        "name": "Kochi",
        "addresstype": "city",
        "address": {"country": "India", "state": "Kerala"},
    }]


def _feature(name, lon, lat, osm_value, city="Kochi"):
    return {
        "properties": {
            "name": name,
            "osm_value": osm_value,
            "country": "India",
            "city": city,
            "state": "Kerala",
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def _get(url, **kwargs):
    if "nominatim" in url:
        return _Response(_geo())
    term = kwargs["params"]["q"]
    if term == "museum":
        features = [
            _feature("Temple", 76.26, 9.96, "museum"),
            _feature("Kerala Folklore Museum", 76.30, 9.97, "museum"),
        ]
    elif term == "beach":
        features = [_feature("Fort Kochi Beach", 76.24, 9.96, "beach")]
    elif term == "hotel":
        features = [_feature("Brunton Boatyard", 76.24, 9.96, "hotel", city="Fort Kochi")]
    else:
        features = []
    return _Response({"features": features})


def test_catalog_city_keeps_local_places():
    clear_place_cache()
    with patch("src.knowledge.osm_places.requests.get") as get_mock:
        names = [spot["name"] for spot in spots_for("Goa")]
        get_mock.assert_not_called()
    assert any("Baga" in name for name in names)


def test_unknown_city_uses_openstreetmap_names():
    clear_place_cache()
    with patch("src.knowledge.osm_places.requests.get", side_effect=_get):
        spots = spots_for("Kochi")
        hotels = hotels_for("Kochi", 4000)
    names = [spot["name"] for spot in spots]
    assert "Kerala Folklore Museum" in names
    assert "Fort Kochi Beach" in names
    assert "Temple" not in names
    assert all("Old-town" not in name for name in names)
    assert spots[0]["source"] == "openstreetmap"
    assert hotels[0]["name"] == "Brunton Boatyard"
    assert hotels[0]["area"] == "Fort Kochi"
    assert "Nightly rate is an estimate" in hotels[0]["features"]


def test_openstreetmap_outage_keeps_generic_places():
    clear_place_cache()
    with patch("src.knowledge.osm_places.requests.get", side_effect=requests.Timeout("down")):
        names = [spot["name"] for spot in spots_for("Assam")]
    assert any(name.startswith("Old-town walking tour") for name in names)
