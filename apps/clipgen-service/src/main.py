from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from .services.job_store import job_store
from .worker import worker
from .services.storage import storage
import logging
import os
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Clip Generation Service")

@app.on_event("startup")
async def startup_event():
    worker.start()

@app.get("/api/v1/clips/{job_id}")
async def get_clips(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    clips = job_store.get_clips(job_id)
    
    return {
        "status": job.get("status"),
        "error": job.get("error"),
        "clips": clips
    }

@app.get("/api/v1/clips/{job_id}/{clip_id}/download")
async def download_clip(job_id: str, clip_id: str, format: str = "mp4_subs"):
    # Stream file from MinIO
    # For simplicity, download to temp and serve
    # In prod, generate presigned URL or stream directly
    
    key = ""
    if format == "mp4_subs":
        key = f"jobs/{job_id}/clips/{clip_id}/sub.mp4"
    elif format == "mp4_clean":
        key = f"jobs/{job_id}/clips/{clip_id}/clean.mp4"
    elif format == "srt":
        key = f"jobs/{job_id}/clips/{clip_id}/subs.srt"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
        
    temp_file = tempfile.mktemp()
    try:
        storage.download_file(key, temp_file)
        return FileResponse(temp_file, filename=os.path.basename(key))
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/v1/clips/regenerate")
async def regenerate_clip(job_id: str, clip_id: str, ratio: str = "9:16", sub_style: str = "hormozi"):
    # This would require re-processing a single clip
    # Not fully implemented in worker yet, need to extract logic
    return {"status": "not_implemented_yet"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
