# WAYPOINT: AI-Powered Travel Planning & Itinerary Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/VectorStore-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![React + Vite](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript%20%2B%20Vite-61DAFB.svg)](https://vitejs.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Project Overview & Business Objective

**Waypoint** is an enterprise-grade, explainable travel intelligence system designed for travel advisors, tourism organizations, and modern travelers. Rather than relying on naive single-prompt LLM wrappers that hallucinate non-existent hotel names, invent arbitrary ratings, and produce broken currency math, Waypoint orchestrates **8 specialized LangGraph agents** grounded in **5,456 authentic review vectors from UCI Dataset 485** and **live OpenStreetMap POI validation**.

The system combines **Hybrid Search (Dense Semantic Embeddings + Lexical BM25)** with **Deterministic Budget Feasibility Arithmetic** and an **LLM-as-a-Judge Quality Validator** with automatic iterative self-refinement.

---

## 2. Architecture & Data Flow

```text
                    UCI DATASET 485 (5,456 Reviews across 24 Categories)
                                       │
                                       ▼
                         PREPROCESSING & CHUNKING
                                       │
                                       ▼
                   EMBEDDINGS (all-MiniLM-L6-v2, 384-d)
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
             CHROMADB VECTOR STORE               BM25 KEYWORD INDEX
             (Dense Semantic Search)             (Lexical Matching)
                     │                                   │
                     └─────────────────┬─────────────────┘
                                       ▼
                 HYBRID RETRIEVER (Reciprocal Rank Fusion, RRF)
                                       │
                                       ▼
              MULTI-FACTOR RERANKER (Pref + Semantic + Rating + Budget)
                                       │
                                       ▼
                     LANGGRAPH 7-AGENT ORCHESTRATION ENGINE
                                       │
  ┌────────────────────────────────────┼────────────────────────────────────┐
  ▼                                    ▼                                    ▼
[01. Input Guardrails]       [02. Preference Classifier]          [03. Destination Analyzer]
  │                                    │                                    │
  └────────────────────────────────────┴────────────────────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          [04. Budget Analyst]               [05. Activity Recommender]
                     │                                   │
                     └─────────────────┬─────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
         [06. Accommodation Finder]          [07. Itinerary Planner]
                     │                                   │
                     └─────────────────┬─────────────────┘
                                       │
                                       ▼
                          [08. Quality Validator]
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                   (APPROVED ✓)              (NEEDS REFINEMENT)
                         │                           │
                         │                           └──→ [Itinerary Planner]
                         ▼
               FASTAPI REST API LAYER (OpenAPI 3.1)
                         │
                         ▼
           REACT + TYPESCRIPT EDITORIAL WORKSPACE
```

---

## 3. The Eight Primary Agents

| # | Agent Name | Node Identifier | Key Responsibility | Primary Grounding / Logic |
|---|---|---|---|---|
| 1 | **Preference Classifier** | `preference_classifier` | Converts natural language travel requirements into structured parameters (`duration`, `budget`, `traveler_type`, `interests`). | Strict extraction; does not invent missing fields (e.g. `destination = null` if unmentioned). |
| 2 | **Destination Analyzer** | `destination_analyzer` | Identifies and ranks destination candidates matching user intent. | Hybrid RAG search over Dataset 485 + Multi-factor reranking formula. |
| 3 | **Budget Analyst** | `budget_analyst` | Determines financial feasibility, confidence ratio, and itemized allocation. | Deterministic Python arithmetic across Stay (38%), Food (24%), Activities (18%), Transit (12%), Misc (8%). |
| 4 | **Activity Recommender** | `activity_recommender` | Selects and ranks activities per destination with time slots and costs. | Historical category ratings from Dataset 485 + OpenStreetMap live tourist spots. |
| 5 | **Accommodation Finder** | `accommodation_finder` | Recommends lodging tiers and strategic neighborhood positioning. | Architectural & budget tiers (Category 13) grounded in local area hubs without hotel hallucinations. |
| 6 | **Flight Finder** | `flight_finder` | Curates realistic transit and airline options across budget/standard/premium tiers. | Realistic route flight times and typical pricing for domestic and international sectors. |
| 7 | **Itinerary Planner** | `itinerary_planner` | Constructs a balanced chronological Morning, Afternoon, Evening plan. | Realistic daily pacing (max 2–3 key activities/day + meal/transit buffers). |
| 8 | **Quality Validator** | `quality_validator` | LLM-as-a-Judge evaluating alignment, feasibility, coherence, and grounding. | Evaluates quality score (0.00–1.00); triggers conditional refinement loop if `< 0.80`. |

---

## 4. Recommendation Scoring Formula

Candidate destinations and experiences are ranked via a transparent, multi-factor scoring formula:

$$\text{Final Score} = w_1 \cdot \text{PreferenceMatch} + w_2 \cdot \text{SemanticRelevance} + w_3 \cdot \text{HistoricalRating} + w_4 \cdot \text{EvidenceStrength} + w_5 \cdot \text{BudgetCompatibility}$$

* **Weights:** $w_1 = 0.30$, $w_2 = 0.25$, $w_3 = 0.20$, $w_4 = 0.15$, $w_5 = 0.10$.
* All factors are normalized in $[0.0, 1.0]$ and presented transparently in the UI and API response.

---

## 5. Technology Stack

* **Backend Engine:** Python 3.11+, FastAPI, Uvicorn, Pydantic V2, Pydantic Settings (10 REST endpoints)
* **Agent Orchestration:** LangGraph (`StateGraph`), LangChain Core (8 specialized agents)
* **Large Language Model:** Google Gemini (`gemini-2.5-flash`) with structured JSON mode and offline deterministic rule-engine fallback
* **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dimensional dense vectors)
* **Vector Store:** ChromaDB (Local Persistent Cosine Index)
* **Keyword Search:** BM25 Okapi (`rank-bm25`)
* **Knowledge & Live POI:** OpenStreetMap (Photon API & Nominatim geocoding)
* **Frontend Applications:**
  * **Streamlit UI:** Native Python interactive application (`frontend.py` / `streamlit_app.py`)
  * **React Workspace:** React 18, Vite 5, TypeScript 5, Tailwind CSS, Lucide Icons (`frontend/`)
* **Testing & Evaluation:** PyTest, PyTest-Asyncio, DeepEval (`deepeval>=4.2.8`), RAGAS Synthetic Benchmarks
* **Deliverable Generators:** ReportLab, python-pptx

---

## 6. Project Directory Structure

```text
Eshan_TravelPlanning/
│
├── architecture/
│   └── Architecture_Diagram.pdf        # High-level architecture & data flow
│
├── design/
│   └── Design_Document.pdf             # Comprehensive technical design specification
│
├── docs/
│   ├── API_Documentation.pdf           # Complete REST API endpoint reference
│   ├── Dataset_Details.pdf             # UCI Dataset 485 schema & provenance
│   └── Evaluation_Report.pdf           # Benchmark evaluation results & metrics
│
├── presentation/
│   └── Project_Presentation.pptx       # 10-minute presentation deck (7 visual slides)
│
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                   # FastAPI route handlers
│   │   └── schemas.py                  # Pydantic V2 request/response models
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── preference_classifier.py    # Agent 1
│   │   ├── destination_analyzer.py     # Agent 2
│   │   ├── budget_analyst.py           # Agent 3
│   │   ├── activity_recommender.py     # Agent 4
│   │   ├── accommodation_finder.py     # Agent 5
│   │   ├── flight_finder.py            # Agent 6 (Transit & Flights)
│   │   ├── itinerary_planner.py        # Agent 7
│   │   └── quality_validator.py        # Agent 8 (LLM-as-a-Judge)
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── preprocessing.py            # UCI 485 cleaning & 24-category mapping
│   │   ├── chunking.py                 # Structured document chunk constructor
│   │   ├── embeddings.py               # SentenceTransformers wrapper
│   │   ├── vector_store.py             # ChromaDB persistent collection manager
│   │   ├── keyword_search.py           # In-memory BM25 Okapi indexer
│   │   ├── hybrid_retriever.py         # Reciprocal Rank Fusion retriever
│   │   ├── reranker.py                 # Multi-factor transparent scoring reranker
│   │   └── ingestion.py                # End-to-end data ingestion pipeline
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── langgraph_workflow.py       # Compiled LangGraph StateGraph & nodes
│   │   ├── recommendation_service.py   # High-level RAG search service
│   │   ├── budget_service.py           # Feasibility wrapper service
│   │   └── validation_service.py       # Quality evaluation wrapper
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py                   # Pydantic Settings & environment loader
│   │   ├── logging.py                  # Structured logging & agent duration timers
│   │   ├── guardrails.py               # Input validation & injection filter
│   │   └── llm.py                      # Gemini client with JSON mode & fallback
│   │
│   ├── __init__.py
│   └── main.py                         # FastAPI application entrypoint
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── components/                 # Workspace, Summary, Timeline, Trace Inspector
│       ├── services/                   # API fetch client
│       ├── types/                      # TypeScript schemas
│       ├── styles/                     # Tailwind & custom CSS
│       ├── App.tsx
│       └── main.tsx
│
├── data/
│   ├── raw/
│   │   └── google_review_ratings.csv   # Exact UCI Dataset 485 archive (5,456 rows)
│   ├── processed/
│   │   └── processed_travel_reviews.json # Ingested JSON document store
│   └── sample_data/
│       └── sample_trips.json           # Sample test queries
│
├── tests/
│   ├── conftest.py
│   ├── test_guardrails.py              # Input bounds & security tests
│   ├── test_retrieval.py               # Vector, BM25 & Hybrid search tests
│   ├── test_agents.py                  # Unit tests for all 7 agents
│   ├── test_workflow.py                # LangGraph full execution test
│   └── test_api.py                     # FastAPI endpoint integration tests
│
├── scripts/
│   ├── download_uci_dataset.py         # UCI 485 fetcher
│   ├── ingest_data.py                  # CLI ingestion runner
│   ├── evaluate.py                     # Evaluation benchmark runner
│   └── generate_deliverables.py        # PDF & PPTX generator
│
├── frontend.py                     # Streamlit frontend entrypoint (Guideline Section 11)
├── streamlit_app.py                # Streamlit client implementation
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 7. Quickstart & Installation Instructions

### Prerequisites
* Python 3.11+
* Node.js 18+ and npm

### 1. Clone & Setup Python Virtual Environment
```bash
# Clone the repository
git clone https://github.com/EshanDasarwarProdapt/Eshan_TravelPlanning.git
cd Eshan_TravelPlanning

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the example environment file and configure your Gemini API Key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
```
*(Note: If `GEMINI_API_KEY` is omitted, the system runs smoothly in local deterministic engine mode for local testing).*

### 3. Ingest UCI Dataset 485
```bash
python scripts/ingest_data.py
```
*Indexes 5,456 review vectors into `./data/chroma_db` and compiles the BM25 index.*

### 4. Start Backend Server
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
* The API will be live at: `http://localhost:8000`
* Interactive OpenAPI Documentation: `http://localhost:8000/docs`

### 5. Start Frontend UI

**Option A: Streamlit Interface (Capstone Guideline Section 11 Standard)**
In a separate terminal:
```bash
streamlit run frontend.py
```
* The Streamlit UI will be live at: `http://localhost:8501`

**Option B: React + Vite Enterprise Workspace**
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
* The React UI will be live at: `http://localhost:5173`

---

## 8. Sample User Queries & Expected Behavior

### Sample Query 1: Coastal Friend Group Getaway
* **Input:** `"I have 5 days and around ₹40,000. I'm travelling with friends and want beaches, good food, nightlife and some adventure."`
* **Identified Destination:** Goa (Match Score: 94.2%)
* **Budget Analysis:** Est. Total ₹35,600 (Feasible, Surplus +₹4,400, Confidence: 88%)
* **Curated Activities:** Grande Island Scuba Diving, Thalassa Sunset Lounge, Club Cubana DJ Night.
* **Itinerary:** 5-Day chronologically sequenced Morning / Afternoon / Evening schedule with transit notes.
* **Quality Score:** 93% (Approved by Quality Validator).

### Sample Query 2: Mountain Adventure
* **Input:** `"4 days mountain adventure in Manali with friends for paragliding, river rafting, and scenic trekking under ₹30,000."`
* **Identified Destination:** Manali (Match Score: 92.5%)
* **Budget Analysis:** Est. Total ₹24,800 (Feasible, Surplus +₹5,200)

### Sample Query 3: Cultural Family Heritage
* **Input:** `"3 days family heritage tour in Jaipur exploring royal forts, palace architecture, and traditional Rajasthani dining for ₹35,000."`
* **Identified Destination:** Jaipur (Match Score: 95.0%)
* **Budget Analysis:** Est. Total ₹28,500 (Feasible, Surplus +₹6,500)

---

## 9. Running Automated Tests & Evaluation

### Run PyTest Suite
```bash
python -m pytest -v
```
*Executes all 23 unit and integration tests across Guardrails, RAG, Agents, LangGraph Workflow, and FastAPI endpoints.*

### Run Synthetic Benchmark Evaluation
```bash
python scripts/evaluate.py
```
*Generates evaluation metrics across Retrieval Relevance, Grounding Faithfulness, Preference Alignment, and Itinerary Coherence.*

---

## 10. Deliverable Artifacts

The repository includes all mandatory and recommended submission artifacts:
1. `architecture/Architecture_Diagram.pdf`
2. `design/Design_Document.pdf`
3. `docs/API_Documentation.pdf`
4. `docs/Dataset_Details.pdf`
5. `docs/Evaluation_Report.pdf`
6. `presentation/Project_Presentation.pptx`

To regenerate any deliverable:
```bash
python scripts/generate_deliverables.py
```

---

## 11. Limitations & Future Roadmap

* **Real-Time Booking Integration:** Currently provides strategic lodging tiers and neighborhood positioning based on Dataset 485; future iterations can connect to live GDS / hotel booking APIs.
* **Live Weather & Flight Pricing:** Multi-modal weather overlays and airline GDS feeds.
* **Multi-Currency Dynamic Conversion:** Real-time forex rates for international itineraries.

---

## 12. License

This project is licensed under the [MIT License](LICENSE).
