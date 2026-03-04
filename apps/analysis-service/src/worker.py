from .services.job_store import job_store
from .services.storage import storage
from .services.analyzer import analyzer
from .config import settings
import threading
import json
import logging
import os
import tempfile
import shutil
import asyncio

logger = logging.getLogger(__name__)

class EventWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.pubsub = job_store.subscribe("transcript_ready")
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        logger.info("Worker started, listening for transcript_ready events...")
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    logger.info(f"Received event: {data}")
                    self.loop.run_until_complete(self.process_job(data))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    async def process_job(self, data: dict):
        job_id = data.get("job_id")
        transcript_key = data.get("transcript_key")
        
        # We also need audio for analysis
        # In previous sprint, we didn't pass audio_key in transcript_ready, but it is predictable: jobs/{job_id}/audio.wav
        # Or we can look up the job metadata.
        audio_key = f"jobs/{job_id}/audio.wav"
        
        if not job_id or not transcript_key:
            logger.error("Invalid event data")
            return

        logger.info(f"Processing analysis for job {job_id}")
        job_store.update_status(job_id, "analyzing")

        temp_dir = tempfile.mkdtemp()
        try:
            transcript_path = os.path.join(temp_dir, "transcript.json")
            audio_path = os.path.join(temp_dir, "audio.wav")
            segments_path = os.path.join(temp_dir, "segments.json")
            
            # Download files
            storage.download_file(transcript_key, transcript_path)
            storage.download_file(audio_key, audio_path)
            
            # Load transcript
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_data = json.load(f)
            
            # Analyze
            segments = await analyzer.analyze(transcript_data, audio_path, job_id)
            
            # Save result
            with open(segments_path, "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False)
            
            # Upload segments
            segments_key = f"jobs/{job_id}/segments.json"
            storage.upload_file(segments_key, segments_path, "application/json")
            
            # Update status
            job_store.update_status(job_id, "analyzed")
            
            # Publish event
            job_store.publish_event("segments_ready", {
                "job_id": job_id,
                "status": "completed",
                "segments_key": segments_key,
                "count": len(segments)
            })
            
            logger.info(f"Analysis completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {e}")
            job_store.update_status(job_id, "failed", error=str(e))
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

worker = EventWorker()
