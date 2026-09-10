from sqlalchemy import String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AnalysisJob(Base, TimestampMixin):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    status: Mapped[str] = mapped_column(String(50), default="queued")
    job_type: Mapped[str] = mapped_column(String(50), default="classification")
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    video: Mapped["Video"] = relationship(back_populates="jobs")
    results: Mapped[list["ClassificationResult"]] = relationship(
        back_populates="job", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AnalysisJob id={self.id} video_id={self.video_id} status={self.status!r}>"


from app.models.video import Video  # noqa: E402
from app.models.result import ClassificationResult  # noqa: E402
