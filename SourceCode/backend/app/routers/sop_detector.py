"""/sop-detector/*: the SOP detector's API, answered by the detector process that runs
beside the backend in the same container (start.sh; SOP-detector/ at the repository root).

The paths and JSON are the detector's own (SOP-detector/README.md, "API"), so the frontend
calls them the same way here as it calls the stand-alone detector locally. While the
detector is starting, or when the image was built without it, the routes answer 503,
which the frontend treats as "not running".
"""
import re
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.config import settings
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/sop-detector", tags=["sop-detector"])

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB, the same limit as /api/v1/videos/upload
JOB_ID = re.compile(r"[0-9a-f]{12}")  # sop_detector_service.py: uuid4().hex[:12]


async def detector_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=settings.sop_detector_url, timeout=60) as client:
        yield client


async def forward(client: httpx.AsyncClient, method: str, path: str, **kwargs) -> Response:
    try:
        r = await client.request(method, path, **kwargs)
    except httpx.TransportError:
        raise HTTPException(status_code=503, detail="The SOP detector is not running")
    return Response(r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type"))


@router.get("/health")
async def health(client: httpx.AsyncClient = Depends(detector_client)) -> Response:
    return await forward(client, "GET", "/sop-detector/health")


@router.post("/jobs", dependencies=[Depends(verify_api_key)])
async def submit(request: Request,
                 client: httpx.AsyncClient = Depends(detector_client)) -> Response:
    too_large = HTTPException(
        status_code=413,
        detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)} MB")
    if int(request.headers.get("content-length") or 0) > MAX_FILE_SIZE:
        raise too_large
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > MAX_FILE_SIZE:
            raise too_large
    # The multipart body goes on as it came, boundary and all.
    return await forward(client, "POST", "/sop-detector/jobs", content=bytes(body),
                         headers={"content-type": request.headers.get("content-type", "")})


@router.get("/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
async def status(job_id: str, client: httpx.AsyncClient = Depends(detector_client)) -> Response:
    if not JOB_ID.fullmatch(job_id):
        raise HTTPException(status_code=404, detail="No such detection job")
    return await forward(client, "GET", f"/sop-detector/jobs/{job_id}")
