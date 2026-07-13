from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.models import User, Itinerary
from app.schemas.schemas import ItineraryCreate, ItineraryUpdate, ItineraryOut
from app.services.auth_service import get_current_user
from app.services.risk_service import compute_risk

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


@router.post("/", response_model=ItineraryOut, status_code=201)
async def create_itinerary(
    data: ItineraryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create and save a travel itinerary for the authenticated user."""
    # Auto-compute risk for the trip
    risk = await compute_risk(data.source_city, data.destination_city, data.travel_date, db)

    itinerary = Itinerary(
        user_id=current_user.id,
        title=data.title or f"{data.source_city} → {data.destination_city}",
        source_city=data.source_city,
        destination_city=data.destination_city,
        travel_date=data.travel_date,
        return_date=data.return_date,
        num_travelers=data.num_travelers,
        selected_route_id=data.selected_route_id,
        selected_hotel_id=data.selected_hotel_id,
        notes=data.notes,
    )
    db.add(itinerary)
    await db.flush()
    await db.refresh(itinerary)
    return itinerary


@router.get("/", response_model=List[ItineraryOut])
async def list_itineraries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all itineraries for the authenticated user."""
    stmt = select(Itinerary).where(
        Itinerary.user_id == current_user.id
    ).order_by(Itinerary.travel_date.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{itinerary_id}", response_model=ItineraryOut)
async def get_itinerary(
    itinerary_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Itinerary).where(
        Itinerary.id == itinerary_id,
        Itinerary.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    itinerary = result.scalar_one_or_none()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary


@router.patch("/{itinerary_id}", response_model=ItineraryOut)
async def update_itinerary(
    itinerary_id: int,
    data: ItineraryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Itinerary).where(
        Itinerary.id == itinerary_id,
        Itinerary.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    itinerary = result.scalar_one_or_none()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(itinerary, field, value)

    await db.flush()
    await db.refresh(itinerary)
    return itinerary


@router.delete("/{itinerary_id}", status_code=204)
async def delete_itinerary(
    itinerary_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Itinerary).where(
        Itinerary.id == itinerary_id,
        Itinerary.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    itinerary = result.scalar_one_or_none()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    await db.delete(itinerary)
