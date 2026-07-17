from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.database import init_db
from app.routers import analytics, auth, categories, transactions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KYDiR — семейный бюджет", lifespan=lifespan)

# CORS нужен только на время разработки фронта с отдельного dev-сервера.
# В проде фронт раздаётся этим же приложением — same-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI(title="KYDiR API")
api.include_router(auth.router)
api.include_router(users.router)
api.include_router(categories.router)
api.include_router(transactions.router)
api.include_router(analytics.router)
app.mount("/api", api)

if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
