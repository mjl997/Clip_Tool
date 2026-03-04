from pydantic import BaseModel
from typing import List, Optional

class Segment(BaseModel):
    start: float
    end: float
    score: float
    hook_phrase: str
    category: str
    reasoning: str
    caption: str
    hook_score: Optional[float] = 0
    emotion_score: Optional[float] = 0
    shareability_score: Optional[float] = 0
    standalone_score: Optional[float] = 0
    audio_score: Optional[float] = 0

class AnalysisResult(BaseModel):
    job_id: str
    segments: List[Segment]
    provider: str

class ReanalyzeRequest(BaseModel):
    job_id: str
    provider: Optional[str] = None
    min_score: Optional[float] = None
