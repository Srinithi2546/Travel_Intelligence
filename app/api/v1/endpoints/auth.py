from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserOut
from app.services.auth_service import register_user, authenticate_user, get_current_user
from app.core.security import create_access_token, create_refresh_token
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    user = await register_user(data, db)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT access + refresh tokens."""
    user = await authenticate_user(data.email, data.password, db)
    return TokenResponse(
        access_token=create_access_token(user.id, {"email": user.email}),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """Get authenticated user profile."""
    return current_user
