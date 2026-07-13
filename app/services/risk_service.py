from datetime import date
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import RiskPrediction, RiskLevel, TrafficLevel
from app.schemas.schemas import RiskOut, HolidayOut
from app.services.weather_service import get_weather, get_weather_risk_score
from app.services.holiday_service import (
    get_holidays_near_date,
    compute_holiday_risk_score,
    is_weekend,
    is_long_weekend,
)


# ── Traffic Score Engine ─────────────────────────────────────────────────────

def compute_traffic_score(
    travel_date: date,
    holidays: List[HolidayOut],
    holiday_score: float,
) -> float:
    """0–10 traffic congestion score based on day type and holiday proximity."""
    score = 0.0

    if is_long_weekend(travel_date, holidays):
        score += 4.0
    elif is_weekend(travel_date):
        score += 2.5

    # Holiday proximity adds traffic
    score += min(holiday_score * 0.4, 4.0)

    # Peak tourism months: Oct–Nov, Dec–Jan, May–Jun
    month = travel_date.month
    if month in (10, 11, 12, 1):
        score += 1.5
    elif month in (5, 6):
        score += 1.0

    return round(min(score, 10), 2)


# ── Demand Score ─────────────────────────────────────────────────────────────

def compute_demand_score(
    holiday_score: float,
    traffic_score: float,
    weather_score: float,
) -> float:
    """Composite demand pressure score."""
    return round(min((holiday_score * 0.5 + traffic_score * 0.3 + weather_score * 0.2), 10), 2)


# ── Risk Level Classifier ────────────────────────────────────────────────────

def classify_risk(score: float) -> RiskLevel:
    if score >= 7.5:
        return RiskLevel.CRITICAL
    elif score >= 5.5:
        return RiskLevel.HIGH
    elif score >= 3.5:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_traffic(score: float) -> TrafficLevel:
    if score >= 6:
        return TrafficLevel.HIGH
    elif score >= 3:
        return TrafficLevel.MODERATE
    return TrafficLevel.LOW


# ── Recommendation Generator ─────────────────────────────────────────────────

def generate_recommendations(
    risk_level: RiskLevel,
    holiday_score: float,
    weather_score: float,
    traffic_score: float,
    holidays: List[HolidayOut],
) -> List[str]:
    recs = []

    if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        recs.append("⚠️ High-risk travel window — consider rescheduling by 2–3 days")

    if holiday_score >= 7:
        names = ", ".join(h.name for h in holidays[:2])
        recs.append(f"🎉 Major holiday period ({names}) — book tickets well in advance")

    if weather_score >= 6:
        recs.append("🌧️ Adverse weather expected — build buffer time into your schedule")
    elif weather_score >= 3:
        recs.append("🌦️ Weather may cause minor delays — check forecast before departure")

    if traffic_score >= 7:
        recs.append("🚦 Heavy traffic expected — prefer early morning or late evening travel")
    elif traffic_score >= 4:
        recs.append("🚗 Moderate traffic — avoid peak hours (8–10 AM, 5–8 PM)")

    if not recs:
        recs.append("✅ Conditions look good for travel")
        recs.append("📋 Book tickets at least 2 days in advance for best fares")

    recs.append("🏨 Pre-book your hotel to avoid last-minute price surges")
    return recs


# ── Main Service ─────────────────────────────────────────────────────────────

async def compute_risk(
    source: str,
    destination: str,
    travel_date: date,
    db: AsyncSession,
) -> RiskOut:
    source = source.strip().title()
    destination = destination.strip().title()

    # Check cache
    stmt = select(RiskPrediction).where(
        and_(
            RiskPrediction.source_city == source,
            RiskPrediction.destination_city == destination,
            RiskPrediction.travel_date == travel_date,
        )
    )
    result = await db.execute(stmt)
    cached = result.scalar_one_or_none()
    if cached:
        return RiskOut.model_validate(cached)

    # Gather inputs
    holidays = await get_holidays_near_date(travel_date, db)
    dest_weather = await get_weather(destination, travel_date, db)

    # Compute individual scores
    holiday_score = compute_holiday_risk_score(holidays, travel_date)
    weather_score = get_weather_risk_score(
        rain_prob=dest_weather.rain_probability or 0,
        fog=dest_weather.fog_alert,
        temp_max=dest_weather.temperature_max or 30,
        wind=dest_weather.wind_speed_kmh or 0,
    )
    traffic_score = compute_traffic_score(travel_date, holidays, holiday_score)
    demand_score = compute_demand_score(holiday_score, traffic_score, weather_score)

    # Weighted overall score
    overall = round(
        holiday_score * 0.30
        + weather_score * 0.25
        + traffic_score * 0.25
        + demand_score * 0.20,
        2,
    )
    risk_level = classify_risk(overall)
    traffic_level = classify_traffic(traffic_score)
    recommendations = generate_recommendations(
        risk_level, holiday_score, weather_score, traffic_score, holidays
    )

    # Persist
    prediction = RiskPrediction(
        source_city=source,
        destination_city=destination,
        travel_date=travel_date,
        holiday_score=holiday_score,
        weather_score=weather_score,
        traffic_score=traffic_score,
        demand_score=demand_score,
        overall_risk_score=overall,
        risk_level=risk_level,
        traffic_level=traffic_level,
        recommendations=recommendations,
    )
    db.add(prediction)
    await db.flush()

    return RiskOut(
        source_city=source,
        destination_city=destination,
        travel_date=travel_date,
        holiday_score=holiday_score,
        weather_score=weather_score,
        traffic_score=traffic_score,
        demand_score=demand_score,
        overall_risk_score=overall,
        risk_level=risk_level,
        traffic_level=traffic_level,
        recommendations=recommendations,
    )
