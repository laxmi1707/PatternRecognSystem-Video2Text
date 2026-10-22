from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# 64-bit IDs (millisecond-timestamp-sized values overflow a 32-bit INTEGER on
# Postgres). SQLite only auto-generates IDs for "INTEGER PRIMARY KEY", not BIGINT,
# and its INTEGER is already 64-bit, so use INTEGER there.
BigIntId = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )
