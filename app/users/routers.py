# app/api/v1/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connections import get_db
from app.users.schemas import (
    RegisterRequest, LoginRequest,
    TokenResponse, UserResponse,
    RefreshRequest, LogoutRequest
)
from app.users import auth_services

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