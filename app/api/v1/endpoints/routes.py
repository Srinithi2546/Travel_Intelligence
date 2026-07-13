from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional
from app.db.session import get_db
from app.schemas.schemas import RouteSearchResponse
from app.services.route_service import search_routes
from app.models.models import TransportMode

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("/search", response_model=RouteSearchResponse)
async def search(
    source: str = Query(..., description="Source city name"),
    destination: str = Query(..., description="Destination city name"),
    date: date = Query(..., description="Travel date (YYYY-MM-DD)"),
    transport_mode: Optional[TransportMode] = Query(None, description="Filter by mode"),
    num_travelers: int = Query(1, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Search available bus and train routes between cities.
    Returns grouped results with total fare for all travelers.
    """
    return await search_routes(
        source=source,
        destination=destination,
        travel_date=date,
        db=db,
        transport_mode=transport_mode,
        num_travelers=num_travelers,
    )
