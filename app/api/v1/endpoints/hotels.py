from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional
from app.db.session import get_db
from app.schemas.schemas import HotelOut
from app.services.hotel_service import search_hotels

router = APIRouter(prefix="/hotels", tags=["Hotels"])


@router.get("/search", response_model=List[HotelOut])
async def search(
    city: str = Query(...),
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    num_guests: int = Query(1, ge=1, le=20),
    max_price: Optional[float] = Query(None, description="Max price per night (INR)"),
    min_stars: Optional[int] = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
):
    """
    Search hotels in a city for a date range.
    Results sorted by rating desc, then price asc.
    Total price shown for the entire stay duration.
    """
    return await search_hotels(
        city=city,
        check_in=check_in,
        check_out=check_out,
        db=db,
        num_guests=num_guests,
        max_price=max_price,
        min_stars=min_stars,
    )
