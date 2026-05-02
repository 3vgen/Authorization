from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.users.models.model_user import User
from app.users.models.model_refresh_token import RefreshToken
from app.users.schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse

from app.services.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token

)


async def register(db: AsyncSession, data: RegisterRequest) -> User:

    is_user = await db.execute(select(User).where(User.username == data.username))
    if is_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already registered")

    new_user = User(
        username=data.username,
        hashed_password=hash_password(data.password)
    )

    db.add(User)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid login or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    