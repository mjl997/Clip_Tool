import redis
import json
from ..config import settings
from typing import Dict, Any, Optional

class JobStore:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.redis.hgetall(f"job:{job_id}")
        if not job:
            return None
        return job
        
    def get_clips(self, job_id: str):
        clips_raw = self.redis.lrange(f"job:{job_id}:clips", 0, -1)
        return [json.loads(c) for c in clips_raw]

job_store = JobStore()
