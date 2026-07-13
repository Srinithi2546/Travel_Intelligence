from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import asyncio
from app.db.session import get_db
from app.schemas.schemas import DashboardRequest, DashboardResponse
from app.services.route_service import search_routes
from app.services.weather_service import get_weather
from app.services.holiday_service import get_holidays_near_date
from app.services.risk_service import compute_risk
from app.services.hotel_service import search_hotels

router = APIRouter(prefix="/dashboard", tags=["Smart Dashboard"])


@router.post("/", response_model=DashboardResponse)
async def smart_dashboard(
    req: DashboardRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    🧠 Smart Travel Intelligence Dashboard

    Single endpoint that aggregates ALL modules:
    - Route options (bus + train)
    - Source & destination weather
    - Nearby holidays
    - Travel risk score + recommendations
    - Hotel suggestions at destination

    Use this to power the main frontend dashboard view.
    """
    check_out = req.check_out_date or (req.travel_date + timedelta(days=1))

    # Run independent queries concurrently
    routes_task = search_routes(req.source, req.destination, req.travel_date, db, num_travelers=req.num_travelers)
    weather_src_task = get_weather(req.source, req.travel_date, db)
    weather_dst_task = get_weather(req.destination, req.travel_date, db)
    holidays_task = get_holidays_near_date(req.travel_date, db)
    risk_task = compute_risk(req.source, req.destination, req.travel_date, db)
    hotels_task = search_hotels(req.destination, req.travel_date, check_out, db)

    (
        routes,
        weather_src,
        weather_dst,
        holidays,
        risk,
        hotels,
    ) = await asyncio.gather(
        routes_task,
        weather_src_task,
        weather_dst_task,
        holidays_task,
        risk_task,
        hotels_task,
        return_exceptions=True,
    )

    # Graceful degradation — if a module fails, return None for that section
    return DashboardResponse(
        routes=routes if not isinstance(routes, Exception) else None,
        weather_source=weather_src if not isinstance(weather_src, Exception) else None,
        weather_destination=weather_dst if not isinstance(weather_dst, Exception) else None,
        holidays=holidays if not isinstance(holidays, Exception) else [],
        risk=risk if not isinstance(risk, Exception) else None,
        hotels=hotels if not isinstance(hotels, Exception) else [],
    )
