from pydantic import BaseModel


class VideoUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    status: str
    job_id: int


class VideoResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    duration_seconds: float | None
    status: str
