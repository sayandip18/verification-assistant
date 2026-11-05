from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Officer, OfficerRole
from app.security import hash_password


async def seed_demo_officer(db: AsyncSession) -> None:
    email = settings.seed_officer_email.strip().lower()
    existing = await db.scalar(select(Officer).where(Officer.email == email))
    if existing:
        return
    db.add(
        Officer(
            employee_id=settings.seed_officer_employee_id,
            email=email,
            full_name=settings.seed_officer_name,
            password_hash=hash_password(settings.seed_officer_password),
            role=OfficerRole.REVENUE_INSPECTOR,
            office_code="DEMO-BLLRO",
        )
    )
    await db.commit()
