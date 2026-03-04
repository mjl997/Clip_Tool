import redis
import json
import logging
from typing import Dict, Any, Callable
import time

logger = logging.getLogger(__name__)

class RedisQueue:
    def __init__(self, redis_url: str, queue_name: str, dlq_name: str = None):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.queue_name = queue_name
        self.dlq_name = dlq_name or f"{queue_name}:dlq"

    def push(self, data: Dict[str, Any]):
        self.redis.rpush(self.queue_name, json.dumps(data))

    def consume(self, callback: Callable[[Dict[str, Any]], None], max_retries: int = 3):
        while True:
            # Blocking pop
            _, message = self.redis.blpop(self.queue_name)
            if not message:
                continue
                
            data = json.loads(message)
            retry_count = data.get("retry_count", 0)
            job_id = data.get("job_id", "unknown")
            
            try:
                # Add job_id to logger context if possible
                # logger = logging.LoggerAdapter(logger, {"job_id": job_id})
                logger.info(f"Processing job {job_id}, attempt {retry_count + 1}")
                
                callback(data)
                
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                
                if retry_count < max_retries:
                    data["retry_count"] = retry_count + 1
                    # Exponential backoff (simple sleep for now, better to use delayed queue)
                    backoff = 2 ** retry_count
                    logger.info(f"Retrying job {job_id} in {backoff}s...")
                    time.sleep(backoff) 
                    self.push(data) # Push back to queue (end)
                else:
                    logger.error(f"Job {job_id} failed after {max_retries} retries. Moving to DLQ.")
                    data["error"] = str(e)
                    self.redis.rpush(self.dlq_name, json.dumps(data))
