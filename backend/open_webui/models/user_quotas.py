import time
from typing import Optional

from sqlalchemy import select
from open_webui.internal.db import Base, get_async_db_context

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
)


class UserQuota(Base):
    __tablename__ = "user_quota"

    user_id = Column(String, primary_key=True, unique=True)
    request_count = Column(Integer, default=0)
    quota_date = Column(String)
    updated_at = Column(BigInteger)


class UserQuotaModel(BaseModel):
    user_id: str
    request_count: int
    quota_date: str
    updated_at: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserQuotasTable:
    async def get_by_user_id(
        self, user_id: str, db: Optional = None
    ) -> Optional[UserQuotaModel]:
        try:
            async with get_async_db_context(db) as db:
                result = await db.execute(
                    select(UserQuota).filter_by(user_id=user_id)
                )
                user_quota = result.scalars().first()
                return (
                    UserQuotaModel.model_validate(user_quota) if user_quota else None
                )
        except Exception:
            return None

    async def increment(
        self, user_id: str, today: str, db: Optional = None
    ) -> Optional[UserQuotaModel]:
        try:
            async with get_async_db_context(db) as db:
                result = await db.execute(
                    select(UserQuota).filter_by(user_id=user_id)
                )
                user_quota = result.scalars().first()

                now_ts = int(time.time())

                if user_quota is None:
                    user_quota = UserQuota(
                        user_id=user_id,
                        request_count=1,
                        quota_date=today,
                        updated_at=now_ts,
                    )
                    db.add(user_quota)
                elif user_quota.quota_date != today:
                    user_quota.request_count = 1
                    user_quota.quota_date = today
                    user_quota.updated_at = now_ts
                else:
                    user_quota.request_count += 1
                    user_quota.updated_at = now_ts

                await db.commit()
                await db.refresh(user_quota)
                return UserQuotaModel.model_validate(user_quota)
        except Exception:
            return None


UserQuotas = UserQuotasTable()