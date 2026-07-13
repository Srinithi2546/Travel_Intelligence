from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.models import Route, TransportMode
from app.schemas.schemas import RouteOption, RouteSearchResponse


# ── Seed Data Helper ─────────────────────────────────────────────────────────

SAMPLE_ROUTES = [
    # Chennai ↔ Bangalore
    {"src": "Chennai", "dst": "Bangalore", "mode": "train", "op": "Indian Railways",
     "rno": "12007", "dep": "06:00", "arr": "10:30", "dur": 270, "fare": 450, "ac": True,
     "amenities": ["WiFi", "Pantry", "Charging Points"]},
    {"src": "Chennai", "dst": "Bangalore", "mode": "bus", "op": "TNSTC",
     "rno": "TN-BLR-01", "dep": "22:00", "arr": "05:30", "dur": 450, "fare": 320, "ac": True,
     "amenities": ["AC", "Reclining Seats"]},
    {"src": "Chennai", "dst": "Bangalore", "mode": "bus", "op": "RedBus Express",
     "rno": "RB-001", "dep": "21:30", "arr": "06:00", "dur": 510, "fare": 650, "ac": True,
     "amenities": ["AC", "Blanket", "Charging Points", "Water Bottle"]},
    # Mumbai ↔ Pune
    {"src": "Mumbai", "dst": "Pune", "mode": "train", "op": "Indian Railways",
     "rno": "12127", "dep": "07:10", "arr": "10:45", "dur": 215, "fare": 280, "ac": False,
     "amenities": ["Pantry"]},
    {"src": "Mumbai", "dst": "Pune", "mode": "bus", "op": "MSRTC Shivneri",
     "rno": "SHV-09", "dep": "06:30", "arr": "10:00", "dur": 210, "fare": 260, "ac": True,
     "amenities": ["AC", "Push-Back Seats"]},
    # Delhi ↔ Agra
    {"src": "Delhi", "dst": "Agra", "mode": "train", "op": "Indian Railways",
     "rno": "12002", "dep": "06:00", "arr": "07:58", "dur": 118, "fare": 750, "ac": True,
     "amenities": ["WiFi", "Breakfast", "Charging Points"]},
    {"src": "Delhi", "dst": "Agra", "mode": "bus", "op": "UPSRTC",
     "rno": "UP-AGA-03", "dep": "07:00", "arr": "11:00", "dur": 240, "fare": 250, "ac": False,
     "amenities": ["Reclining Seats"]},
    # Hyderabad ↔ Vijayawada
    {"src": "Hyderabad", "dst": "Vijayawada", "mode": "train", "op": "Indian Railways",
     "rno": "12703", "dep": "06:25", "arr": "10:40", "dur": 255, "fare": 340, "ac": False,
     "amenities": ["Pantry"]},
    {"src": "Hyderabad", "dst": "Vijayawada", "mode": "bus", "op": "APSRTC Garuda",
     "rno": "AP-VJA-07", "dep": "21:00", "arr": "04:00", "dur": 420, "fare": 480, "ac": True,
     "amenities": ["AC", "Blanket", "Water Bottle"]},
]


async def seed_routes(db: AsyncSession) -> None:
    for r in SAMPLE_ROUTES:
        stmt = select(Route).where(
            and_(
                Route.source_city == r["src"],
                Route.destination_city == r["dst"],
                Route.route_number == r["rno"],
            )
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue
        db.add(Route(
            source_city=r["src"],
            destination_city=r["dst"],
            transport_mode=TransportMode(r["mode"]),
            operator_name=r["op"],
            route_number=r["rno"],
            departure_time=r["dep"],
            arrival_time=r["arr"],
            duration_minutes=r["dur"],
            base_fare=r["fare"],
            is_ac=r["ac"],
            amenities=r["amenities"],
        ))
    await db.flush()


# ── Search ───────────────────────────────────────────────────────────────────

async def search_routes(
    source: str,
    destination: str,
    travel_date: date,
    db: AsyncSession,
    transport_mode: Optional[TransportMode] = None,
    num_travelers: int = 1,
) -> RouteSearchResponse:
    source = source.strip().title()
    destination = destination.strip().title()

    conditions = [
        or_(
            and_(Route.source_city == source, Route.destination_city == destination),
            and_(Route.source_city == destination, Route.destination_city == source),
        ),
        Route.is_active == True,
    ]
    if transport_mode:
        conditions.append(Route.transport_mode == transport_mode)

    stmt = select(Route).where(and_(*conditions)).order_by(Route.base_fare)
    result = await db.execute(stmt)
    routes = result.scalars().all()

    bus_options: List[RouteOption] = []
    train_options: List[RouteOption] = []

    for r in routes:
        option = RouteOption(
            id=r.id,
            source_city=r.source_city,
            destination_city=r.destination_city,
            transport_mode=r.transport_mode,
            operator_name=r.operator_name,
            route_number=r.route_number,
            departure_time=r.departure_time,
            arrival_time=r.arrival_time,
            duration_minutes=r.duration_minutes,
            base_fare=r.base_fare,
            total_fare=round(r.base_fare * num_travelers, 2) if r.base_fare else None,
            is_ac=r.is_ac,
            amenities=r.amenities or [],
        )
        if r.transport_mode == TransportMode.BUS:
            bus_options.append(option)
        elif r.transport_mode == TransportMode.TRAIN:
            train_options.append(option)

    return RouteSearchResponse(
        source=source,
        destination=destination,
        travel_date=travel_date,
        bus_options=bus_options,
        train_options=train_options,
        total_results=len(bus_options) + len(train_options),
    )
