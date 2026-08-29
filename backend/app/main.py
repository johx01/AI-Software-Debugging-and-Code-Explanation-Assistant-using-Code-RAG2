import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.database import init_db
from app.api import routes_auth, routes_upload, routes_chat, routes_files, routes_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("johnbot")

app = FastAPI(title="JohnBot API", description="AI Software Debugging and Code Explanation Assistant using Code RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("JohnBot backend started")


@app.get("/")
def root():
    return {"status": "ok", "service": "JohnBot API"}


app.include_router(routes_auth.router)
app.include_router(routes_upload.router)
app.include_router(routes_chat.router)
app.include_router(routes_files.router)
app.include_router(routes_settings.router)
