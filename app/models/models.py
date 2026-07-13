from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    Text, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class TransportMode(str, enum.Enum):
    BUS = "bus"
    TRAIN = "train"
    FLIGHT = "flight"
    CAB = "cab"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TrafficLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# ── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    itineraries = relationship("Itinerary", back_populates="user", cascade="all, delete")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    preferred_transport = Column(Enum(TransportMode), default=TransportMode.TRAIN)
    max_budget = Column(Float, nullable=True)
    notify_weather = Column(Boolean, default=True)
    notify_holiday = Column(Boolean, default=True)

    user = relationship("User", back_populates="preferences")


# ── Route ────────────────────────────────────────────────────────────────────

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    source_city = Column(String(100), nullable=False, index=True)
    destination_city = Column(String(100), nullable=False, index=True)
    transport_mode = Column(Enum(TransportMode), nullable=False)
    operator_name = Column(String(150))
    route_number = Column(String(50))
    departure_time = Column(String(10))       # HH:MM
    arrival_time = Column(String(10))
    duration_minutes = Column(Integer)
    base_fare = Column(Float)
    is_ac = Column(Boolean, default=False)
    amenities = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source_city", "destination_city", "transport_mode", "route_number"),
    )


# ── Hotel ────────────────────────────────────────────────────────────────────

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    star_rating = Column(Integer)             # 1-5
    avg_price_per_night = Column(Float)
    amenities = Column(JSON, default=list)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    website_url = Column(String(500))
    google_rating = Column(Float)
    total_reviews = Column(Integer, default=0)
    image_urls = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Holiday ──────────────────────────────────────────────────────────────────

class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    date = Column(Date, nullable=False, index=True)
    holiday_type = Column(String(50))        # national, regional, festival
    state = Column(String(100), nullable=True)   # NULL = national
    demand_multiplier = Column(Float, default=1.0)  # 1.0–3.0
    description = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("name", "date"),)


# ── Weather Log ──────────────────────────────────────────────────────────────

class WeatherLog(Base):
    __tablename__ = "weather_logs"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    temperature_min = Column(Float)
    temperature_max = Column(Float)
    humidity = Column(Float)
    rain_probability = Column(Float)         # 0–100
    rain_mm = Column(Float, default=0)
    fog_alert = Column(Boolean, default=False)
    wind_speed_kmh = Column(Float)
    weather_condition = Column(String(100))
    travel_advice = Column(Text)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("city", "date"),)


# ── Risk Prediction ──────────────────────────────────────────────────────────

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    source_city = Column(String(100), nullable=False)
    destination_city = Column(String(100), nullable=False)
    travel_date = Column(Date, nullable=False, index=True)
    holiday_score = Column(Float, default=0)    # 0–10
    weather_score = Column(Float, default=0)
    traffic_score = Column(Float, default=0)
    demand_score = Column(Float, default=0)
    overall_risk_score = Column(Float, nullable=False)  # 0–10
    risk_level = Column(Enum(RiskLevel))
    traffic_level = Column(Enum(TrafficLevel))
    recommendations = Column(JSON, default=list)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


# ── Itinerary ────────────────────────────────────────────────────────────────

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200))
    source_city = Column(String(100), nullable=False)
    destination_city = Column(String(100), nullable=False)
    travel_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    num_travelers = Column(Integer, default=1)
    selected_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    selected_hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)
    risk_prediction_id = Column(Integer, ForeignKey("risk_predictions.id"), nullable=True)
    notes = Column(Text)
    total_estimated_cost = Column(Float)
    status = Column(String(30), default="draft")   # draft, confirmed, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="itineraries")
    route = relationship("Route")
    hotel = relationship("Hotel")
    risk = relationship("RiskPrediction")
