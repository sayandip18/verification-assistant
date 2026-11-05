from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_officer
from app.models import Officer, utcnow
from app.schemas import LoginRequest, OfficerOut
from app.security import (
    clear_session_cookie,
    create_access_token,
    set_session_cookie,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=OfficerOut)
async def login(
    payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> Officer:
    email = str(payload.email).strip().lower()
    officer = await db.scalar(select(Officer).where(Officer.email == email))
    if officer is None or not officer.is_active or not verify_password(payload.password, officer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    officer.last_login_at = utcnow()
    await db.commit()
    await db.refresh(officer)
    set_session_cookie(response, create_access_token(officer.id))
    return officer


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=OfficerOut)
async def me(officer: Officer = Depends(get_current_officer)) -> Officer:
    return officer
