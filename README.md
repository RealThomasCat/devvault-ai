# DevVault AI

DevVault AI is a source-cited RAG knowledge base for engineering teams. It lets users upload Markdown or plain text documents, stores document chunks with vector embeddings, retrieves semantically relevant source context, and answers questions with citations from the uploaded documents.

## Features

- FastAPI backend with OpenAPI documentation.
- PostgreSQL database with pgvector support.
- Markdown and TXT document upload.
- Character-based document chunking with overlap.
- Local embedding generation through Ollama.
- Vector similarity search over uploaded document chunks.
- Source-cited chat responses generated from retrieved context.
- Document listing, detail, and delete endpoints.
- Alembic-managed database migrations.
- Docker Compose setup for PostgreSQL.

## Tech Stack

| Layer | Technology |
| --- | --- |
| API | FastAPI |
| Configuration | Pydantic Settings |
| Database | PostgreSQL |
| Vector storage/search | pgvector |
| ORM/database access | SQLAlchemy |
| Migrations | Alembic |
| Embeddings | Ollama `embeddinggemma` |
| Chat generation | Ollama `llama3.2` |
| Local infrastructure | Docker Compose |

## Architecture

```text
User / API Client
  -> FastAPI backend
  -> Document upload and management routes
  -> Chunking service
  -> Ollama embedding model
  -> PostgreSQL + pgvector
  -> Retrieval service
  -> Ollama chat model
  -> Source-cited answer
```

RAG flow:

```text
upload document
  -> validate file
  -> decode text
  -> split into chunks
  -> generate embeddings
  -> store document, chunks, and vectors

ask question
  -> embed question
  -> retrieve nearest chunks
  -> build grounded prompt context
  -> generate answer
  -> return answer with citations
```

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
          chat.py
          documents.py
          health.py
          search.py
      core/
        __init__.py
        config.py
      db/
        __init__.py
        base.py
        session.py
        models/
          __init__.py
          document.py
          document_chunk.py
      integrations/
        __init__.py
        ollama_client.py
      schemas/
        __init__.py
        chat.py
        document.py
        search.py
      services/
        __init__.py
        chat_service.py
        chunking_service.py
        document_service.py
        embedding_service.py
        retrieval_service.py
    migrations/
    scripts/
    alembic.ini
    requirements.txt
  docker-compose.yml
  README.md
```

## Configuration

Create `backend/.env` with local settings:

```env
APP_NAME=DevVault AI
APP_ENV=local
DATABASE_URL=postgresql+psycopg://devvault:devvault@localhost:5433/devvault
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=embeddinggemma
OLLAMA_CHAT_MODEL=llama3.2
```

## Run Locally

### 1. Start PostgreSQL

Run Docker Compose from the project root:

```powershell
cd D:\Github\devvault-ai
docker compose up -d
```

Check the container:

```powershell
docker compose ps
```

### 2. Prepare Python Environment

Run from the backend folder:

```powershell
cd D:\Github\devvault-ai\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Prepare Ollama Models

Make sure Ollama is running, then pull the local models:

```powershell
ollama pull embeddinggemma
ollama pull llama3.2
```

### 4. Apply Migrations

Run Alembic from the backend folder:

```powershell
cd D:\Github\devvault-ai\backend
.venv\Scripts\Activate.ps1
alembic upgrade head
```

This enables pgvector and creates the document/chunk tables.

### 5. Run the Backend

```powershell
cd D:\Github\devvault-ai\backend
.venv\Scripts\Activate.ps1
fastapi dev app/main.py
```

The API runs at:

```text
http://127.0.0.1:8000
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Root welcome response. |
| `GET` | `/health` | Application health check. |
| `GET` | `/health/db` | Database connectivity check. |
| `POST` | `/documents/upload` | Upload a Markdown or TXT document. |
| `GET` | `/documents` | List uploaded documents with chunk counts. |
| `GET` | `/documents/{document_id}` | Get one document summary. |
| `DELETE` | `/documents/{document_id}` | Delete a document and its chunks. |
| `POST` | `/search` | Search uploaded chunks by semantic similarity. |
| `POST` | `/chat` | Ask a question and receive a source-cited answer. |

## Example Usage

### Upload a Document

```powershell
curl.exe -X POST `
  http://127.0.0.1:8000/documents/upload `
  -F "file=@D:\Github\devvault-ai\sample.md"
```

Example response:

```json
{
  "document_id": 1,
  "filename": "sample.md",
  "chunk_count": 3
}
```

### List Documents

```powershell
curl.exe http://127.0.0.1:8000/documents
```

### Search Documents

```powershell
curl.exe -X POST `
  http://127.0.0.1:8000/search `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"What does this project use pgvector for?\",\"top_k\":3}"
```

### Ask a Question

```powershell
curl.exe -X POST `
  http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d "{\"question\":\"What does this project use pgvector for?\"}"
```

Example response shape:

```json
{
  "answer": "pgvector is used to store and compare document chunk embeddings for semantic retrieval.",
  "citations": [
    {
      "chunk_id": 1,
      "document_id": 1,
      "filename": "sample.md",
      "snippet": "..."
    }
  ]
}
```

## Database

Main tables:

| Table | Purpose |
| --- | --- |
| `documents` | Stores uploaded document metadata. |
| `document_chunks` | Stores chunk text and `VECTOR(768)` embeddings. |

Useful checks:

```sql
SELECT * FROM documents;
SELECT document_id, chunk_index, embedding IS NOT NULL AS has_embedding
FROM document_chunks
ORDER BY document_id, chunk_index;
```

Check embedding dimensions:

```sql
SELECT id, vector_dims(embedding) AS dimensions
FROM document_chunks
WHERE embedding IS NOT NULL;
```

Expected dimension:

```text
768
```
