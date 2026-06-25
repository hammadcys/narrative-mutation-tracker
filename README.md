# 🔍 Narrative Mutation Tracker

> **Trace how viral claims mutate across Pakistani and South Asian media — from origin to amplification.**

A RAG-powered agentic pipeline that takes any news claim, fetches real articles from multiple sources, embeds them into a vector store, and uses an LLM to detect how the narrative evolved over time.

---

## ✨ Features

- **Multi-source fetching** — GDELT (65,000+ outlets), The Guardian, GNews
- **Narrative mutation detection** — LLM scores how much the story drifted (1–10)
- **Timeline reconstruction** — Origin article → spread → amplification buckets
- **Source credibility scoring** — Reliable / Mixed / Tabloid / Unknown breakdown
- **RAG Q&A** — Ask questions grounded strictly in fetched articles
- **Clean Streamlit UI** — Dark-mode, newspaper-style dashboard

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq (`llama-3.3-70b-versatile`) — fast & free |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | ChromaDB (local persistent store) |
| News sources | GDELT API · The Guardian API · GNews API |
| Frontend | Streamlit + Plotly |
| Backend | FastAPI (optional REST API) |

---

## 🚀 Getting Started

### 1. Clone & install

```bash
git clone https://github.com/hammadcys/narrative-mutation-tracker.git
cd narrative-mutation-tracker
pip install -r requirements.txt
```

### 2. Set up API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY="your_groq_key"          # groq.com — free
GUARDIAN_API_KEY="your_guardian_key"  # open-platform.theguardian.com — free
GNEWS_API_KEY="your_gnews_key"        # gnews.io — free (100 req/day)
```

### 3. Run

```bash
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser.

---

## 🗂️ Project Structure

```
misinformation-tracker/
├── agents/
│   ├── fetcher.py          # GDELT + Guardian + GNews fetching
│   ├── normalizer.py       # LLM query generation from raw claim
│   ├── mutation_detector.py # LLM narrative drift analysis
│   ├── timeline.py         # Origin → spread → amplification buckets
│   └── credibility_scorer.py # Outlet trust rating
├── rag/
│   ├── embedder.py         # Chunk + embed articles into ChromaDB
│   ├── retriever.py        # RAG retrieval + LLM answer generation
│   └── singletons.py       # Shared model/client instances
├── frontend/
│   └── app.py              # Streamlit UI
├── api/
│   └── main.py             # FastAPI REST endpoints
├── data/
│   └── outlet_ratings.json # Outlet credibility ratings
├── pipeline.py             # Full orchestration pipeline
└── config.py               # All tuneable constants
```

---

## 🔄 How It Works

```
User claim
    │
    ▼
[1] Groq LLM generates 3 search queries
    │
    ▼
[2] Fetch articles — GDELT + Guardian + GNews
    │
    ▼
[3] Embed chunks into ChromaDB (sentence-transformers)
    │
    ▼
[4] Build timeline (origin → spread → amplification)
    │
    ▼
[5] Detect mutation — LLM compares early vs late framing
    │
    ▼
[6] Score source credibility
    │
    ▼
Dashboard + RAG Q&A
```

---

## 📡 API (Optional)

Run the FastAPI backend:

```bash
uvicorn api.main:app --reload
```

Endpoints:
- `GET /health` — health check
- `POST /analyze` — run full pipeline on a claim
- `POST /ask` — RAG Q&A on last fetched articles

---

## 📋 Requirements

See [`requirements.txt`](requirements.txt). Key dependencies:

```
streamlit
fastapi
groq
chromadb
sentence-transformers
plotly
requests
python-dotenv
```

---

## ⚠️ Notes

- GDELT is a free public API — it can be slow or rate-limited at peak times. The pipeline retries automatically.
- The Guardian and GNews keys are free — sign up takes under 2 minutes.
- ChromaDB is stored locally in `./chroma_store/` — excluded from git.

---

## 📜 License

MIT
