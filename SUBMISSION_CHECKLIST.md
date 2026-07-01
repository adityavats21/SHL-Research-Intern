# Submission Checklist

1. Push this folder to GitHub.
2. Deploy on Render, Railway, Fly, or another public host.
3. Set the start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

4. Confirm the public health URL returns `{"status":"ok"}`:

```bash
curl https://YOUR-APP-URL/health
```

5. Confirm `/chat` returns the required schema:

```bash
curl -X POST https://YOUR-APP-URL/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hiring a senior backend Java engineer. Core Java, Spring, SQL, AWS, Docker. Senior IC."}]}'
```

6. Submit:
   - Public API endpoint URL
   - `APPROACH.md`

Before deploying, local verification should pass:

```bash
pytest
python scripts/validate_public_traces.py
```
