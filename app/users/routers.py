# app/api/v1/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models.model_user import User
from app.db.connections import get_db
from app.users.schemas import (
    RegisterRequest, LoginRequest,
    TokenResponse, UserResponse,
    RefreshRequest, LogoutRequest
)
from app.users import auth_services
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_services.register(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_services.login(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_services.refresh(db, data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await auth_services.logout(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
