from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from .services.storage import storage
from .services.job_store import job_store
from .services.db import db_service
from .scheduler import scheduler
import logging
import zipfile
import io
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Export Service")

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    db_service.create_tables()

@app.get("/api/v1/export/{job_id}/all")
async def export_all_zip(job_id: str):
    # Streaming ZIP generation is complex because zipfile requires random access for writing usually?
    # Actually python's zipfile can write to a stream.
    # But for HTTP streaming, we need a generator that yields bytes.
    # A common approach is using a custom generator that zips on the fly.
    # Or simpler: use a library like `stream-zip` or buffer small files.
    # Given video clips can be large, we should probably not buffer everything in memory.
    
    # Simpler implementation: Download files to temp, zip, then stream zip? 
    # Or just stream the zip structure.
    
    # Let's try to list files first.
    clips = job_store.get_clips(job_id)
    if not clips:
        raise HTTPException(status_code=404, detail="No clips found for this job")
        
    # We will include subbed videos for now in the ZIP
    files_to_zip = []
    for clip in clips:
        clip_id = clip["clip_id"]
        key = f"jobs/{job_id}/clips/{clip_id}/sub.mp4"
        filename = f"clip_{clip_id}_sub.mp4"
        files_to_zip.append((key, filename))
        
    # Using a generator to stream the zip content
    # We need a way to construct zip file chunks.
    # Since writing a zip streaming is tricky with standard lib without seekable stream,
    # we can use a helper or just zip in memory if files are small? No, video files are big.
    
    # Alternative: Use `zip` command line if installed? (we installed zip in Dockerfile)
    # But we need to download files first.
    
    # Let's use a simpler approach: Just stream one large file? No, requirement is ZIP.
    # We will use `zipfile` with a BytesIO buffer that we yield from, but that requires careful management.
    
    # Let's use a generator that:
    # 1. Creates a ZipFile object wrapping a custom file-like object that yields data?
    # This is complicated.
    
    # Let's fallback to "Download to temp, Zip, Stream, Delete" for MVP safety, 
    # unless files are huge (e.g. > 1GB total).
    # If clips are short (1min), total size might be 100-200MB. Manageable in temp.
    
    import tempfile
    import shutil
    import os
    from fastapi.concurrency import run_in_threadpool
    
    async def generate_zip():
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"job_{job_id}.zip")
        
        try:
            # Run blocking I/O in threadpool
            def create_zip_file():
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for key, filename in files_to_zip:
                        temp_file = os.path.join(temp_dir, filename)
                        try:
                            storage.client.fget_object(storage.bucket_name, key, temp_file)
                            zf.write(temp_file, filename)
                            os.remove(temp_file)
                        except Exception as e:
                            logger.error(f"Failed to zip {key}: {e}")
            
            await run_in_threadpool(create_zip_file)
            
            # Now stream the zip file
            with open(zip_path, "rb") as f:
                while True:
                    chunk = await run_in_threadpool(f.read, 64*1024)
                    if not chunk:
                        break
                    yield chunk
                    
        finally:
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except: pass
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except: pass

    return StreamingResponse(
        generate_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_clips.zip"}
    )

@app.get("/api/v1/export/{job_id}/{clip_id}")
async def export_clip(job_id: str, clip_id: str, format: str = "mp4_subs"):
    # Map format to file key suffix
    key = ""
    filename = ""
    
    if format == "mp4_subs":
        key = f"jobs/{job_id}/clips/{clip_id}/sub.mp4"
        filename = f"job_{job_id}_clip_{clip_id}_sub.mp4"
    elif format == "mp4_clean":
        key = f"jobs/{job_id}/clips/{clip_id}/clean.mp4"
        filename = f"job_{job_id}_clip_{clip_id}_clean.mp4"
    elif format == "srt":
        key = f"jobs/{job_id}/clips/{clip_id}/subs.srt"
        filename = f"job_{job_id}_clip_{clip_id}.srt"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
        
    try:
        # Get stream from MinIO
        response = storage.get_object_stream(key)
        
        # Generator for streaming
        def iterfile():
            try:
                while True:
                    data = response.read(64*1024) # 64k chunks
                    if not data:
                        break
                    yield data
            finally:
                response.close()
                response.release_conn()

        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error streaming file: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/v1/jobs")
async def list_jobs(limit: int = 50):
    return db_service.get_recent_jobs(limit)

@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    # Delete from MinIO
    # Recursive delete under jobs/{job_id}
    objects = storage.list_objects(f"jobs/{job_id}/", recursive=True)
    for obj in objects:
        storage.remove_object(obj.object_name)
        
    # Mark as deleted in DB or remove
    db_service.delete_job(job_id)
    
    return {"deleted": True}

@app.get("/health")
def health_check():
    return {"status": "ok"}
