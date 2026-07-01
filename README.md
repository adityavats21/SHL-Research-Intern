# SHL Conversational Assessment Recommender

FastAPI service for the SHL AI Intern take-home assignment. It exposes the required stateless endpoints:

- `GET /health` -> `{"status": "ok"}`
- `POST /chat` -> next agent reply, `recommendations`, and `end_of_conversation`

The app uses the official SHL catalog JSON in `data/shl_product_catalog.json`, never returns URLs outside that catalog, and keeps response generation deterministic for low-latency automated evaluation.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs` to try `/chat` from Swagger UI.

## Example

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hiring a senior Java engineer with Spring, SQL, AWS and Docker. Backend leaning, senior IC."}]}'
```

## Test

```bash
pip install -r requirements-dev.txt
pytest
python scripts/validate_public_traces.py
```

## Deploy

Render can deploy this repo directly. Use:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

The included `render.yaml`, `Procfile`, `runtime.txt`, and `Dockerfile` cover common free-tier hosts.
