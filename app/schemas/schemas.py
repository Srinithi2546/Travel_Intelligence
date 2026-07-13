from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import date, datetime
from app.models.models import TransportMode, RiskLevel, TrafficLevel


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Route ────────────────────────────────────────────────────────────────────

class RouteSearchRequest(BaseModel):
    source: str
    destination: str
    date: date
    transport_mode: Optional[TransportMode] = None
    num_travelers: int = 1


class RouteOption(BaseModel):
    id: int
    source_city: str
    destination_city: str
    transport_mode: TransportMode
    operator_name: Optional[str]
    route_number: Optional[str]
    departure_time: Optional[str]
    arrival_time: Optional[str]
    duration_minutes: Optional[int]
    base_fare: Optional[float]
    total_fare: Optional[float]        # base_fare * num_travelers
    is_ac: bool
    amenities: List[str] = []
    availability: str = "available"

    class Config:
        from_attributes = True


class RouteSearchResponse(BaseModel):
    source: str
    destination: str
    travel_date: date
    bus_options: List[RouteOption] = []
    train_options: List[RouteOption] = []
    total_results: int


# ── Hotel ────────────────────────────────────────────────────────────────────

class HotelSearchRequest(BaseModel):
    city: str
    check_in: date
    check_out: date
    num_guests: int = 1
    max_price: Optional[float] = None
    min_stars: Optional[int] = None


class HotelOut(BaseModel):
    id: int
    name: str
    city: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    star_rating: Optional[int]
    avg_price_per_night: Optional[float]
    total_price: Optional[float]        # price * nights
    amenities: List[str] = []
    google_rating: Optional[float]
    total_reviews: int
    image_urls: List[str] = []

    class Config:
        from_attributes = True


# ── Weather ──────────────────────────────────────────────────────────────────

class WeatherRequest(BaseModel):
    city: str
    date: date


class WeatherOut(BaseModel):
    city: str
    date: date
    temperature_min: Optional[float]
    temperature_max: Optional[float]
    humidity: Optional[float]
    rain_probability: Optional[float]
    fog_alert: bool
    wind_speed_kmh: Optional[float]
    weather_condition: Optional[str]
    travel_advice: Optional[str]

    class Config:
        from_attributes = True


# ── Holiday ──────────────────────────────────────────────────────────────────

class HolidayOut(BaseModel):
    id: int
    name: str
    date: date
    holiday_type: str
    state: Optional[str]
    demand_multiplier: float
    description: Optional[str]

    class Config:
        from_attributes = True


# ── Risk ─────────────────────────────────────────────────────────────────────

class RiskRequest(BaseModel):
    source: str
    destination: str
    travel_date: date


class RiskOut(BaseModel):
    source_city: str
    destination_city: str
    travel_date: date
    holiday_score: float
    weather_score: float
    traffic_score: float
    demand_score: float
    overall_risk_score: float
    risk_level: RiskLevel
    traffic_level: TrafficLevel
    recommendations: List[str] = []

    class Config:
        from_attributes = True


# ── Itinerary ─────────────────────────────────────────────────────────────────

class ItineraryCreate(BaseModel):
    title: Optional[str] = None
    source_city: str
    destination_city: str
    travel_date: date
    return_date: Optional[date] = None
    num_travelers: int = 1
    selected_route_id: Optional[int] = None
    selected_hotel_id: Optional[int] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.return_date and self.return_date <= self.travel_date:
            raise ValueError("return_date must be after travel_date")
        return self


class ItineraryUpdate(BaseModel):
    title: Optional[str] = None
    selected_route_id: Optional[int] = None
    selected_hotel_id: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ItineraryOut(BaseModel):
    id: int
    title: Optional[str]
    source_city: str
    destination_city: str
    travel_date: date
    return_date: Optional[date]
    num_travelers: int
    notes: Optional[str]
    total_estimated_cost: Optional[float]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ────────────────────────────────────────────────────────────────

class DashboardRequest(BaseModel):
    source: str
    destination: str
    travel_date: date
    num_travelers: int = 1
    check_out_date: Optional[date] = None


class DashboardResponse(BaseModel):
    routes: RouteSearchResponse
    weather_source: Optional[WeatherOut]
    weather_destination: Optional[WeatherOut]
    holidays: List[HolidayOut]
    risk: Optional[RiskOut]
    hotels: List[HotelOut]
