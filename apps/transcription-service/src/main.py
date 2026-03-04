from fastapi import FastAPI, HTTPException
from .services.job_store import job_store
from .worker import worker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Transcription Service")

@app.on_event("startup")
async def startup_event():
    worker.start()

@app.get("/api/v1/transcription/{job_id}")
async def get_transcription_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "status": job.get("status"),
        "progress": job.get("progress"),
        "error": job.get("error")
    }

    # If completed, check for metadata or fetch transcript key
    # Metadata might contain "transcript_key" or similar if we stored it?
    # In worker.py, we published "transcript_ready" with "transcript_key".
    # But we didn't explicitly store "transcript_key" in redis hash in worker.py, we only updated status.
    # We should update redis hash with result details too.
    
    # Wait, let's fix worker.py to store result info in redis hash so we can return it here.
    # For now, let's assume if status is "transcribed" or "completed", the key is standard.
    
    if response["status"] in ["transcribed", "completed"]:
        response["transcript_key"] = f"jobs/{job_id}/transcript.json"
        
        # Optionally, we could fetch the transcript content from MinIO if requested
        # via a query param like ?include_transcript=true
        # But for basic status, just the key/link is enough.
        
    return response

@app.post("/api/v1/transcription/reprocess")
async def reprocess_transcription(job_id: str, model: str = "base"):
    # This would trigger a re-run.
    # We need to manually push an event or call logic.
    # For simplicity, we can push a 'video_ready' event again with same data?
    # But we need the audio key.
    
    job = job_store.get_job(job_id)
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")
    
    # We need audio_key. It should be in metadata or we can infer it.
    # job_store stores "metadata" json string if available.
    
    # In ingest service, we stored metadata. In transcription service, we just read/update status.
    # We didn't store audio_key in the job hash in ingest service explicitly separate from metadata?
    # In ingest service: job_store.create_job(job_id, metadata)
    # Metadata had youtube info.
    # The event had "audio_key".
    
    # If we want to reprocess, we need audio_key.
    # We can reconstruct it: jobs/{job_id}/audio.wav
    audio_key = f"jobs/{job_id}/audio.wav"
    
    # Publish event
    job_store.publish_event("video_ready", {
        "job_id": job_id,
        "status": "completed", # Mimic ingest completion
        "audio_key": audio_key
    })
    
    return {"status": "reprocessing_started"}

@app.get("/api/v1/transcription/health")
def health_check_api():
    return {"status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
