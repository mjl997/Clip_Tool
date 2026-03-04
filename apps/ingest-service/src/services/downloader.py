import yt_dlp
import asyncio
import os
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(3)
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def get_metadata(self, url: str):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': 'in_playlist'
        }
        
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(self.executor, lambda: ydl.extract_info(url, download=False))
                
                if info.get('is_live'):
                    raise ValueError("Live streams are not supported")
                if info.get('availability') == 'private':
                    raise ValueError("Video is private")
                
                return {
                    "title": info.get("title"),
                    "thumbnail": info.get("thumbnail"),
                    "duration": info.get("duration"),
                    "channel": info.get("uploader"),
                    "id": info.get("id"),
                    "original_url": info.get("original_url") or url
                }
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error: {e}")
            raise ValueError(f"Video unavailable or invalid URL: {str(e)}")
        except Exception as e:
            logger.error(f"Metadata error: {e}")
            raise ValueError(f"Error fetching metadata: {str(e)}")

    async def process_video(self, url: str, job_id: str, output_dir: str):
        async with self.semaphore:
            job_dir = os.path.join(output_dir, job_id)
            os.makedirs(job_dir, exist_ok=True)
            
            # Use fixed filenames to avoid extension guessing issues
            video_path = os.path.join(job_dir, "video.mp4")
            audio_path = os.path.join(job_dir, "audio.wav")

            # Retry logic for downloads
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Downloading video {job_id}, attempt {attempt + 1}")
                    
                    # Video options: Force MP4 container, but allow fallback for direct URLs
                    video_opts = {
                        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best',
                        'outtmpl': video_path,
                        'quiet': True,
                        'no_warnings': True,
                        'overwrites': True,
                        'merge_output_format': 'mp4'
                    }

                    # Audio options: Extract WAV
                    audio_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(job_dir, 'audio_temp'), # Temp name before postprocessing
                        'quiet': True,
                        'no_warnings': True,
                        'overwrites': True,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'wav',
                            'preferredquality': '192',
                        }],
                        'postprocessor_args': [
                            '-ac', '1', 
                            '-ar', '16000'
                        ],
                        'keepvideo': False
                    }
                    
                    loop = asyncio.get_event_loop()
                    
                    # Download video
                    with yt_dlp.YoutubeDL(video_opts) as ydl:
                        await loop.run_in_executor(self.executor, lambda: ydl.download([url]))
                    
                    # Download audio
                    with yt_dlp.YoutubeDL(audio_opts) as ydl:
                        await loop.run_in_executor(self.executor, lambda: ydl.download([url]))
                    
                    # yt-dlp with postprocessor appends extension to outtmpl
                    # Check what file was created for audio
                    possible_audio = os.path.join(job_dir, 'audio_temp.wav')
                    if os.path.exists(possible_audio):
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                        os.rename(possible_audio, audio_path)
                    
                    if os.path.exists(video_path) and os.path.exists(audio_path):
                        return video_path, audio_path
                    else:
                        raise FileNotFoundError("Output files not found after download")

                except Exception as e:
                    logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"All download retries failed for job {job_id}")
                        raise e
                    time.sleep(2 ** attempt) # Exponential backoff

downloader = DownloadService()
