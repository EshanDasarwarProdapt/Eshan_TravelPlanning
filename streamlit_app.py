"""Streamlit client for Waypoint. The React app is unchanged."""
import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

API = os.environ.get("WAYPOINT_API", "http://127.0.0.1:8000").rstrip("/")

STARTERS = [
    "Best time to visit Assam?",
    "Flight or train on a tight budget?",
    "How should I split ₹40,000 for 5 days?",
]


def inr(amount: Optional[float]) -> str:
    if amount is None:
        return ""
    return f"₹{int(amount):,}"


def api(method: str, path: str, body: Optional[Dict[str, Any]] = None, timeout: int = 120) -> Dict[str, Any]:
    response = requests.request(method, f"{API}{path}", json=body, timeout=timeout)
    if not response.ok:
        detail = response.text
        try:
            payload = response.json()
            detail = payload.get("detail") or detail
        except ValueError:
            pass
        if isinstance(detail, list):
            detail = "; ".join(str(item) for item in detail)
        raise RuntimeError(str(detail) or f"Server responded with status {response.status_code}")
    return response.json()


def init_state() -> None:
    st.session_state.setdefault("page", "Explore")
    st.session_state.setdefault("step", "where")
    st.session_state.setdefault("options", None)
    st.session_state.setdefault("transport_mode", "")
    st.session_state.setdefault("hotel_name", "")
    st.session_state.setdefault("built", None)
    st.session_state.setdefault("open_place", None)
    st.session_state.setdefault("recommendation", None)
    st.session_state.setdefault("dest_input", "")
    st.session_state.setdefault("origin_input", "")
    st.session_state.setdefault("trip_days", 3)
    st.session_state.setdefault("travelers", 2)
    st.session_state.setdefault("stay_days", 3)
    st.session_state.setdefault("preferences", "")
    st.session_state.setdefault("chat", [{
        "role": "assistant",
        "content": "Ask me anything about a trip: cities, seasons, budgets, trains, flights, or hotels. For a full day-by-day plan, use Plan.",
    }])


def health_line() -> str:
    try:
        data = api("GET", "/health", timeout=8)
        return f"API online · {data.get('database_records_indexed', 0)} records · {data.get('llm_status', '')}"
    except Exception as exc:
        return f"API not reachable at {API}. {exc}"


def send_chat(message: str) -> None:
    history = st.session_state.chat[-8:]
    st.session_state.chat.append({"role": "user", "content": message})
    reply = api("POST", "/api/v1/chat", {"message": message, "history": history}, timeout=40)
    st.session_state.chat.append({"role": "assistant", "content": reply.get("reply") or ""})


def render_chat() -> None:
    if st.session_state.pop("clear_chat_draft", False):
        st.session_state.chat_draft = ""
    st.subheader("Travel chat")
    st.caption("Questions about trips, not a full itinerary")
    for turn in st.session_state.chat[-8:]:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])
    for starter in STARTERS:
        if st.button(starter, key=f"starter-{starter}"):
            with st.spinner("Thinking…"):
                try:
                    send_chat(starter)
                except Exception as exc:
                    st.session_state.chat.append({"role": "assistant", "content": str(exc)})
            st.rerun()
    draft = st.text_input("Ask a travel question", key="chat_draft")
    if st.button("Send", disabled=not draft.strip()):
        with st.spinner("Thinking…"):
            try:
                send_chat(draft.strip())
                st.session_state.clear_chat_draft = True
            except Exception as exc:
                st.session_state.chat.append({"role": "assistant", "content": str(exc)})
        st.rerun()


def render_header() -> None:
    brand, explore, plan, status = st.columns([3, 1, 1, 2])
    brand.markdown("## WAYPOINT")
    brand.caption("Travel Intelligence & Multi-Agent Planning")
    if explore.button("Explore", type="primary" if st.session_state.page == "Explore" else "secondary", use_container_width=True):
        st.session_state.page = "Explore"
        st.rerun()
    if plan.button("Plan", type="primary" if st.session_state.page == "Plan" else "secondary", use_container_width=True):
        st.session_state.page = "Plan"
        st.rerun()
    status.caption(health_line())
    st.divider()


def open_planner(destination: str) -> None:
    st.session_state.page = "Plan"
    st.session_state.step = "where"
    st.session_state.options = None
    st.session_state.built = None
    st.session_state.transport_mode = ""
    st.session_state.hotel_name = ""
    st.session_state.dest_input = destination
    st.rerun()


def place_label(place: Dict[str, Any]) -> str:
    return place.get("display_name") or place.get("destination") or "Place"


def render_explore() -> None:
    st.title("Trips rated by past travelers")
    try:
        catalog = api("GET", "/api/v1/explore", timeout=30)
    except Exception as exc:
        st.error(str(exc))
        return
    st.caption(
        f"Each score is the average of traveler records in the database ({catalog.get('record_count', 0)} records). "
        "Places with no records are shown without a rating. Use Plan when you want to choose a hotel, a route, and a final cost."
    )

    with st.form("match_form"):
        preferences = st.text_input("What kind of trip?", value="5 day trip for beaches, sightseeing, and local food")
        budget = st.text_input("Trip budget in INR, optional", placeholder="40000")
        submitted = st.form_submit_button("Match similar travelers")
    if submitted:
        parsed = int(budget) if budget.strip().isdigit() else None
        try:
            st.session_state.recommendation = api(
                "POST",
                "/api/v1/explore/recommend",
                {"preferences": preferences, "budget": parsed},
            )
        except Exception as exc:
            st.error(str(exc))

    match = st.session_state.recommendation
    if match:
        st.subheader("Best match")
        st.write(match.get("summary") or "")
        rows = match.get("comparison") or []
        if rows:
            st.dataframe(
                [
                    {
                        "Destination": row["destination"],
                        "Rating": "Not rated" if row.get("average_rating") is None else f"{row['average_rating']:.2f} / 5",
                        "Similar travelers": row.get("similar_travelers"),
                        "Stored trip cost": f"{inr(row.get('trip_cost_inr'))} for {row.get('days')} days",
                        "Budget": "Inside" if row.get("within_budget") else "Over",
                    }
                    for row in rows
                ],
                hide_index=True,
                use_container_width=True,
            )
        recommended = match.get("recommended")
        if recommended:
            if st.button(f"Plan {recommended['destination']}"):
                open_planner(recommended["destination"])

    for theme in catalog.get("themes") or []:
        st.subheader(theme["title"])
        places = theme.get("places") or []
        columns = st.columns(3)
        for index, place in enumerate(places):
            label = place_label(place)
            with columns[index % 3]:
                if place.get("available"):
                    rating = place.get("average_rating")
                    st.markdown(f"**{label}**")
                    st.write(f"{rating:.2f} / 5 from {place.get('traveler_count')} travelers" if rating is not None else "")
                else:
                    st.markdown(f"**{label}**")
                    st.write(place.get("note") or "")
                if place.get("trip_cost_inr"):
                    st.caption(f"{place.get('days')} days from Delhi · about {inr(place.get('trip_cost_inr'))} a person")
                if st.button("Open", key=f"open-{theme['id']}-{label}"):
                    st.session_state.open_place = place
                    st.rerun()

    opened = st.session_state.open_place
    if opened:
        st.divider()
        st.subheader(place_label(opened))
        st.write(opened.get("note") or "")
        if opened.get("price_note"):
            st.write(opened["price_note"])
        if opened.get("available"):
            stays = ", ".join(opened.get("stay_types") or [])
            st.write(f"Stored stays: {stays}. Season on the records: {opened.get('best_season') or ''}.")
            for day in opened.get("outline") or []:
                st.markdown(f"**Day {day.get('day_number')}**")
                st.write(day.get("sightseeing") or "")
                st.write(day.get("food") or "")
                st.caption(f"Stay recorded for this place: {day.get('stay')}")
            if st.button("Plan this trip"):
                open_planner(opened.get("destination") or place_label(opened))


def load_options() -> None:
    destination = st.session_state.dest_input.strip()
    origin = st.session_state.origin_input.strip()
    data = api("POST", "/api/v1/trip-options", {"destination": destination, "origin": origin}, timeout=90)
    st.session_state.options = data
    fastest = next((item for item in data.get("transport") or [] if item.get("fastest")), None)
    if fastest is None and data.get("transport"):
        fastest = data["transport"][0]
    st.session_state.transport_mode = "local" if data.get("local_only") or not fastest else fastest["mode"]
    st.session_state.hotel_name = ""
    st.session_state.step = "hotel" if data.get("local_only") or not data.get("transport") else "route"
    st.session_state.built = None


def generate_plan() -> None:
    options = st.session_state.options
    stay_days = int(st.session_state.stay_days)
    trip_days = int(st.session_state.trip_days)
    if stay_days > trip_days:
        raise RuntimeError("Days in the city cannot be longer than the whole trip.")
    st.session_state.built = api(
        "POST",
        "/api/v1/build-trip",
        {
            "destination": options["destination"],
            "origin": options["origin"],
            "transport_mode": st.session_state.transport_mode or "local",
            "hotel_name": st.session_state.hotel_name,
            "trip_days": max(1, min(30, trip_days)),
            "travelers": max(1, min(20, int(st.session_state.travelers))),
            "stay_days": max(1, min(30, stay_days)),
            "preferences": st.session_state.preferences,
        },
        timeout=180,
    )


def render_plan_result() -> None:
    plan = st.session_state.built
    itinerary = plan.get("itinerary") or {}
    st.caption("Your plan")
    st.title(itinerary.get("trip_title") or plan.get("destination"))
    st.write(
        f"{plan.get('origin')} to {plan.get('destination')} by {plan.get('transport_mode')}. "
        f"{plan.get('travelers')} travelers, {plan.get('stay_days')} days in the city, "
        f"{plan.get('nights')} nights at {plan.get('hotel_name')}."
    )
    if st.button("Start over"):
        st.session_state.built = None
        st.session_state.step = "where"
        st.session_state.options = None
        st.rerun()
    st.subheader("Day-by-day itinerary")
    for day in itinerary.get("daily_itinerary") or []:
        with st.expander(f"Day {day.get('day_number')} · {day.get('theme')}", expanded=day.get("day_number") in (1, 2)):
            for slot in ("morning", "afternoon", "evening"):
                block = day.get(slot) or {}
                st.markdown(f"**{slot.title()}**")
                st.write(block.get("activity") or "")
                if block.get("logistics"):
                    st.caption(block["logistics"])
    st.subheader("Estimated cost")
    st.write(plan.get("note") or "")
    for line in plan.get("cost_lines") or []:
        st.write(f"**{line.get('label')}** · {inr(line.get('amount'))}")
        st.caption(line.get("detail") or "")
    st.metric("Estimated total", inr(plan.get("estimated_total")))
    for tip in itinerary.get("logistical_tips") or []:
        st.caption(tip)


def render_plan() -> None:
    if st.session_state.built:
        render_plan_result()
        return
    st.caption("Plan the trip, then see the cost")
    st.title("Where are you going?")
    st.write(
        "Start with the destination and the city you are in. Pick how you want to get there and where you want to stay, "
        "then tell us who is traveling. The estimated cost is added up at the end."
    )
    labels = ["1. Where", "2. How to get there", "3. Hotel", "4. Trip details"]
    steps = ["where", "route", "hotel", "details"]
    current = steps.index(st.session_state.step) if st.session_state.step in steps else 0
    st.write(" · ".join(f"**{label}**" if index == current else label for index, label in enumerate(labels)))

    if st.session_state.step == "where":
        st.text_input("Destination", key="dest_input", placeholder="Jaipur")
        st.text_input("Your current city", key="origin_input", placeholder="Delhi")
        ready = bool(st.session_state.get("dest_input", "").strip() and st.session_state.get("origin_input", "").strip())
        if st.button("Show ways to get there", disabled=not ready):
            with st.spinner("Looking up routes..."):
                try:
                    load_options()
                except Exception as exc:
                    st.error(str(exc))
                    return
            st.rerun()
        return

    options = st.session_state.options or {}
    if st.session_state.step == "route":
        st.subheader("How to get there")
        st.write(options.get("note") or "")
        modes = options.get("transport") or []
        labels_by_mode = {
            item["mode"]: f"{item.get('label')} · {inr(item.get('per_person_price'))} per person · {item.get('duration')}{' · Fastest' if item.get('fastest') else ''}"
            for item in modes
        }
        choice = st.radio(
            "Route",
            list(labels_by_mode),
            format_func=lambda mode: labels_by_mode[mode],
            index=max(0, list(labels_by_mode).index(st.session_state.transport_mode)) if st.session_state.transport_mode in labels_by_mode else 0,
        )
        st.session_state.transport_mode = choice
        chosen = next(item for item in modes if item["mode"] == choice)
        st.caption(f"{chosen.get('route')} · {chosen.get('stops')} · {chosen.get('booking_tip') or ''}")
        col1, col2 = st.columns(2)
        if col1.button("Back"):
            st.session_state.step = "where"
            st.rerun()
        if col2.button(f"See hotels in {options.get('destination')}"):
            st.session_state.step = "hotel"
            st.rerun()
        return

    if st.session_state.step == "hotel":
        st.subheader("Where do you want to stay?")
        st.write(f"Nightly rates are planning estimates for {options.get('destination')}. Pick the stay the rest of the trip should use.")
        if options.get("local_only"):
            st.write(options.get("note") or "")
        hotels = options.get("hotels") or []
        if not hotels:
            st.warning("No stays were found for this city yet.")
        else:
            names = [hotel["name"] for hotel in hotels]
            picked = st.radio(
                "Hotel",
                names,
                index=names.index(st.session_state.hotel_name) if st.session_state.hotel_name in names else 0,
            )
            st.session_state.hotel_name = picked
            hotel = next(item for item in hotels if item["name"] == picked)
            features = ", ".join(hotel.get("features") or [])
            st.caption(f"{hotel.get('area')} · {hotel.get('tier')} · {inr(hotel.get('nightly'))} a night. {features}")
        col1, col2 = st.columns(2)
        if col1.button("Back"):
            st.session_state.step = "route" if options.get("transport") else "where"
            st.rerun()
        if col2.button("Enter trip details", disabled=not st.session_state.hotel_name):
            st.session_state.step = "details"
            st.rerun()
        return

    st.subheader("Trip details")
    st.write(
        f"{options.get('origin')} to {options.get('destination')} by {st.session_state.transport_mode}, "
        f"staying at {st.session_state.hotel_name}."
    )
    c1, c2, c3 = st.columns(3)
    c1.number_input("Days of the trip", min_value=1, max_value=30, key="trip_days")
    c2.number_input("Travelers", min_value=1, max_value=20, key="travelers")
    c3.number_input("Days in this city", min_value=1, max_value=30, key="stay_days")
    st.caption("Hotel nights are one less than the days in the city, because the last day is checkout. A 3-day stay is 2 nights.")
    st.text_area("What do you want to do?", key="preferences", placeholder="Forts, markets, and Rajasthani food")
    col1, col2 = st.columns(2)
    if col1.button("Back"):
        st.session_state.step = "hotel"
        st.rerun()
    if col2.button("Generate the plan"):
        with st.spinner("Building the plan..."):
            try:
                generate_plan()
            except Exception as exc:
                st.error(str(exc))
                return
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Waypoint", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed")
    init_state()
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;} [data-testid='collapsedControl']{display:none;}</style>",
        unsafe_allow_html=True,
    )
    render_header()
    main_col, chat_col = st.columns([2.4, 1], gap="large")
    with main_col:
        if st.session_state.page == "Explore":
            render_explore()
        else:
            render_plan()
    with chat_col:
        render_chat()


if __name__ == "__main__":
    main()
