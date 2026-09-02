  # JohnBot — AI Software Debugging and Code Explanation Assistant using Code RAG

## Overview

JohnBot is a full-stack AI developer tool. You upload source code files, JohnBot indexes
them using Retrieval-Augmented Generation (RAG), and you can then ask natural-language
questions about the codebase — "explain this function," "find potential bugs," "how does
authentication work?" — and JohnBot answers using only the code chunks actually relevant
to your question, with real file/line source references.

This is a real RAG system: your question is embedded, matched against your indexed code
via vector similarity search, and only the top matching chunks are sent to the LLM. The
full codebase is never sent to the model on every question.

## Features

- Code upload (`.py .js .jsx .ts .tsx .java .c .cpp .html .css .sql .json .md`)
- Local, logical code chunking (splits on functions/classes where possible)
- Embeddings via the **Jina AI Embeddings API** (`jina-embeddings-v3`) — chat still uses Gemini, so two free-tier keys power the app
- Local vector store with cosine similarity search (configurable `TOP_K`)
- One LLM call per question via **Gemini**
- Real source references (file name + line range) — never fabricated
- Chat history, persisted per user in SQLite
- File management (list, status, delete)
- Settings (theme, enter-to-send, show-sources)
- Simple local authentication (register/login/logout, hashed passwords, JWT)
- Light / dark / system theme, black + silver + neutral design

## Architecture

```
React (Vite)
   |
FastAPI backend
   |
   +-- Upload -> chunk -> embed (Jina) -> vector store
   |
   +-- Chat -> embed question (Jina) -> vector search -> top-K chunks -> Gemini -> answer
```

## Technologies

- Frontend: React, Vite, React Router, react-markdown, react-syntax-highlighter
- Backend: Python, FastAPI, Uvicorn, SQLAlchemy
- Database: SQLite
- RAG: Jina AI Embeddings API (`jina-embeddings-v3`, free tier) for chunk/query embeddings, a lightweight local pickle-backed vector store
- LLM: Gemini (`gemini-3.6-flash` by default)
- Auth: JWT + bcrypt (passlib)

## Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.6-flash
JINA_API_KEY=your_key_here
JINA_EMBEDDING_MODEL=jina-embeddings-v3
```

Get a free Gemini key at https://aistudio.google.com/apikey (chat) and a free Jina key at
https://jina.ai/embeddings (embeddings) — no credit card needed for either. Free-tier
embedding calls are rate-limited; the embedder batches and retries automatically, but
very large uploads may take a little longer or need a short pause between files.

### Frontend

```bash
cd frontend
npm install
```

## Running

**Backend** (from `backend/`, with the virtualenv active):

```bash
uvicorn app.main:app --reload --port 8000
```

**Frontend** (from `frontend/`, in a second terminal):

```bash
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend
on port 8000 (see `frontend/vite.config.js`).

## Usage

1. Register an account (or log in if you already have one).
2. Go to **Files** and upload one or more source files.
3. Wait for each file's status to reach **Ready** (this means it's chunked, embedded,
   and indexed).
4. Go to **Chat** and ask a question, or click one of the example prompts.
5. JohnBot retrieves the relevant code chunks, sends them to Agent Router, and answers
   with source references shown underneath.
6. Open **History** to revisit past conversations, or **Settings** to change theme/behavior.

## Environment variables (`backend/.env`)

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Your free Gemini API key (never committed, never sent to the frontend) |
| `GEMINI_MODEL` | Gemini chat model to use |
| `JINA_API_KEY` | Your free Jina AI API key (never committed, never sent to the frontend) |
| `JINA_EMBEDDING_MODEL` | Jina embedding model to use |
| `JWT_SECRET` | Secret used to sign auth tokens — set to a random string |
| `TOP_K` | Number of code chunks retrieved per question |
| `MAX_FILE_SIZE_MB` | Max upload size per file |
| `FRONTEND_ORIGIN` | Allowed CORS origin for the frontend |

## Security

Uploaded code is only ever read as plain text — it is never executed, evaluated, or run
as a subprocess. Passwords are hashed with bcrypt and never stored in plain text. The
Gemini API key lives only in the backend `.env` file and is never exposed to the
browser.

## Testing

```bash
cd backend
pytest tests/
```

Tests cover code chunking, embedding output shape/normalization, and local title
generation.

## Project structure

```
backend/
  app/
    main.py               FastAPI app entry point
    config.py              Environment-based settings
    api/                    Route handlers (thin)
    services/               Business logic (RAG orchestration, LLM client, files)
    rag/                    loader / chunker / embedder / vector_store
    database/               SQLAlchemy models
    models/                 Pydantic schemas
    utils/                  Auth helpers
  tests/
frontend/
  src/
    components/             Sidebar, ChatWindow, ChatMessage, FileUpload, etc.
    pages/                   Home, History, Files, Settings, Login, Register
    services/                api.js, AuthContext, ThemeContext
    styles/                  theme.css, app.css
```
