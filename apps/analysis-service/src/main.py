from fastapi import FastAPI, HTTPException
from .services.job_store import job_store
from .worker import worker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analysis Service")

@app.on_event("startup")
async def startup_event():
    worker.start()

@app.get("/api/v1/analysis/{job_id}")
async def get_analysis_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "status": job.get("status"),
        "error": job.get("error")
    }
    
    if response["status"] in ["analyzed", "completed"]:
        # We could fetch segments from MinIO if needed, but returning key is standard
        response["segments_key"] = f"jobs/{job_id}/segments.json"
        
    return response

@app.post("/api/v1/analysis/reanalyze")
async def reanalyze(job_id: str, provider: str = None):
    # Trigger re-analysis
    job = job_store.get_job(job_id)
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")
         
    # Publish event to self
    transcript_key = f"jobs/{job_id}/transcript.json"
    
    job_store.publish_event("transcript_ready", {
        "job_id": job_id,
        "transcript_key": transcript_key
        # Provider override could be handled if we passed it in event or stored in job settings
    })
    
    return {"status": "reanalysis_started"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
