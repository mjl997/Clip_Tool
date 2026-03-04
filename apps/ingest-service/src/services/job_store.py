import redis
import json
from ..config import settings
from typing import Dict, Any, Optional

class JobStore:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.expire_time = 86400  # 24 hours

    def create_job(self, job_id: str, metadata: Dict[str, Any]):
        self.redis.hset(f"job:{job_id}", mapping={
            "status": "pending",
            "metadata": json.dumps(metadata),
            "error": ""
        })
        self.redis.expire(f"job:{job_id}", self.expire_time)

    def update_status(self, job_id: str, status: str, error: Optional[str] = None):
        update_data = {"status": status}
        if error:
            update_data["error"] = error
        self.redis.hset(f"job:{job_id}", mapping=update_data)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.redis.hgetall(f"job:{job_id}")
        if not job:
            return None
        
        # Parse metadata json
        if "metadata" in job and isinstance(job["metadata"], str):
            try:
                job["metadata"] = json.loads(job["metadata"])
            except:
                pass
                
        return job

    def publish_event(self, channel: str, message: Dict[str, Any]):
        self.redis.publish(channel, json.dumps(message))

job_store = JobStore()
