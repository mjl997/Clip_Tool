from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from .schemas import IngestRequest, IngestResponse, JobStatus
from .services.job_store import job_store
from .services.downloader import downloader  # Use the instance created in downloader.py
from .services.storage import storage
import uuid
import logging
import os
import shutil
import tempfile
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ingest Service")

async def run_background_job(job_id: str, url: str):
    temp_dir = tempfile.mkdtemp()
    try:
        # Update status
        job_store.update_status(job_id, "downloading")
        
        # Download
        # process_video returns (video_path, audio_path)
        video_path, audio_path = await downloader.process_video(url, job_id, temp_dir)
        
        # Verify paths
        if not os.path.exists(video_path):
            # Fallback check
            job_files_dir = os.path.join(temp_dir, job_id)
            if os.path.exists(job_files_dir):
                files = os.listdir(job_files_dir)
                for f in files:
                    if f.endswith('.mp4'):
                        video_path = os.path.join(job_files_dir, f)
                        break
        
        if not os.path.exists(audio_path):
             # Fallback check
            job_files_dir = os.path.join(temp_dir, job_id)
            if os.path.exists(job_files_dir):
                files = os.listdir(job_files_dir)
                for f in files:
                    if f.endswith('.wav'):
                        audio_path = os.path.join(job_files_dir, f)
                        break

        if not os.path.exists(video_path) or not os.path.exists(audio_path):
            raise FileNotFoundError(f"Downloaded files missing. Found: {os.listdir(os.path.join(temp_dir, job_id)) if os.path.exists(os.path.join(temp_dir, job_id)) else 'No dir'}")

        # Update status
        job_store.update_status(job_id, "uploading")
        
        # Upload
        storage.upload_file(f"jobs/{job_id}/video.mp4", video_path, "video/mp4")
        storage.upload_file(f"jobs/{job_id}/audio.wav", audio_path, "audio/wav")
        
        # Publish completion
        job_store.update_status(job_id, "completed")
        job_store.publish_event("video_ready", {
            "job_id": job_id, 
            "status": "completed",
            "video_key": f"jobs/{job_id}/video.mp4",
            "audio_key": f"jobs/{job_id}/audio.wav"
        })
        
    except Exception as e:
        logger.error(f"Background job {job_id} failed: {e}")
        job_store.update_status(job_id, "failed", str(e))
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.post("/api/v1/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_video(request: IngestRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Validate & Metadata
        metadata = await downloader.get_metadata(str(request.url))
        
        # 2. Create Job
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id, metadata)
        
        # 3. Start Background Task
        background_tasks.add_task(run_background_job, job_id, str(request.url))
        
        return IngestResponse(
            job_id=job_id,
            status="pending",
            metadata=metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/ingest/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(
        job_id=job_id,
        status=job.get("status"),
        metadata=job.get("metadata"),
        error=job.get("error")
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}
