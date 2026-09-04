from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.search_service import search_service

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(payload: SearchRequest) -> SearchResponse:
    results = search_service.search(payload.query)
    return SearchResponse(
        results=[
            SearchResultItem(job_id=str(r.task_id), video_name=r.app, snippet=r.snippet, score=r.score)
            for r in results
        ]
    )
