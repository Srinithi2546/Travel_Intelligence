from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.endpoints.websocket import router as ws_router
from app.db.session import engine, Base
from app.services.holiday_service import seed_holidays
from app.services.route_service import seed_routes
from app.services.hotel_service import seed_hotels
from app.db.session import AsyncSessionLocal

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Smart Travel API...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables ready")

    # Seed reference data
    async with AsyncSessionLocal() as db:
        await seed_holidays(db, year=2025)
        await seed_holidays(db, year=2026)
        await seed_routes(db)
        await seed_hotels(db)
        await db.commit()
    logger.info("✅ Seed data loaded")

    yield

    logger.info("🛑 Shutting down Smart Travel API")
    await engine.dispose()


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🗺️ Smart Travel Intelligence Platform API

Aggregates travel data, predicts risk, and recommends optimal travel plans for intercity travel in India.

### Modules
| Module | Endpoint Prefix |
|--------|----------------|
| Authentication | `/api/v1/auth` |
| Route Aggregation | `/api/v1/routes` |
| Weather Analysis | `/api/v1/weather` |
| Holiday Detection | `/api/v1/holidays` |
| Risk Prediction | `/api/v1/risk` |
| Hotel Recommendations | `/api/v1/hotels` |
| Smart Dashboard | `/api/v1/dashboard` |
| Itinerary Manager | `/api/v1/itineraries` |
| Real-time Alerts | `ws://host/ws/alerts/{src}/{dst}/{date}` |
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(api_router)
app.include_router(ws_router)


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to Smart Travel Intelligence API",
        "docs": "/docs",
        "health": "/health",
    }
