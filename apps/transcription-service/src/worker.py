import threading
import json
import logging
import time
import os
import tempfile
import shutil
from .services.job_store import job_store
from .services.storage import storage
from .services.transcriber import transcriber
from .config import settings

logger = logging.getLogger(__name__)

class EventWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.pubsub = job_store.subscribe("video_ready")

    def run(self):
        logger.info("Worker started, listening for video_ready events...")
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    logger.info(f"Received event: {data}")
                    self.process_job_with_retry(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    def process_job_with_retry(self, data: dict, max_retries: int = 3):
        job_id = data.get("job_id")
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.process_job(data)
                return
            except Exception as e:
                retry_count += 1
                logger.error(f"Transcription failed for job {job_id} (Attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    backoff = 2 ** retry_count
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"Job {job_id} failed after {max_retries} attempts.")
                    job_store.update_status(job_id, "failed", error=str(e))
                    # Publish to DLQ or similar mechanism if implemented
                    # job_store.publish_to_dlq(...)

    def process_job(self, data: dict):
        job_id = data.get("job_id")
        audio_key = data.get("audio_key")
        
        if not job_id or not audio_key:
            logger.error("Invalid event data")
            return

        logger.info(f"Processing transcription for job {job_id}")
        job_store.update_status(job_id, "transcribing", progress=0.1)

        temp_dir = tempfile.mkdtemp()
        try:
            audio_path = os.path.join(temp_dir, "audio.wav")
            transcript_path = os.path.join(temp_dir, "transcript.json")
            
            storage.download_file(audio_key, audio_path)
            
            result = transcriber.transcribe(audio_path, job_id)
            
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False)
            
            transcript_key = f"jobs/{job_id}/transcript.json"
            storage.upload_file(transcript_key, transcript_path, "application/json")
            
            job_store.update_status(job_id, "transcribed", progress=1.0)
            
            job_store.publish_event("transcript_ready", {
                "job_id": job_id,
                "status": "completed",
                "transcript_key": transcript_key,
                "language": result["language"]
            })
            
            logger.info(f"Transcription completed for job {job_id}")
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

worker = EventWorker()
