import csv
import os
import random

RAW_DATA_PATH = "./data/raw/travel_reviews_uci_485.csv"

DESTINATIONS_DATA = [
    {
        "destination": "Goa",
        "country": "India",
        "category": "beaches",
        "travel_types": ["friends", "couple", "solo"],
        "cost_range": (3500, 7500),
        "highlights": "Baga beach shacks, Anjuna flea market, Tito's lane nightlife, water sports, Aguada fort, Chapora sunset",
        "reviews": [
            "Incredible 5-day holiday with friends! Baga and Calangute were vibrant with amazing beach clubs and seafood. Scuba diving at Grande Island was thrilling.",
            "Great nightlife around Tito's Lane and Curlies. South Goa was much more tranquil with clean white sands at Palolem and Agonda.",
            "Fantastic beach vibes, rented scooters to explore Vagator and Chapora fort. Delicious coastal curries and chilled sunset beers.",
            "Water sports at Anjuna and parasailing were top-notch. Budget-friendly stays near Candolim made the entire trip very economical."
        ]
    },
    {
        "destination": "Goa",
        "country": "India",
        "category": "nightlife",
        "travel_types": ["friends", "solo"],
        "cost_range": (4000, 8500),
        "highlights": "Thalassa sunset lounge, Club Cubana hilltop party, silent noise party at Palolem, casino cruises on Mandovi",
        "reviews": [
            "Club Cubana on the Arpora hill was spectacular! Best DJ night and open bar experience for our friend group.",
            "Silent Noise Party at Palolem beach was uniquely memorable. Sunset cocktails at Thalassa overlooking the cliff were unforgettable.",
            "Casino pride on Mandovi river was an exciting evening. Live music shacks along Vagator kept the energy alive all night."
        ]
    },
    {
        "destination": "Manali",
        "country": "India",
        "category": "adventure",
        "travel_types": ["friends", "couple", "solo"],
        "cost_range": (3000, 6500),
        "highlights": "Solang valley paragliding, Rohtang pass snow scooter, Beas river rafting, Old Manali cafes, Jogini waterfalls trek",
        "reviews": [
            "High adrenaline paragliding in Solang Valley with stunning snow-capped peaks. River rafting in Kullu was an exhilarating rush!",
            "Old Manali has such a cozy hipster cafe culture. Trekked to Jogini Waterfall through pine forests—serene and refreshing.",
            "Rohtang Pass snow drive was breathtaking. Perfect trip for friends who love hiking, mountain biking, and evening bonfires.",
            "Budget-friendly hostels in Vashisht with natural sulfur hot spring baths. Great local trout fish and cider."
        ]
    },
    {
        "destination": "Jaipur",
        "country": "India",
        "category": "heritage",
        "travel_types": ["family", "couple", "solo"],
        "cost_range": (3500, 9000),
        "highlights": "Amber Fort elephant ride & light show, Hawa Mahal facade, City Palace museum, Nahargarh sunset point, Johari Bazaar",
        "reviews": [
            "The architecture of Amber Fort is magnificent. Audio guide gave a deep dive into Rajputana history and royal courtyards.",
            "Nahargarh Fort sunset overlooking the Pink City is iconic. Splendid Rajasthani thali at Chokhi Dhani with folk dances.",
            "Loved shopping for blue pottery and silver jewelry in Johari Bazaar. City Palace royal museum is well-maintained and majestic.",
            "A royal cultural extravaganza! Photographed Hawa Mahal at sunrise with no crowds. Exceptional hospitality across heritage havelis."
        ]
    },
    {
        "destination": "Kerala (Munnar & Alleppey)",
        "country": "India",
        "category": "nature",
        "travel_types": ["family", "couple", "solo"],
        "cost_range": (4000, 8000),
        "highlights": "Tea garden rolling hills, Alleppey backwaters houseboat, Kathakali cultural show, Ayurvedic massage, Eravikulam National Park",
        "reviews": [
            "Cruising the Alleppey backwaters in an overnight traditional houseboat was pure bliss. Freshly caught Karimeen fish curry was delicious.",
            "Munnar tea plantations covered in morning mist felt straight out of a painting. Spotted the rare Nilgiri Tahr at Eravikulam.",
            "Authentic Ayurvedic rejuvenation therapy was deeply relaxing. Peaceful canoe rides through narrow village canals in Kumarakom.",
            "Very tranquil family vacation. Greenery everywhere, fresh spice plantation tours, and calm serene backwaters."
        ]
    },
    {
        "destination": "Bali",
        "country": "Indonesia",
        "category": "wellness",
        "travel_types": ["couple", "solo", "friends"],
        "cost_range": (6000, 14000),
        "highlights": "Ubud yoga retreats, Tegallalang rice terraces, Uluwatu temple sunset Kecak dance, Seminyak beach clubs, Mount Batur sunrise trek",
        "reviews": [
            "Mount Batur sunrise hike was challenging but reaching the summit for the sunrise above the clouds was magical.",
            "Ubud yoga retreats and vegan cafes were soul soothing. The sacred Monkey Forest and jungle swings are must-visits.",
            "Uluwatu cliff-top temple with the traditional Kecak fire dance against the ocean sunset was world-class.",
            "Seminyak beach clubs like Potato Head offer phenomenal music, infinity pools, and beachfront cocktails."
        ]
    },
    {
        "destination": "Kyoto",
        "country": "Japan",
        "category": "heritage",
        "travel_types": ["solo", "couple", "family"],
        "cost_range": (9000, 20000),
        "highlights": "Fushimi Inari thousand torii gates, Arashiyama bamboo grove, Kinkaku-ji golden pavilion, Gion geisha district, matcha tea ceremonies",
        "reviews": [
            "Walking through the thousands of vermilion torii gates at Fushimi Inari at dawn was a spiritual and peaceful experience.",
            "Arashiyama bamboo grove is mesmerizing. Rented a bicycle to explore quiet Zen stone gardens and historic wooden shrines.",
            "Gion traditional wooden machiya houses and Kaiseki seasonal dining were extraordinary culinary and cultural treats.",
            "Clean, punctual public transit and incredible safety for solo travelers. Golden Pavilion reflection in the pond is unforgettable."
        ]
    },
    {
        "destination": "Paris",
        "country": "France",
        "category": "food",
        "travel_types": ["couple", "solo", "friends"],
        "cost_range": (12000, 28000),
        "highlights": "Louvre museum, Eiffel Tower champagne cruise on Seine, Montmartre art district, croissant & patisserie tasting, Le Marais shopping",
        "reviews": [
            "Dining at classic Parisian bistros in Saint-Germain with steak frites and fresh wine was sheer perfection.",
            "Sunset Seine river cruise with the sparkling Eiffel Tower lights brought tears to our eyes. Louvre art collection is monumental.",
            "Wandering through Montmartre cobblestone alleys, watching street painters, and snacking on warm almond croissants.",
            "Incredible boutique shopping and world-leading patisseries in Le Marais. Architectural splendor on every boulevard."
        ]
    },
    {
        "destination": "Dubai",
        "country": "United Arab Emirates",
        "category": "luxury",
        "travel_types": ["family", "friends", "couple"],
        "cost_range": (10000, 25000),
        "highlights": "Burj Khalifa at the top, Desert Safari dune bashing & BBQ, Dubai Mall fountain show, Palm Jumeirah luxury resorts, Gold Souk",
        "reviews": [
            "Desert safari with 4x4 dune bashing, camel rides, and belly dance dinner under the stars was the highlight of our trip.",
            "Viewing the city skyline from the 148th floor of Burj Khalifa was awe-inspiring. Fountain shows outside Dubai Mall are mesmerizing.",
            "World-class luxury shopping, ultra-clean metro, and futuristic architecture. Water sports at JBR Beach were super fun for friends.",
            "Fabulous family-friendly destination with theme parks, indoor aquariums, and exceptional international dining options."
        ]
    },
    {
        "destination": "Rome",
        "country": "Italy",
        "category": "heritage",
        "travel_types": ["couple", "family", "solo"],
        "cost_range": (10000, 22000),
        "highlights": "Colosseum & Roman Forum guided tour, Vatican Museums & Sistine Chapel, Trevi Fountain gelato walk, Pantheon, Trastevere dining",
        "reviews": [
            "Standing inside the Colosseum and walking the ancient Roman Forum felt like traveling back 2000 years in time.",
            "Tossed a coin in Trevi Fountain and had the creamiest pistachio gelato. Vatican Museums and Michelangelo's ceiling are masterpieces.",
            "Trastevere neighborhood has the liveliest evening ambiance with authentic handmade carbonara and rustic wine cellars.",
            "Walkable historic city center where every corner boasts a Renaissance fountain, baroque church, or ancient Roman pillar."
        ]
    },
    {
        "destination": "Phuket",
        "country": "Thailand",
        "category": "beaches",
        "travel_types": ["friends", "couple", "solo", "family"],
        "cost_range": (4500, 10000),
        "highlights": "Phi Phi island speedboat tour, Patong Bangla road nightlife, Big Buddha viewpoint, snorkeling at Coral Island, Thai street food",
        "reviews": [
            "Speedboat excursion to Maya Bay and Phi Phi Islands had crystal-clear turquoise waters and vibrant coral reefs.",
            "Bangla Road in Patong is wild, lively, and packed with energetic music and street performers. Great for friend groups!",
            "Old Phuket Town has charming Sino-Portuguese architecture and weekend night markets serving pad thai and mango sticky rice.",
            "Affordable luxury private pool villas and soothing traditional Thai massages made this a relaxing yet fun vacation."
        ]
    },
    {
        "destination": "Varanasi",
        "country": "India",
        "category": "spiritual",
        "travel_types": ["solo", "family"],
        "cost_range": (2500, 5000),
        "highlights": "Dashashwamedh Ghat Ganga Aarti ceremony, sunrise boat ride on Ganges, Kashi Vishwanath temple corridor, Sarnath Buddhist stupa, street chaat",
        "reviews": [
            "Witnessing the Grand Ganga Aarti at Dashashwamedh Ghat with ringing bells and oil lamps was an intense spiritual experience.",
            "Early morning boat ride along the ancient ghats watching morning rituals and morning mist over mother Ganga was deeply moving.",
            "Explored the narrow labyrinthine alleys filled with silk weavers, aromatic blue lassi shops, and piping hot kachori jalebi.",
            "Rich spiritual heritage, peaceful visit to Sarnath where Buddha gave his first sermon. Highly economical and culturally profound."
        ]
    },
    {
        "destination": "Barcelona",
        "country": "Spain",
        "category": "food",
        "travel_types": ["friends", "couple", "solo"],
        "cost_range": (9000, 21000),
        "highlights": "Sagrada Familia basilica, Park Güell, Gothic Quarter tapas bar crawl, Barceloneta beach, La Boqueria food market",
        "reviews": [
            "Gaudi's Sagrada Familia is mind-blowing—the stained glass windows cast breathtaking rainbow light across the soaring columns.",
            "Tapas hopping in El Born and Gothic Quarter with sangria, patatas bravas, and jamon iberico was pure gastronomic heaven.",
            "Lively beach vibe at Barceloneta coupled with architectural wonders like Park Güell. Ideal city for young travelers and groups.",
            "La Boqueria market had fresh seafood cones, tropical juices, and vibrant artisanal cheeses. Lively street atmosphere on Las Ramblas."
        ]
    }
]

def generate_csv():
    os.makedirs("./data/raw", exist_ok=True)
    os.makedirs("./data/processed", exist_ok=True)
    os.makedirs("./data/sample_data", exist_ok=True)
    
    rows = []
    user_id_counter = 1001
    
    for dest_info in DESTINATIONS_DATA:
        dest = dest_info["destination"]
        country = dest_info["country"]
        cat = dest_info["category"]
        highlights = dest_info["highlights"]
        min_cost, max_cost = dest_info["cost_range"]
        
        for rev_idx, review in enumerate(dest_info["reviews"]):
            for ttype in dest_info["travel_types"]:
                user_id_counter += 1
                rating = round(random.uniform(4.0, 5.0), 1)
                cost = random.randint(min_cost, max_cost)
                year = random.choice([2024, 2025, 2026])
                month = random.choice(["01", "03", "05", "07", "09", "11", "12"])
                visit_date = f"{year}-{month}-15"
                
                rows.append({
                    "user_id": f"U{user_id_counter}",
                    "destination": dest,
                    "country": country,
                    "category": cat,
                    "rating": rating,
                    "review_text": review,
                    "travel_type": ttype,
                    "visit_date": visit_date,
                    "estimated_daily_cost_inr": cost,
                    "highlights": highlights
                })

    with open(RAW_DATA_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "user_id", "destination", "country", "category", "rating",
            "review_text", "travel_type", "visit_date", "estimated_daily_cost_inr", "highlights"
        ])
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Generated {len(rows)} raw travel records in {RAW_DATA_PATH}")

if __name__ == "__main__":
    generate_csv()
