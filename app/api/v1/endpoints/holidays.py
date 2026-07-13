from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List
from app.db.session import get_db
from app.schemas.schemas import HolidayOut
from app.services.holiday_service import get_holidays_near_date, compute_holiday_risk_score

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.get("/near", response_model=List[HolidayOut])
async def holidays_near_date(
    date: date = Query(..., description="Travel date (YYYY-MM-DD)"),
    window: int = Query(3, ge=1, le=14, description="Days to look around date"),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch holidays within ±window days of the travel date.
    Used to detect peak demand periods like long weekends, Diwali, etc.
    """
    return await get_holidays_near_date(date, db, window_days=window)


@router.get("/score")
async def holiday_risk_score(
    date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Returns the holiday demand risk score (0–10) for a travel date."""
    holidays = await get_holidays_near_date(date, db)
    score = compute_holiday_risk_score(holidays, date)
    return {
        "travel_date": date,
        "holiday_score": score,
        "nearby_holidays": [h.name for h in holidays],
    }
