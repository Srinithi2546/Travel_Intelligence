"""
Unit tests for Smart Travel Backend core services.
Run with: pytest tests/ -v
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.services.holiday_service import compute_holiday_risk_score, is_weekend, is_long_weekend
from app.services.weather_service import _generate_travel_advice, _compute_weather_score, _mock_weather
from app.services.risk_service import (
    compute_traffic_score,
    compute_demand_score,
    classify_risk,
    classify_traffic,
    generate_recommendations,
)
from app.models.models import RiskLevel, TrafficLevel
from app.schemas.schemas import HolidayOut


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def diwali_holiday():
    return HolidayOut(
        id=1, name="Diwali", date=date(2025, 11, 1),
        holiday_type="festival", state=None, demand_multiplier=3.0,
        description=None,
    )


@pytest.fixture
def republic_day():
    return HolidayOut(
        id=2, name="Republic Day", date=date(2025, 1, 26),
        holiday_type="national", state=None, demand_multiplier=2.5,
        description=None,
    )


# ── Holiday Tests ─────────────────────────────────────────────────────────────

class TestHolidayService:

    def test_holiday_risk_score_same_day(self, diwali_holiday):
        score = compute_holiday_risk_score([diwali_holiday], date(2025, 11, 1))
        assert score == pytest.approx(10.0, abs=0.1)

    def test_holiday_risk_score_adjacent_day(self, diwali_holiday):
        score = compute_holiday_risk_score([diwali_holiday], date(2025, 11, 2))
        assert 0 < score < 10

    def test_holiday_risk_score_no_holidays(self):
        score = compute_holiday_risk_score([], date(2025, 6, 15))
        assert score == 0.0

    def test_is_weekend_saturday(self):
        assert is_weekend(date(2025, 1, 11)) is True  # Saturday

    def test_is_weekend_monday(self):
        assert is_weekend(date(2025, 1, 13)) is False  # Monday


# ── Weather Tests ─────────────────────────────────────────────────────────────

class TestWeatherService:

    def test_travel_advice_heavy_rain(self):
        data = {"rain_probability": 85, "fog_alert": False, "temperature_max": 28, "wind_speed_kmh": 15}
        advice = _generate_travel_advice(data)
        assert "rain" in advice.lower()

    def test_travel_advice_fog(self):
        data = {"rain_probability": 10, "fog_alert": True, "temperature_max": 18, "wind_speed_kmh": 5}
        advice = _generate_travel_advice(data)
        assert "fog" in advice.lower()

    def test_travel_advice_clear(self):
        data = {"rain_probability": 5, "fog_alert": False, "temperature_max": 27, "wind_speed_kmh": 10}
        advice = _generate_travel_advice(data)
        assert "favorable" in advice.lower()

    def test_weather_score_zero_for_clear(self):
        score = _compute_weather_score(5, False, 25, 10)
        assert score < 2.0

    def test_weather_score_high_for_bad_weather(self):
        score = _compute_weather_score(90, True, 42, 70)
        assert score >= 7.0

    def test_mock_weather_deterministic(self):
        w1 = _mock_weather("Chennai", date(2025, 12, 1))
        w2 = _mock_weather("Chennai", date(2025, 12, 1))
        assert w1 == w2

    def test_mock_weather_different_cities(self):
        w1 = _mock_weather("Chennai", date(2025, 12, 1))
        w2 = _mock_weather("Mumbai", date(2025, 12, 1))
        assert w1 != w2


# ── Risk Engine Tests ─────────────────────────────────────────────────────────

class TestRiskService:

    def test_classify_risk_low(self):
        assert classify_risk(2.0) == RiskLevel.LOW

    def test_classify_risk_moderate(self):
        assert classify_risk(4.5) == RiskLevel.MODERATE

    def test_classify_risk_high(self):
        assert classify_risk(6.5) == RiskLevel.HIGH

    def test_classify_risk_critical(self):
        assert classify_risk(8.5) == RiskLevel.CRITICAL

    def test_classify_traffic_low(self):
        assert classify_traffic(1.0) == TrafficLevel.LOW

    def test_classify_traffic_high(self):
        assert classify_traffic(7.0) == TrafficLevel.HIGH

    def test_recommendations_include_positive_when_safe(self):
        recs = generate_recommendations(RiskLevel.LOW, 0, 0, 0, [])
        assert any("✅" in r for r in recs)

    def test_recommendations_warn_on_critical(self):
        recs = generate_recommendations(RiskLevel.CRITICAL, 9, 8, 8, [])
        assert any("⚠️" in r for r in recs)

    def test_traffic_score_long_weekend(self, diwali_holiday):
        score = compute_traffic_score(date(2025, 11, 1), [diwali_holiday], 9.0)
        assert score >= 4.0

    def test_demand_score_bounded(self):
        score = compute_demand_score(10.0, 10.0, 10.0)
        assert 0 <= score <= 10.0
