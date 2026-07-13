from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.db.session import get_db
from app.schemas.schemas import WeatherOut
from app.services.weather_service import get_weather

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/", response_model=WeatherOut)
async def weather(
    city: str = Query(..., description="City name"),
    date: date = Query(..., description="Date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weather forecast for a city on a specific date.
    Returns temperature, rain probability, fog alerts and travel advice.
    """
    return await get_weather(city=city, target_date=date, db=db)
