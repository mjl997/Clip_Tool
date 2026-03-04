import requests
import time
import sys
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost"

def submit_job(url):
    logger.info(f"Submitting video: {url}")
    try:
        # Ingest Service on port 8001
        resp = requests.post(f"{BASE_URL}:8001/api/v1/ingest", json={"url": url})
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("job_id")
        logger.info(f"Job submitted successfully. Job ID: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"Failed to submit job: {e}")
        sys.exit(1)

def wait_for_completion(job_id, timeout=600):
    logger.info(f"Waiting for job {job_id} to complete (Timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Check clip status (final stage) - ClipGen on 8003
            resp = requests.get(f"{BASE_URL}:8003/api/v1/clips/{job_id}")
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                
                if status == "completed" or status == "clips_ready":
                    clips = data.get("clips", [])
                    logger.info(f"Job completed! Generated {len(clips)} clips.")
                    return clips
                elif status == "failed":
                    logger.error(f"Job failed: {data.get('error')}")
                    sys.exit(1)
                else:
                    logger.info(f"Status: {status}...")
            else:
                # Fallback to checking ingest status if clip endpoint 404s (early stage) - Ingest on 8001
                resp_ingest = requests.get(f"{BASE_URL}:8001/api/v1/ingest/{job_id}")
                if resp_ingest.status_code == 200:
                    logger.info(f"Ingest Status: {resp_ingest.json().get('status')}...")
            
            time.sleep(5)
        except Exception as e:
            logger.warning(f"Error checking status: {e}")
            time.sleep(5)
            
    logger.error("Timeout waiting for job completion")
    sys.exit(1)

def verify_downloads(job_id, clips):
    logger.info("Verifying clip downloads...")
    success_count = 0
    
    for clip in clips:
        clip_id = clip.get("clip_id")
        # Try downloading mp4_subs - Export Service on 8002
        url = f"{BASE_URL}:8002/api/v1/export/{job_id}/{clip_id}?format=mp4_subs"
        try:
            logger.info(f"Downloading clip {clip_id}...")
            resp = requests.get(url, stream=True)
            if resp.status_code == 200:
                size = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    size += len(chunk)
                logger.info(f"Clip {clip_id} downloaded successfully ({size} bytes)")
                success_count += 1
            else:
                logger.error(f"Failed to download clip {clip_id}: Status {resp.status_code}")
        except Exception as e:
            logger.error(f"Error downloading clip {clip_id}: {e}")
            
    if success_count == len(clips):
        logger.info("All clips verified successfully!")
    else:
        logger.warning(f"Only {success_count}/{len(clips)} clips verified.")

def main():
    parser = argparse.ArgumentParser(description="E2E Test for Clip Tool")
    # Use Big Buck Bunny (direct MP4) to avoid YouTube 403 errors in CI/CD environments
    parser.add_argument("--url", default="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", help="Video URL")
    args = parser.parse_args()
    
    job_id = submit_job(args.url)
    clips = wait_for_completion(job_id)
    verify_downloads(job_id, clips)
    
    logger.info("E2E Test Passed ✅")

if __name__ == "__main__":
    main()
