# DevVault AI

Source-cited RAG knowledge base for engineering teams.

## Current Milestone

Foundation only:

- FastAPI backend
- Environment config
- Health check endpoint
- PostgreSQL with pgvector via Docker Compose

Not implemented yet:

- Document ingestion
- Embeddings
- RAG retrieval
- Chat generation
- Frontend

## Project Structure

```text
devvault-ai/
  backend/
    app/
      __init__.py
      main.py
      api/
        __init__.py
        routes/
          __init__.py
          health.py
      core/
        __init__.py
        config.py
    .env
    .env.example
    requirements.txt
  docker-compose.yml
  README.md
```

## Run Locally

### 1. Start PostgreSQL

Run Docker Compose from the project root:

```powershell
cd D:\Github\devvault-ai
docker compose up -d
```

Check that the container is running:

```powershell
docker compose ps
```

### 2. Enable pgvector

Run this from the project root:

```powershell
docker exec -it devvault-postgres psql -U devvault -d devvault -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Verify pgvector:

```powershell
docker exec -it devvault-postgres psql -U devvault -d devvault -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Expected output should include:

```text
vector
```

### 3. Run the Backend

Run these commands from the backend folder:

```powershell
cd D:\Github\devvault-ai\backend
.venv\Scripts\Activate.ps1
fastapi dev app/main.py
```

The server should start at:

```text
http://127.0.0.1:8000
```

### 4. Verify the API

Open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
    "status": "ok",
    "app": "DevVault AI",
    "env": "local"
}
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```
