import aiohttp
import json
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import WeatherLog
from app.schemas.schemas import WeatherOut
from app.core.config import settings


# ── Weather Advice Engine ────────────────────────────────────────────────────

def _generate_travel_advice(data: dict) -> str:
    advice_parts = []

    rain_prob = data.get("rain_probability", 0)
    fog = data.get("fog_alert", False)
    temp_max = data.get("temperature_max", 25)
    wind = data.get("wind_speed_kmh", 0)

    if rain_prob >= 80:
        advice_parts.append("Heavy rain expected — carry rain gear and expect delays")
    elif rain_prob >= 50:
        advice_parts.append("Moderate rain likely — keep an umbrella handy")
    elif rain_prob >= 30:
        advice_parts.append("Light showers possible")

    if fog:
        advice_parts.append("Dense fog alert — travel delays likely, avoid early morning travel")

    if temp_max >= 42:
        advice_parts.append("Extreme heat — stay hydrated and travel during cooler hours")
    elif temp_max >= 38:
        advice_parts.append("Very hot conditions — carry water")

    if wind >= 60:
        advice_parts.append("Strong winds — may affect bus/cab routes")

    return ". ".join(advice_parts) if advice_parts else "Weather conditions are favorable for travel"


def _compute_weather_score(rain_prob: float, fog: bool, temp_max: float, wind: float) -> float:
    """Returns 0–10 where 10 = worst weather for travel."""
    score = 0.0
    score += min(rain_prob / 10, 4)    # max 4 pts from rain
    if fog:
        score += 2.5
    if temp_max >= 42:
        score += 2
    elif temp_max >= 38:
        score += 1
    score += min(wind / 30, 1.5)       # max 1.5 pts from wind
    return round(min(score, 10), 2)


# ── OpenWeatherMap Fetch ─────────────────────────────────────────────────────

async def _fetch_from_openweather(city: str, target_date: date) -> Optional[dict]:
    """Fetches 5-day forecast from OpenWeatherMap and extracts target date data."""
    if not settings.OPENWEATHER_API_KEY:
        return None

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": f"{city},IN",
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "cnt": 40,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                raw = await resp.json()

        # Filter forecast items for the target date
        target_str = target_date.strftime("%Y-%m-%d")
        items = [
            item for item in raw.get("list", [])
            if item["dt_txt"].startswith(target_str)
        ]

        if not items:
            return None

        temps = [i["main"]["temp"] for i in items]
        humidities = [i["main"]["humidity"] for i in items]
        rain_probs = [i.get("pop", 0) * 100 for i in items]
        rain_mm = sum(i.get("rain", {}).get("3h", 0) for i in items)
        wind_speeds = [i["wind"]["speed"] * 3.6 for i in items]  # m/s → km/h
        conditions = [i["weather"][0]["main"] for i in items]

        fog_alert = any(c in ["Fog", "Mist", "Haze", "Smoke"] for c in conditions)
        dominant_condition = max(set(conditions), key=conditions.count)

        return {
            "temperature_min": round(min(temps), 1),
            "temperature_max": round(max(temps), 1),
            "humidity": round(sum(humidities) / len(humidities), 1),
            "rain_probability": round(max(rain_probs), 1),
            "rain_mm": round(rain_mm, 2),
            "fog_alert": fog_alert,
            "wind_speed_kmh": round(max(wind_speeds), 1),
            "weather_condition": dominant_condition,
        }
    except Exception:
        return None


# ── Mock Fallback ────────────────────────────────────────────────────────────

def _mock_weather(city: str, target_date: date) -> dict:
    """Returns deterministic mock weather when API key is absent (dev mode)."""
    import hashlib
    seed = int(hashlib.md5(f"{city}{target_date}".encode()).hexdigest(), 16) % 100
    return {
        "temperature_min": 18 + seed % 10,
        "temperature_max": 28 + seed % 15,
        "humidity": 50 + seed % 40,
        "rain_probability": seed % 70,
        "rain_mm": (seed % 20) * 0.5,
        "fog_alert": seed % 10 == 0,
        "wind_speed_kmh": 10 + seed % 40,
        "weather_condition": ["Clear", "Clouds", "Rain", "Haze"][seed % 4],
    }


# ── Main Service ─────────────────────────────────────────────────────────────

async def get_weather(city: str, target_date: date, db: AsyncSession) -> WeatherOut:
    city = city.strip().title()

    # 1. Check DB cache
    stmt = select(WeatherLog).where(
        and_(WeatherLog.city == city, WeatherLog.date == target_date)
    )
    result = await db.execute(stmt)
    cached = result.scalar_one_or_none()
    if cached:
        return WeatherOut.model_validate(cached)

    # 2. Fetch live or mock
    data = await _fetch_from_openweather(city, target_date)
    if data is None:
        data = _mock_weather(city, target_date)

    advice = _generate_travel_advice(data)

    # 3. Persist to DB
    log = WeatherLog(
        city=city,
        date=target_date,
        travel_advice=advice,
        **data,
    )
    db.add(log)
    await db.flush()

    return WeatherOut(
        city=city,
        date=target_date,
        travel_advice=advice,
        **data,
    )


def get_weather_risk_score(rain_prob: float, fog: bool, temp_max: float, wind: float) -> float:
    return _compute_weather_score(rain_prob, fog, temp_max, wind)
