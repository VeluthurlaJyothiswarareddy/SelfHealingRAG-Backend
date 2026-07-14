# Backend (FastAPI) — SelfHealingRAG

Lightweight FastAPI backend for the SelfHealingRAG project. Serves the API, vector store integration, and background scripts used by the frontend.

Prerequisites
- Python 3.10+
- pip

Quick start (local)
1. Create and activate a virtual environment:

   python -m venv venv
   source venv/bin/activate

2. Install dependencies:

   pip install -r requirements.txt

3. Copy environment variables and edit as needed:

   cp .env.example .env
   # then edit .env

4. Run the development server:

   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Docker (optional)

Build and run the provided Dockerfile:

   docker build -t selfhealingrag-backend .
   docker run --env-file .env -p 8000:8000 selfhealingrag-backend

Important paths
- `app/` — application package (routes, services, db, models)
- `requirements.txt` — Python dependencies
- `scripts/seed_global_docs.py` — helper to seed documents into the index

API overview
The backend exposes API routes under `app/api/` including authentication, chat, and documents endpoints. Start the server and visit `http://localhost:8000/docs` for the interactive OpenAPI UI.

Contributing
- Follow existing code style. Run the server locally and use `uvicorn --reload` for iterative development.
# SelfHealingRAG-Backend
