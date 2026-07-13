from datetime import date, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, extract
from app.models.models import Holiday
from app.schemas.schemas import HolidayOut


# ── Seed Data (Indian National + Major Festival Holidays) ────────────────────

SEED_HOLIDAYS = [
    # National holidays
    {"name": "Republic Day", "date": "01-26", "type": "national", "multiplier": 2.5},
    {"name": "Independence Day", "date": "08-15", "type": "national", "multiplier": 2.5},
    {"name": "Gandhi Jayanti", "date": "10-02", "type": "national", "multiplier": 1.8},
    {"name": "Christmas", "date": "12-25", "type": "national", "multiplier": 2.2},
    # Festivals (approximate dates — should be updated yearly)
    {"name": "Holi", "date": "03-14", "type": "festival", "multiplier": 2.8},
    {"name": "Diwali", "date": "11-01", "type": "festival", "multiplier": 3.0},
    {"name": "Dussehra", "date": "10-12", "type": "festival", "multiplier": 2.5},
    {"name": "Eid ul-Fitr", "date": "04-10", "type": "festival", "multiplier": 2.8},
    {"name": "Navratri Start", "date": "10-03", "type": "festival", "multiplier": 2.0},
    {"name": "New Year", "date": "01-01", "type": "festival", "multiplier": 2.9},
    {"name": "New Year Eve", "date": "12-31", "type": "festival", "multiplier": 2.8},
    {"name": "Makar Sankranti", "date": "01-14", "type": "festival", "multiplier": 1.8},
    {"name": "Pongal", "date": "01-15", "type": "festival", "multiplier": 1.8},
    {"name": "Onam", "date": "09-07", "type": "festival", "multiplier": 2.0},
    {"name": "Baisakhi", "date": "04-13", "type": "festival", "multiplier": 1.7},
]


async def seed_holidays(db: AsyncSession, year: int = 2025) -> None:
    """Seeds DB with holiday data for the given year if not already present."""
    for h in SEED_HOLIDAYS:
        month, day = map(int, h["date"].split("-"))
        holiday_date = date(year, month, day)

        exists_stmt = select(Holiday).where(
            and_(Holiday.name == h["name"], Holiday.date == holiday_date)
        )
        result = await db.execute(exists_stmt)
        if result.scalar_one_or_none():
            continue

        db.add(Holiday(
            name=h["name"],
            date=holiday_date,
            holiday_type=h["type"],
            state=None,
            demand_multiplier=h["multiplier"],
        ))
    await db.flush()


# ── Detection Logic ──────────────────────────────────────────────────────────

async def get_holidays_near_date(
    travel_date: date,
    db: AsyncSession,
    window_days: int = 3,
) -> List[HolidayOut]:
    """Returns holidays within ±window_days of travel_date."""
    start = travel_date - timedelta(days=window_days)
    end = travel_date + timedelta(days=window_days)

    stmt = select(Holiday).where(
        and_(Holiday.date >= start, Holiday.date <= end)
    ).order_by(Holiday.date)

    result = await db.execute(stmt)
    holidays = result.scalars().all()
    return [HolidayOut.model_validate(h) for h in holidays]


def compute_holiday_risk_score(holidays: List[HolidayOut], travel_date: date) -> float:
    """
    Calculates 0–10 holiday risk score.
    Same-day holiday = full weight; adjacent days = partial weight.
    """
    if not holidays:
        return 0.0

    max_score = 0.0
    for h in holidays:
        gap = abs((h.date - travel_date).days)
        decay = 1.0 if gap == 0 else 0.6 if gap == 1 else 0.3
        score = (h.demand_multiplier / 3.0) * 10 * decay
        max_score = max(max_score, score)

    return round(min(max_score, 10), 2)


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # Saturday = 5, Sunday = 6


def is_long_weekend(d: date, holidays: List[HolidayOut]) -> bool:
    holiday_dates = {h.date for h in holidays}
    # Check if the date forms a 3+ day stretch with weekends
    for delta in range(-2, 3):
        check = d + timedelta(days=delta)
        if check in holiday_dates:
            # See if we get a 3-day weekend
            streak = 0
            for i in range(-2, 3):
                day = d + timedelta(days=i)
                if day.weekday() >= 5 or day in holiday_dates:
                    streak += 1
            return streak >= 3
    return False
