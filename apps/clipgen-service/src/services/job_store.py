import redis
import json
from ..config import settings
from typing import Dict, Any, Optional

class JobStore:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.expire_time = 86400  # 24 hours

    def update_status(self, job_id: str, status: str, error: Optional[str] = None):
        update_data = {"status": status}
        if error:
            update_data["error"] = error
        self.redis.hset(f"job:{job_id}", mapping=update_data)
        
    def add_clip(self, job_id: str, clip_data: Dict[str, Any]):
        # Store clip metadata in a list or hash
        # Ideally we append to a list of clips for this job
        self.redis.rpush(f"job:{job_id}:clips", json.dumps(clip_data))

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.redis.hgetall(f"job:{job_id}")
        if not job:
            return None
        return job
        
    def get_clips(self, job_id: str):
        clips_raw = self.redis.lrange(f"job:{job_id}:clips", 0, -1)
        return [json.loads(c) for c in clips_raw]

    def publish_event(self, channel: str, message: Dict[str, Any]):
        self.redis.publish(channel, json.dumps(message))

    def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

job_store = JobStore()
