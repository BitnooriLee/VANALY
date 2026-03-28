from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import UPLOADS_DIR, init_db
from backend.routers import coach, meals, users

load_dotenv()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="VANALY API",
    description="Sustainable AI Health Coach — '꿀꺽' 전 찰나의 개입",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 라우터 (정적 파일 마운트보다 먼저 등록해야 우선순위가 높음) ────────────
app.include_router(users.router)
app.include_router(meals.router)
app.include_router(coach.router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "VANALY API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── 정적 파일 마운트 (API 라우터 등록 후 마지막에 배치) ───────────────────────
# 업로드 이미지
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# 프론트엔드 — html=True 로 SPA 라우팅 지원 (매칭 안 되는 경로 → index.html)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
