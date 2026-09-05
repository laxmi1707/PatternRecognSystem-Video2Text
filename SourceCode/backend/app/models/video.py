from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")

    jobs: Mapped[list["AnalysisJob"]] = relationship(back_populates="video", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Video id={self.id} filename={self.filename!r} status={self.status!r}>"


from app.models.job import AnalysisJob  # noqa: E402
