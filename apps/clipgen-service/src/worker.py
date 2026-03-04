from .services.job_store import job_store
from .services.storage import storage
from .services.video_processor import video_processor
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
        self.pubsub = job_store.subscribe("segments_ready")
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        logger.info("Worker started, listening for segments_ready events...")
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    logger.info(f"Received event: {data}")
                    self.process_job(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    def process_job(self, data: dict):
        job_id = data.get("job_id")
        segments_key = data.get("segments_key")
        
        # We also need video and transcript
        # Transcript is needed for word-level subtitles
        # Video is needed for cutting
        
        # We can infer keys
        video_key = f"jobs/{job_id}/video.mp4"
        transcript_key = f"jobs/{job_id}/transcript.json"
        
        if not job_id or not segments_key:
            logger.error("Invalid event data")
            return

        logger.info(f"Processing clips for job {job_id}")
        job_store.update_status(job_id, "clipping")

        temp_dir = tempfile.mkdtemp()
        try:
            segments_path = os.path.join(temp_dir, "segments.json")
            video_path = os.path.join(temp_dir, "video.mp4")
            transcript_path = os.path.join(temp_dir, "transcript.json")
            
            # Download files
            storage.download_file(segments_key, segments_path)
            storage.download_file(video_key, video_path)
            storage.download_file(transcript_key, transcript_path)
            
            with open(segments_path, "r", encoding="utf-8") as f:
                segments = json.load(f)
                
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript = json.load(f)
                # Handle whisper result format (sometimes 'words' is inside 'chunks' or top level)
                if "words" in transcript:
                    words = transcript["words"]
                elif "segments" in transcript:
                    # Flatten segments if words are inside segments
                    words = []
                    for s in transcript["segments"]:
                        if "words" in s:
                            words.extend(s["words"])
                else:
                    words = []
            
            generated_clips = []
            
            for i, seg in enumerate(segments):
                clip_id = str(i + 1) # simple ID 1, 2, 3
                logger.info(f"Processing clip {clip_id} for job {job_id}")
                
                start = seg.get("start")
                end = seg.get("end")
                
                # Clip directory
                clip_dir = os.path.join(temp_dir, f"clip_{clip_id}")
                os.makedirs(clip_dir, exist_ok=True)
                
                # Process
                result = video_processor.process_clip(
                    video_path, start, end, words, clip_dir, clip_id
                )
                
                # Upload artifacts
                # /jobs/{job_id}/clips/{clip_id}/[sub.mp4, clean.mp4, subs.srt, thumb.jpg]
                base_key = f"jobs/{job_id}/clips/{clip_id}"
                
                storage.upload_file(f"{base_key}/clean.mp4", result["clean_video"], "video/mp4")
                storage.upload_file(f"{base_key}/sub.mp4", result["subbed_video"], "video/mp4")
                storage.upload_file(f"{base_key}/subs.srt", result["srt"], "text/plain")
                storage.upload_file(f"{base_key}/thumb.jpg", result["thumbnail"], "image/jpeg")
                
                clip_data = {
                    "clip_id": clip_id,
                    "start": start,
                    "end": end,
                    "clean_video": f"{base_key}/clean.mp4",
                    "subbed_video": f"{base_key}/sub.mp4",
                    "thumbnail": f"{base_key}/thumb.jpg",
                    "score": seg.get("score"),
                    "category": seg.get("category"),
                    "hook": seg.get("hook_phrase")
                }
                
                job_store.add_clip(job_id, clip_data)
                generated_clips.append(clip_data)
            
            # Update status
            job_store.update_status(job_id, "clips_ready")
            
            # Publish event
            job_store.publish_event("clips_ready", {
                "job_id": job_id,
                "status": "completed",
                "clips_count": len(generated_clips)
            })
            
            logger.info(f"Clip generation completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Clip generation failed for job {job_id}: {e}")
            job_store.update_status(job_id, "failed", error=str(e))
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

worker = EventWorker()
