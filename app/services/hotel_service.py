from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import Hotel
from app.schemas.schemas import HotelOut


# ── Seed Data ────────────────────────────────────────────────────────────────

SAMPLE_HOTELS = [
    {"name": "Taj Coromandel", "city": "Chennai", "lat": 13.0609, "lon": 80.2518,
     "stars": 5, "price": 8500, "rating": 4.6, "reviews": 3200,
     "amenities": ["Pool", "Spa", "Gym", "Restaurant", "Bar", "WiFi", "Valet Parking"]},
    {"name": "The Leela Palace", "city": "Chennai", "lat": 12.9836, "lon": 80.2542,
     "stars": 5, "price": 9200, "rating": 4.7, "reviews": 2800,
     "amenities": ["Pool", "Spa", "Gym", "Restaurant", "Club Lounge", "WiFi"]},
    {"name": "GRT Grand", "city": "Chennai", "lat": 13.0599, "lon": 80.2520,
     "stars": 4, "price": 4500, "rating": 4.3, "reviews": 1800,
     "amenities": ["Restaurant", "Gym", "WiFi", "Business Center"]},
    {"name": "FabHotel Prime Select", "city": "Chennai", "lat": 13.0478, "lon": 80.2535,
     "stars": 3, "price": 1800, "rating": 3.9, "reviews": 950,
     "amenities": ["WiFi", "AC", "TV"]},
    {"name": "The Oberoi", "city": "Bangalore", "lat": 12.9634, "lon": 77.5925,
     "stars": 5, "price": 12000, "rating": 4.8, "reviews": 4100,
     "amenities": ["Pool", "Spa", "Gym", "Restaurant", "Bar", "Butler Service", "WiFi"]},
    {"name": "Lemon Tree Premier", "city": "Bangalore", "lat": 12.9783, "lon": 77.6408,
     "stars": 4, "price": 3800, "rating": 4.2, "reviews": 2200,
     "amenities": ["Restaurant", "Gym", "WiFi", "Pool"]},
    {"name": "Zostel Bangalore", "city": "Bangalore", "lat": 12.9584, "lon": 77.6539,
     "stars": 2, "price": 700, "rating": 4.0, "reviews": 1100,
     "amenities": ["WiFi", "Common Area", "Locker", "Laundry"]},
    {"name": "The Taj Mahal Hotel", "city": "Mumbai", "lat": 18.9217, "lon": 72.8331,
     "stars": 5, "price": 25000, "rating": 4.9, "reviews": 8900,
     "amenities": ["Sea View", "Pool", "Spa", "Multiple Restaurants", "Bar", "Butler", "WiFi"]},
    {"name": "ITC Maratha", "city": "Mumbai", "lat": 19.0954, "lon": 72.8638,
     "stars": 5, "price": 11000, "rating": 4.6, "reviews": 3600,
     "amenities": ["Pool", "Spa", "Gym", "Restaurant", "Bar", "WiFi"]},
    {"name": "Novotel Mumbai Juhu Beach", "city": "Mumbai", "lat": 19.0989, "lon": 72.8268,
     "stars": 4, "price": 6500, "rating": 4.3, "reviews": 2700,
     "amenities": ["Beach View", "Pool", "Restaurant", "Gym", "WiFi"]},
    {"name": "The Imperial", "city": "Delhi", "lat": 28.6248, "lon": 77.2229,
     "stars": 5, "price": 18000, "rating": 4.7, "reviews": 5600,
     "amenities": ["Heritage Property", "Pool", "Spa", "Multiple Restaurants", "WiFi"]},
    {"name": "Hyatt Regency Delhi", "city": "Delhi", "lat": 28.5621, "lon": 77.1919,
     "stars": 5, "price": 9800, "rating": 4.5, "reviews": 4200,
     "amenities": ["Pool", "Spa", "Gym", "Restaurant", "Bar", "WiFi"]},
    {"name": "Hotel Clarks Shiraz", "city": "Agra", "lat": 27.1767, "lon": 78.0081,
     "stars": 4, "price": 5500, "rating": 4.4, "reviews": 3100,
     "amenities": ["Taj View", "Pool", "Restaurant", "WiFi", "Travel Desk"]},
    {"name": "Trident Hyderabad", "city": "Hyderabad", "lat": 17.4449, "lon": 78.3867,
     "stars": 5, "price": 8000, "rating": 4.5, "reviews": 2900,
     "amenities": ["Pool", "Spa", "Gym", "Restaurant", "WiFi"]},
]


async def seed_hotels(db: AsyncSession) -> None:
    for h in SAMPLE_HOTELS:
        stmt = select(Hotel).where(
            and_(Hotel.name == h["name"], Hotel.city == h["city"])
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue
        db.add(Hotel(
            name=h["name"],
            city=h["city"],
            latitude=h["lat"],
            longitude=h["lon"],
            star_rating=h["stars"],
            avg_price_per_night=h["price"],
            google_rating=h["rating"],
            total_reviews=h["reviews"],
            amenities=h["amenities"],
        ))
    await db.flush()


# ── Search ───────────────────────────────────────────────────────────────────

async def search_hotels(
    city: str,
    check_in: date,
    check_out: date,
    db: AsyncSession,
    num_guests: int = 1,
    max_price: Optional[float] = None,
    min_stars: Optional[int] = None,
) -> List[HotelOut]:
    city = city.strip().title()
    nights = max((check_out - check_in).days, 1)

    conditions = [Hotel.city == city, Hotel.is_active == True]
    if max_price:
        conditions.append(Hotel.avg_price_per_night <= max_price)
    if min_stars:
        conditions.append(Hotel.star_rating >= min_stars)

    stmt = select(Hotel).where(and_(*conditions)).order_by(
        Hotel.google_rating.desc(), Hotel.avg_price_per_night
    )
    result = await db.execute(stmt)
    hotels = result.scalars().all()

    return [
        HotelOut(
            id=h.id,
            name=h.name,
            city=h.city,
            address=h.address,
            latitude=h.latitude,
            longitude=h.longitude,
            star_rating=h.star_rating,
            avg_price_per_night=h.avg_price_per_night,
            total_price=round(h.avg_price_per_night * nights, 2) if h.avg_price_per_night else None,
            amenities=h.amenities or [],
            google_rating=h.google_rating,
            total_reviews=h.total_reviews,
            image_urls=h.image_urls or [],
        )
        for h in hotels
    ]
