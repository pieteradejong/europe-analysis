## Learnings

### 2025-12-19 — `run.sh` backend not ready (port already in use)
- **Symptom**: Backend health check never becomes ready; logs show `Address already in use`.
- **Root cause**: A prior `uvicorn`/Python process was already listening on **TCP 8000** (and sometimes the Vite dev server on **5173**).
- **Fix**: Updated `run.sh` to proactively **free ports 8000 and 5173** before starting backend/frontend, so rerunning `./run.sh` replaces any already-running dev instances.
- **Debug tip**: Identify the blocker with `lsof -nP -iTCP:8000 -sTCP:LISTEN` (and similarly for `5173`).
