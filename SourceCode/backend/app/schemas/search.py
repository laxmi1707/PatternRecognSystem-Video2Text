from pydantic import BaseModel

from app.schemas.analysis import CamelModel


class SearchRequest(BaseModel):
    query: str


class SearchResultItem(CamelModel):
    job_id: str
    video_name: str
    snippet: str
    score: float


class SearchResponse(CamelModel):
    results: list[SearchResultItem]
