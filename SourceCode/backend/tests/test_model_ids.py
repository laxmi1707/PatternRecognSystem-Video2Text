"""Primary keys must be 64-bit on Postgres and auto-generated on SQLite.

BIGINT keeps millisecond-timestamp-sized IDs from overflowing on Postgres, but
SQLite only auto-generates IDs for "INTEGER PRIMARY KEY", so a plain BigInteger
column made every insert on SQLite (the deployed database) fail with
"NOT NULL constraint failed: videos.id".
"""
from __future__ import annotations

import pytest
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateTable

from app.models import AnalysisJob, Base, Video


@pytest.mark.parametrize("model", [Video, AnalysisJob])
def test_id_column_type_per_dialect(model):
    sqlite_ddl = str(CreateTable(model.__table__).compile(dialect=sqlite.dialect()))
    pg_ddl = str(CreateTable(model.__table__).compile(dialect=postgresql.dialect()))
    assert "id INTEGER NOT NULL" in sqlite_ddl
    assert "id BIGSERIAL NOT NULL" in pg_ddl or "id BIGINT NOT NULL" in pg_ddl


@pytest.mark.asyncio
async def test_sqlite_generates_ids_and_stores_64_bit_values():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, expire_on_commit=False)

    async with session() as db:
        auto = Video(filename="a.mp4", original_filename="a.mp4", file_path="/tmp/a.mp4")
        big = Video(id=1792322733055, filename="b.mp4", original_filename="b.mp4", file_path="/tmp/b.mp4")
        db.add_all([auto, big])
        await db.commit()
        job = AnalysisJob(video_id=big.id)
        db.add(job)
        await db.commit()

    assert auto.id is not None
    assert big.id == 1792322733055
    assert job.id is not None and job.video_id == 1792322733055
    await engine.dispose()
