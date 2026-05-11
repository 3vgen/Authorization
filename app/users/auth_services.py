from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.users.models.model_user import User
from app.users.models.model_refresh_token import RefreshToken
from app.users.schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse

from app.services.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token

)


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    new_user = User(
        username=data.username,
        hashed_password=hash_password(data.password)
    )
    try:
        db.add(new_user)
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "User already registered")
    return new_user


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid login or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    try:
        db_token = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        db.add(db_token)

        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh(db: AsyncSession, refresh_token: str) -> TokenResponse:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    db_token: RefreshToken | None = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Token revoked or expired")

    await db.delete(db_token)

    new_access_token = create_access_token(db_token.user_id)
    new_refresh_token = create_refresh_token(db_token.user_id)

    new_db_token = RefreshToken(
        user_id=db_token.user_id,
        token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(new_db_token)
    await db.commit()
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


async def logout(db: AsyncSession, refresh_token: str) -> None:
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token == refresh_token)
    )
    await db.commit()
