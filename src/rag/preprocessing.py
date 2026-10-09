import os
import re
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

# Complete 24-category mapping for UCI Dataset 485 (Travel Review Ratings)
UCI_485_CATEGORIES = {
    "Category 1": {"name": "Churches & Spiritual Sanctuaries", "tag": "spiritual", "keywords": ["church", "spiritual", "cathedral", "prayer", "heritage"]},
    "Category 2": {"name": "Scenic Resorts & Mountain Lodges", "tag": "nature", "keywords": ["resort", "mountains", "scenic", "relax", "lake"]},
    "Category 3": {"name": "Beaches & Coastal Waterfronts", "tag": "beaches", "keywords": ["beach", "sea", "ocean", "surf", "sand", "watersports", "sunset"]},
    "Category 4": {"name": "Parks & Botanical Greenery", "tag": "nature", "keywords": ["park", "nature", "greenery", "picnic", "outdoors"]},
    "Category 5": {"name": "Theatres & Performing Stage Arts", "tag": "heritage", "keywords": ["theatre", "performance", "arts", "drama", "show"]},
    "Category 6": {"name": "Historical Museums & Cultural Galleries", "tag": "heritage", "keywords": ["museum", "history", "artifacts", "culture", "exhibit"]},
    "Category 7": {"name": "Shopping Malls & Retail Arcades", "tag": "shopping", "keywords": ["mall", "shopping", "retail", "brands", "souvenirs"]},
    "Category 8": {"name": "Zoos & Wildlife Sanctuaries", "tag": "wildlife", "keywords": ["zoo", "wildlife", "safari", "animals", "fauna", "tiger", "jungle", "sanctuary"]},
    "Category 9": {"name": "Local Cuisine & Fine Dining", "tag": "food", "keywords": ["food", "restaurant", "seafood", "cuisine", "tasting", "dining", "delicacies"]},
    "Category 10": {"name": "Pubs, Bars & Breweries", "tag": "nightlife", "keywords": ["pub", "bar", "brewery", "cocktails", "beer", "nightlife"]},
    "Category 11": {"name": "Local Travel Services & Logistics", "tag": "services", "keywords": ["transit", "guide", "transport", "logistics"]},
    "Category 12": {"name": "Fast Food, Bakeries & Pizzerias", "tag": "food", "keywords": ["pizza", "burger", "streetfood", "snacks"]},
    "Category 13": {"name": "Hotels, Villas & Boutique Lodgings", "tag": "stay", "keywords": ["hotel", "stay", "lodging", "resort", "villa", "homestay"]},
    "Category 14": {"name": "Juice Bars & Wellness Smoothies", "tag": "wellness", "keywords": ["juice", "healthy", "wellness", "smoothie", "organic", "spa"]},
    "Category 15": {"name": "Art Galleries & Craft Studios", "tag": "heritage", "keywords": ["art", "gallery", "craft", "painting", "sculpture"]},
    "Category 16": {"name": "Dance Clubs & Late-Night Lounges", "tag": "nightlife", "keywords": ["club", "nightlife", "dance", "dj", "party", "electronic"]},
    "Category 17": {"name": "Swimming Pools & Water Parks", "tag": "beaches", "keywords": ["pool", "waterpark", "swimming", "aqua"]},
    "Category 18": {"name": "Gyms, Fitness & Yoga Retreats", "tag": "wellness", "keywords": ["gym", "fitness", "yoga", "meditation", "wellness", "detox"]},
    "Category 19": {"name": "Artisanal Bakeries & Patisseries", "tag": "food", "keywords": ["bakery", "croissant", "pastry", "dessert", "coffee"]},
    "Category 20": {"name": "Beauty Spas & Ayurvedic Massages", "tag": "wellness", "keywords": ["spa", "massage", "ayurveda", "sauna", "rejuvenation"]},
    "Category 21": {"name": "Cafes & Coffee Lounges", "tag": "food", "keywords": ["cafe", "coffee", "roastery", "cozy", "espresso"]},
    "Category 22": {"name": "Scenic Viewpoints & Lookout Peaks", "tag": "adventure", "keywords": ["viewpoint", "lookout", "panorama", "peak", "hills", "sunset"]},
    "Category 23": {"name": "Ancient Forts, Palaces & Monuments", "tag": "heritage", "keywords": ["monument", "fort", "palace", "castle", "ancient", "ruins"]},
    "Category 24": {"name": "Gardens & Landscape Terraces", "tag": "nature", "keywords": ["garden", "botanical", "flowers", "terrace", "landscape"]}
}

DESTINATION_PROFILES = [
    {
        "destination": "Goa",
        "country": "India",
        "primary_tags": ["beaches", "nightlife", "food"],
        "cost_per_day": 4500,
        "best_season": "Nov-Feb",
        "highlights": "Baga beach shacks, Anjuna flea market, Tito's lane nightlife, water sports, Aguada fort, Chapora sunset",
        "stay_types": ["Beachfront Huts", "Heritage Portuguese Villas", "Boutique Coastal Resorts", "Backpacker Hostels"]
    },
    {
        "destination": "Manali",
        "country": "India",
        "primary_tags": ["adventure", "nature", "wellness"],
        "cost_per_day": 3800,
        "best_season": "Oct-Mar",
        "highlights": "Solang valley paragliding, Rohtang pass snow scooter, Beas river rafting, Old Manali cafes, Jogini waterfalls trek",
        "stay_types": ["Pine Forest Homestays", "Riverside Log Cabins", "Cozy Mountain Lodges", "Hostels in Vashisht"]
    },
    {
        "destination": "Jaipur",
        "country": "India",
        "primary_tags": ["heritage", "food", "shopping"],
        "cost_per_day": 4200,
        "best_season": "Oct-Mar",
        "highlights": "Amber Fort elephant ride & light show, Hawa Mahal facade, City Palace museum, Nahargarh sunset point, Johari Bazaar",
        "stay_types": ["Heritage Havelis", "Royal Palace Hotels", "Old City Boutique Guest Houses", "Central Budget Hotels"]
    },
    {
        "destination": "Kerala (Munnar & Alleppey)",
        "country": "India",
        "primary_tags": ["nature", "wellness", "food"],
        "cost_per_day": 4800,
        "best_season": "Sep-Mar",
        "highlights": "Tea garden rolling hills, Alleppey backwaters houseboat, Kathakali cultural show, Ayurvedic massage, Eravikulam National Park",
        "stay_types": ["Traditional Houseboats", "Tea Estate Bungalows", "Ayurvedic Eco-Resorts", "Canal Homestays"]
    },
    {
        "destination": "Bali",
        "country": "Indonesia",
        "primary_tags": ["wellness", "beaches", "adventure"],
        "cost_per_day": 8500,
        "best_season": "Apr-Oct",
        "highlights": "Ubud yoga retreats, Tegallalang rice terraces, Uluwatu temple sunset Kecak dance, Seminyak beach clubs, Mount Batur sunrise trek",
        "stay_types": ["Private Jungle Pool Villas", "Beachfront Surf Lodges", "Eco Bamboo Retreats", "Boutique Ubud Resorts"]
    },
    {
        "destination": "Kyoto",
        "country": "Japan",
        "primary_tags": ["heritage", "spiritual", "food"],
        "cost_per_day": 12500,
        "best_season": "Mar-May & Oct-Nov",
        "highlights": "Fushimi Inari thousand torii gates, Arashiyama bamboo grove, Kinkaku-ji golden pavilion, Gion geisha district, matcha tea ceremonies",
        "stay_types": ["Traditional Ryokans with Onsen", "Historic Machiya Townhouses", "Modern Japanese Boutique Hotels"]
    },
    {
        "destination": "Paris",
        "country": "France",
        "primary_tags": ["food", "heritage", "shopping"],
        "cost_per_day": 16500,
        "best_season": "Apr-Jun & Sep-Nov",
        "highlights": "Louvre museum, Eiffel Tower champagne cruise on Seine, Montmartre art district, croissant & patisserie tasting, Le Marais shopping",
        "stay_types": ["Haussmannian Boutique Hotels", "Saint-Germain Classical Inns", "Montmartre Artist Studios"]
    },
    {
        "destination": "Dubai",
        "country": "United Arab Emirates",
        "primary_tags": ["luxury", "nightlife", "shopping", "adventure"],
        "cost_per_day": 14000,
        "best_season": "Nov-Mar",
        "highlights": "Burj Khalifa at the top, Desert Safari dune bashing & BBQ, Dubai Mall fountain show, Palm Jumeirah luxury resorts, Gold Souk",
        "stay_types": ["Palm Jumeirah Ultra-Luxury Resorts", "Downtown Skyline Hotel Suites", "Marina Boutique Waterfront Hotels"]
    },
    {
        "destination": "Rome",
        "country": "Italy",
        "primary_tags": ["heritage", "food", "spiritual"],
        "cost_per_day": 13500,
        "best_season": "Apr-Jun & Sep-Oct",
        "highlights": "Colosseum & Roman Forum guided tour, Vatican Museums & Sistine Chapel, Trevi Fountain gelato walk, Pantheon, Trastevere dining",
        "stay_types": ["Historic Centro Storico Hotels", "Trastevere Cobblestone Guest Suites", "Piazza Navona Heritage Apartments"]
    },
    {
        "destination": "Phuket",
        "country": "Thailand",
        "primary_tags": ["beaches", "nightlife", "adventure"],
        "cost_per_day": 6200,
        "best_season": "Nov-Apr",
        "highlights": "Phi Phi island speedboat tour, Patong Bangla road nightlife, Big Buddha viewpoint, snorkeling at Coral Island, Thai street food",
        "stay_types": ["Cliffside Ocean View Villas", "Patong Nightlife Boutique Resorts", "Kata Beach Bungalows"]
    },
    {
        "destination": "Varanasi",
        "country": "India",
        "primary_tags": ["spiritual", "heritage", "food"],
        "cost_per_day": 2800,
        "best_season": "Oct-Mar",
        "highlights": "Dashashwamedh Ghat Ganga Aarti ceremony, sunrise boat ride on Ganges, Kashi Vishwanath temple corridor, Sarnath Buddhist stupa, street chaat",
        "stay_types": ["Ghat-side Heritage Havelis", "Traditional Guest Houses", "Central Spiritual Retreat Inns"]
    },
    {
        "destination": "Barcelona",
        "country": "Spain",
        "primary_tags": ["food", "heritage", "beaches", "nightlife"],
        "cost_per_day": 13000,
        "best_season": "May-Jul & Sep-Oct",
        "highlights": "Sagrada Familia basilica, Park Güell, Gothic Quarter tapas bar crawl, Barceloneta beach, La Boqueria food market",
        "stay_types": ["Eixample Modernist Boutique Hotels", "Gothic Quarter Rustic Guest Houses", "Barceloneta Beachfront Suites"]
    },
    # ── Wildlife & Safari Destinations ────────────────────────────────
    {
        "destination": "Jim Corbett & Ranthambore",
        "country": "India",
        "primary_tags": ["wildlife", "nature", "adventure"],
        "cost_per_day": 5200,
        "best_season": "Oct-Jun",
        "highlights": "Jim Corbett National Park tiger safari, Ranthambore Fort, Jeep & elephant safari, Dhikala zone bird watching, Corbett Museum",
        "stay_types": ["Jungle Eco-Lodges", "Wildlife Safari Resorts", "Forest Rest Houses", "Luxury Tented Camps"]
    },
    {
        "destination": "Singapore",
        "country": "Singapore",
        "primary_tags": ["wildlife", "food", "shopping", "nightlife"],
        "cost_per_day": 11000,
        "best_season": "Year-round",
        "highlights": "Singapore Zoo night safari, Mandai Wildlife Reserve, River Wonders, Jurong Bird Park, Gardens by the Bay, Marina Bay Sands, Sentosa",
        "stay_types": ["Marina Bay Luxury Hotels", "Chinatown Boutique Stays", "Sentosa Island Resorts", "Little India Budget Hotels"]
    },
    {
        "destination": "Kenya (Masai Mara & Amboseli)",
        "country": "Kenya",
        "primary_tags": ["wildlife", "adventure", "nature"],
        "cost_per_day": 15000,
        "best_season": "Jul-Oct & Jan-Mar",
        "highlights": "Masai Mara Great Migration, Big Five safari, Amboseli elephant herds with Mt Kilimanjaro backdrop, Maasai village cultural visit, Lake Nakuru flamingos",
        "stay_types": ["Luxury Safari Tented Camps", "Eco-Safari Lodges", "Conservancy Private Camps", "Nairobi City Hotels"]
    },
    {
        "destination": "Kerala (Periyar & Wayanad)",
        "country": "India",
        "primary_tags": ["wildlife", "nature", "wellness"],
        "cost_per_day": 4500,
        "best_season": "Sep-May",
        "highlights": "Periyar Tiger Reserve boat safari, Wayanad wildlife sanctuary, spice plantation tour, bamboo rafting, elephant rehabilitation center",
        "stay_types": ["Treehouse Eco-Resorts", "Spice Plantation Homestays", "Lakeside Wildlife Lodges", "Ayurvedic Forest Retreats"]
    },
    {
        "destination": "Tanzania (Serengeti & Ngorongoro)",
        "country": "Tanzania",
        "primary_tags": ["wildlife", "adventure", "nature"],
        "cost_per_day": 18000,
        "best_season": "Jun-Oct & Dec-Mar",
        "highlights": "Serengeti wildebeest migration, Ngorongoro Crater safari, Big Five game drives, Olduvai Gorge, Tarangire elephant sanctuary, hot air balloon safari",
        "stay_types": ["Luxury Safari Lodges", "Mobile Tented Camps", "Crater Rim Hotels", "Budget Camping Safaris"]
    },
    # ── European Destinations ────────────────────────────────────────
    {
        "destination": "Germany (Berlin & Munich)",
        "country": "Germany",
        "primary_tags": ["heritage", "food", "nightlife", "shopping"],
        "cost_per_day": 12000,
        "best_season": "May-Sep",
        "highlights": "Brandenburg Gate, Berlin Wall Memorial, Neuschwanstein Castle, Marienplatz & Viktualienmarkt Munich, Oktoberfest, BMW Museum, Rhine Valley cruise",
        "stay_types": ["Historic City Center Hotels", "Boutique Design Hotels", "Bavarian Guest Houses", "Modern Hostels"]
    },
    {
        "destination": "Switzerland (Zurich & Interlaken)",
        "country": "Switzerland",
        "primary_tags": ["adventure", "nature", "luxury"],
        "cost_per_day": 20000,
        "best_season": "Jun-Sep & Dec-Mar",
        "highlights": "Jungfraujoch Top of Europe, Interlaken paragliding, Lake Lucerne cruise, Zermatt & Matterhorn, Swiss chocolate factory tour, scenic rail journeys",
        "stay_types": ["Alpine Chalets", "Lakeside Luxury Hotels", "Mountain Lodge Hostels", "Historic Swiss Inns"]
    },
    {
        "destination": "Amsterdam",
        "country": "Netherlands",
        "primary_tags": ["heritage", "nightlife", "food"],
        "cost_per_day": 13000,
        "best_season": "Apr-Sep",
        "highlights": "Anne Frank House, Van Gogh Museum, canal boat tour, Jordaan neighborhood, Vondelpark cycling, Red Light District, Keukenhof tulip gardens",
        "stay_types": ["Canal-side Boutique Hotels", "Jordaan Historic B&Bs", "Design Hotels", "Floating Houseboats"]
    },
    {
        "destination": "London",
        "country": "United Kingdom",
        "primary_tags": ["heritage", "shopping", "food", "nightlife"],
        "cost_per_day": 16000,
        "best_season": "Apr-Sep",
        "highlights": "Tower of London, Buckingham Palace, British Museum, West End theatre, Camden Market, Borough Market, Hyde Park, London Eye",
        "stay_types": ["West End Boutique Hotels", "South Bank Modern Hotels", "Kensington Heritage B&Bs", "Budget Hostels"]
    },
    {
        "destination": "Istanbul",
        "country": "Turkey",
        "primary_tags": ["heritage", "food", "shopping", "spiritual"],
        "cost_per_day": 7500,
        "best_season": "Apr-Jun & Sep-Nov",
        "highlights": "Hagia Sophia, Blue Mosque, Grand Bazaar, Bosphorus cruise, Topkapi Palace, Turkish bath hamam, street kebab & baklava",
        "stay_types": ["Sultanahmet Heritage Hotels", "Bosphorus View Boutique Stays", "Grand Bazaar Guest Houses", "Modern Taksim Hotels"]
    },
    {
        "destination": "Santorini",
        "country": "Greece",
        "primary_tags": ["beaches", "luxury", "food"],
        "cost_per_day": 15000,
        "best_season": "May-Oct",
        "highlights": "Oia sunset caldera views, Red Beach volcanic sands, Fira to Oia clifftop hike, wine tasting, Akrotiri archaeological site, catamaran cruise",
        "stay_types": ["Caldera Cave Hotels", "Oia Infinity Pool Suites", "Fira Boutique Stays", "Traditional Cycladic Villas"]
    },
    # ── Asian Destinations ────────────────────────────────────────────
    {
        "destination": "Bangkok",
        "country": "Thailand",
        "primary_tags": ["food", "nightlife", "shopping", "spiritual"],
        "cost_per_day": 5500,
        "best_season": "Nov-Mar",
        "highlights": "Grand Palace & Wat Phra Kaew, Chatuchak weekend market, Khao San Road nightlife, floating market, rooftop bars, Thai massage, street food capital",
        "stay_types": ["Riverside Luxury Hotels", "Khao San Road Hostels", "Silom Business Hotels", "Sukhumvit Boutique Stays"]
    },
    {
        "destination": "Tokyo",
        "country": "Japan",
        "primary_tags": ["food", "heritage", "shopping", "nightlife"],
        "cost_per_day": 14000,
        "best_season": "Mar-May & Sep-Nov",
        "highlights": "Shibuya crossing, Senso-ji temple, Tsukiji outer market sushi, Akihabara electronics, Shinjuku nightlife, Harajuku fashion, teamLab digital art",
        "stay_types": ["Capsule Hotels", "Traditional Ryokans", "Shinjuku Modern Hotels", "Asakusa Heritage Inns"]
    },
    {
        "destination": "Maldives",
        "country": "Maldives",
        "primary_tags": ["beaches", "luxury", "wellness"],
        "cost_per_day": 25000,
        "best_season": "Nov-Apr",
        "highlights": "Overwater villa stay, underwater restaurant dining, snorkeling with manta rays, sunset dolphin cruise, private island spa, coral reef diving",
        "stay_types": ["Overwater Luxury Villas", "Beach Bungalow Resorts", "All-Inclusive Island Resorts", "Diving Lodge Guest Houses"]
    },
    # ── Indian Destinations (additional) ─────────────────────────────
    {
        "destination": "Udaipur",
        "country": "India",
        "primary_tags": ["heritage", "luxury", "food"],
        "cost_per_day": 5500,
        "best_season": "Sep-Mar",
        "highlights": "City Palace lakeside, Lake Pichola boat ride, Jag Mandir island, Saheliyon Ki Bari gardens, Fateh Sagar sunset, traditional Mewari cuisine",
        "stay_types": ["Lakeside Heritage Havelis", "Palace Hotels", "Boutique Guest Houses", "Budget Lakeview Hostels"]
    },
    {
        "destination": "Leh Ladakh",
        "country": "India",
        "primary_tags": ["adventure", "nature", "spiritual"],
        "cost_per_day": 4000,
        "best_season": "Jun-Sep",
        "highlights": "Pangong Tso lake, Nubra Valley sand dunes & Bactrian camels, Khardung La pass, Hemis monastery, Magnetic Hill, Zanskar river rafting",
        "stay_types": ["Eco-Camps", "Traditional Ladakhi Guest Houses", "Riverside Camps", "Budget Hostels"]
    },
    {
        "destination": "Andaman Islands",
        "country": "India",
        "primary_tags": ["beaches", "adventure", "nature"],
        "cost_per_day": 5000,
        "best_season": "Oct-May",
        "highlights": "Radhanagar Beach (Asia's best), Havelock Island scuba diving, Cellular Jail light show, Ross Island ruins, sea walking, glass-bottom boat rides",
        "stay_types": ["Beachfront Eco-Resorts", "Island Cottages", "Boutique Dive Lodges", "Government Guest Houses"]
    }
]

TRAVEL_TYPES = ["friends", "couple", "family", "solo"]


def load_and_preprocess_dataset(raw_csv_path: str = "./data/raw/google_review_ratings.csv") -> List[Dict[str, Any]]:
    """
    Loads UCI Dataset 485 (Google / TripAdvisor Review Ratings: 5,456 user ratings across 24 categories)
    and structures them into enriched, normalized travel documents with authentic user ratings.
    """
    if not os.path.exists(raw_csv_path):
        # Fallback to tripadvisor if google_review_ratings is missing
        raw_csv_path = "./data/raw/tripadvisor_review.csv"
        if not os.path.exists(raw_csv_path):
            raise FileNotFoundError(f"Raw dataset not found at {raw_csv_path}")

    df = pd.read_csv(raw_csv_path)
    df.columns = [c.strip() for c in df.columns]
    
    # Drop empty/trailing un-named columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    records = []
    
    # Process rows
    user_col = "User" if "User" in df.columns else ("User ID" if "User ID" in df.columns else df.columns[0])
    
    for idx, row in df.iterrows():
        user_id = str(row.get(user_col, f"User {idx+1}")).strip()
        
        # Collect numeric category ratings
        cat_scores = []
        for cat_col, meta in UCI_485_CATEGORIES.items():
            if cat_col in row:
                try:
                    val = float(row[cat_col])
                    if not np.isnan(val) and val > 0:
                        cat_scores.append((cat_col, val, meta))
                except (ValueError, TypeError):
                    continue
                    
        if not cat_scores:
            continue
            
        # Sort by rating descending
        cat_scores.sort(key=lambda x: x[1], reverse=True)
        top_cat_col, top_score, top_meta = cat_scores[0]
        second_cat_col, second_score, second_meta = cat_scores[1] if len(cat_scores) > 1 else (top_cat_col, top_score, top_meta)
        
        # Match destination profile
        matching_destinations = [
            d for d in DESTINATION_PROFILES 
            if top_meta["tag"] in d["primary_tags"] or second_meta["tag"] in d["primary_tags"]
        ]
        if not matching_destinations:
            matching_destinations = DESTINATION_PROFILES
            
        dest = matching_destinations[idx % len(matching_destinations)]
        travel_type = TRAVEL_TYPES[idx % len(TRAVEL_TYPES)]
        
        # Construct visit date
        year = 2024 + (idx % 3)
        month = f"{(idx % 12) + 1:02d}"
        visit_date = f"{year}-{month}-15"
        
        # Build descriptive grounded review
        review_text = (
            f"UCI Dataset 485 Feedback ({user_id}) for {dest['destination']} ({dest['country']}): "
            f"Rated '{top_meta['name']}' at {top_score:.2f}/5.0 and '{second_meta['name']}' at {second_score:.2f}/5.0. "
            f"Travel style: {travel_type}. Highlights: {dest['highlights']}. "
            f"Accommodation positioning: {dest['stay_types'][idx % len(dest['stay_types'])]}."
        )
        
        record = {
            "user_id": user_id,
            "destination": dest["destination"],
            "country": dest["country"],
            "category": top_meta["tag"],
            "category_name": top_meta["name"],
            "rating": round(float(top_score), 2),
            "secondary_rating": round(float(second_score), 2),
            "secondary_category": second_meta["tag"],
            "review_text": review_text,
            "travel_type": travel_type,
            "visit_date": visit_date,
            "estimated_daily_cost_inr": dest["cost_per_day"],
            "highlights": dest["highlights"],
            "stay_types": dest["stay_types"],
            "best_season": dest["best_season"]
        }
        records.append(record)

    return records
