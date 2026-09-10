from sqlalchemy import String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ClassificationResult(Base, TimestampMixin):
    __tablename__ = "classification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id"))
    segment_index: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[float] = mapped_column(Float, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_label: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    probabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    model_name: Mapped[str] = mapped_column(String(100))
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    job: Mapped["AnalysisJob"] = relationship(back_populates="results")

    def __repr__(self) -> str:
        return (
            f"<ClassificationResult id={self.id} segment={self.segment_index} "
            f"label={self.predicted_label!r} conf={self.confidence:.2f}>"
        )


from app.models.job import AnalysisJob  # noqa: E402


class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(50), default="comparative")
    n_models: Mapped[int] = mapped_column(Integer, default=0)
    n_samples: Mapped[int] = mapped_column(Integer, default=0)
    comparison_table: Mapped[dict] = mapped_column(JSON, default=dict)
    best_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    best_f1: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<EvaluationRun id={self.id} type={self.run_type!r} best={self.best_model!r}>"
