from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any

class IngestRequest(BaseModel):
    url: HttpUrl
    max_duration: Optional[int] = None

class IngestResponse(BaseModel):
    job_id: str
    status: str
    metadata: Dict[str, Any]

class JobStatus(BaseModel):
    job_id: str
    status: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
