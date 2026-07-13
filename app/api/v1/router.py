from fastapi import APIRouter
from app.api.v1.endpoints import auth, routes, weather, holidays, risk, hotels, dashboard, itineraries

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(routes.router)
api_router.include_router(weather.router)
api_router.include_router(holidays.router)
api_router.include_router(risk.router)
api_router.include_router(hotels.router)
api_router.include_router(dashboard.router)
api_router.include_router(itineraries.router)
