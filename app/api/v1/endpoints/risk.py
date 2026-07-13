from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.db.session import get_db
from app.schemas.schemas import RiskOut
from app.services.risk_service import compute_risk

router = APIRouter(prefix="/risk", tags=["Risk Prediction"])


@router.get("/", response_model=RiskOut)
async def travel_risk(
    source: str = Query(...),
    destination: str = Query(...),
    date: date = Query(..., description="Travel date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compute the overall travel risk score for a route and date.

    Combines:
    - Holiday demand score
    - Weather risk score
    - Traffic congestion score
    - Overall demand pressure

    Returns a 0–10 risk meter + actionable recommendations.
    """
    return await compute_risk(
        source=source,
        destination=destination,
        travel_date=date,
        db=db,
    )
