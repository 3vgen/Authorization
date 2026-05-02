from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.users.models.model_user import User
from app.users.models.model_refresh_token import RefreshToken
from app.users.schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse

from app.services.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token

)


# utc now – устарвший подход
# хранить токен в виде хэша

async def register(db: AsyncSession, data: RegisterRequest) -> User:
    is_user = await db.execute(select(User).where(User.username == data.username))
    if is_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already registered")

    new_user = User(
        username=data.username,
        hashed_password=hash_password(data.password)
    )

    db.add(new_user)
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

    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(db_token)

    user.last_login_at = datetime.utcnow()
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh(db: AsyncSession, refresh_token: str) -> TokenResponse:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    db_token: RefreshToken | None = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token revoked or expired")

    await db.delete(db_token)

    new_access_token = create_access_token(db_token.user_id)
    new_refresh_token = create_refresh_token(db_token.user_id)

    new_db_token = RefreshToken(
        user_id=db_token.user_id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(new_db_token)
    await db.commit()
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


async def logout(db: AsyncSession, refresh_token: str) -> None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(status_code=401, detail="Token not found")

    await db.delete(db_token)
    await db.commit()
