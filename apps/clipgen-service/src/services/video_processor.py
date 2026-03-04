import subprocess
import os
import logging
from .face_detection import face_service
from .subtitles import subtitle_service

logger = logging.getLogger(__name__)

class VideoProcessor:
    def process_clip(self, video_path: str, start: float, end: float, transcript_words: list, output_dir: str, clip_id: str):
        """
        1. Cut video
        2. Analyze for cropping (9:16)
        3. Generate Subtitles
        4. Burn Subtitles (Ass)
        5. Export clean and subbed versions
        6. Generate Thumbnail
        """
        
        # Paths
        cut_path = os.path.join(output_dir, "cut.mp4")
        cropped_path = os.path.join(output_dir, "cropped.mp4")
        clean_path = os.path.join(output_dir, "clean.mp4")
        subbed_path = os.path.join(output_dir, "sub.mp4")
        ass_path = os.path.join(output_dir, "subs.ass")
        srt_path = os.path.join(output_dir, "subs.srt")
        thumb_path = os.path.join(output_dir, "thumb.jpg")
        
        # 1. Cut Video (Exact)
        # Use re-encoding to ensure precision and keyframes
        cmd_cut = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(end - start),
            "-c:v", "libx264", "-c:a", "aac",
            cut_path
        ]
        subprocess.run(cmd_cut, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. Smart Crop (9:16)
        # Analyze cut video to find face center
        # For simplicity, we take the average face center of the clip or keyframes
        centers = face_service.analyze_video_for_cropping(cut_path)
        if centers:
            avg_center_x = sum([c[1] for c in centers]) / len(centers)
        else:
            avg_center_x = 0.5
            
        # Calculate crop window
        # Input: 1280x720 (16:9) -> Output: 405x720 (9:16)
        # But usually we want 720x1280, which means we need to upscale or just crop to vertical slice?
        # If original is landscape 16:9 (e.g. 1920x1080).
        # Target 9:16 vertical means crop 607x1080 from center.
        
        # Let's assume input is 1280x720. Height is 720. Target width for 9:16 is 720 * 9/16 = 405.
        # We crop a 405x720 window centered at avg_center_x.
        
        # We need video dimensions
        # probe = ffmpeg.probe(cut_path) ... using subprocess
        # Assuming 1280x720 for calculation sake, but we should detect.
        # For now, let's use a filter that calculates crop.
        
        # Using crop filter: crop=h*(9/16):h:x:0
        # x = (in_w - out_w) * center_x
        
        crop_filter = f"crop=ih*(9/16):ih:(iw-ow)*{avg_center_x}:0"
        
        # Apply crop and fade in/out
        # Add fade in (0.3s) and fade out (0.3s)
        duration = end - start
        fade_filter = f"fade=t=in:st=0:d=0.3,fade=t=out:st={duration-0.3}:d=0.3"
        
        # Combine filters
        # Note: crop filter uses iw/ih/ow/oh, so it must be applied first or chained correctly
        # Also need to re-encode audio for aac if copy doesn't work with filters? 
        # Actually -c:a copy is fine if we don't touch audio, but we might want audio fade?
        # Let's skip audio fade for now or add afade.
        
        full_vf = f"{crop_filter},{fade_filter}"
        
        cmd_crop = [
            "ffmpeg", "-y",
            "-i", cut_path,
            "-vf", full_vf,
            "-c:a", "aac", # Re-encode audio to be safe with container
            clean_path
        ]
        subprocess.run(cmd_crop, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 3. Generate Subtitles
        # We need to offset timestamps relative to start time
        relative_words = []
        for w in transcript_words:
            if w['start'] >= start and w['end'] <= end:
                relative_words.append({
                    'word': w['word'],
                    'start': w['start'] - start,
                    'end': w['end'] - start
                })
                
        subtitle_service.generate_ass(relative_words, ass_path, style="hormozi")
        subtitle_service.generate_srt(relative_words, srt_path)
        
        # 4. Burn Subtitles
        # Using libass
        # Note: path to ass file in filter must be absolute or escaped correctly
        ass_path_abs = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
        
        cmd_burn = [
            "ffmpeg", "-y",
            "-i", clean_path,
            "-vf", f"ass='{ass_path_abs}'",
            "-c:a", "copy",
            subbed_path
        ]
        subprocess.run(cmd_burn, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 5. Thumbnail
        # Extract at 50% duration
        duration = end - start
        cmd_thumb = [
            "ffmpeg", "-y",
            "-ss", str(duration / 2),
            "-i", clean_path,
            "-vframes", "1",
            "-q:v", "2",
            thumb_path
        ]
        subprocess.run(cmd_thumb, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return {
            "clean_video": clean_path,
            "subbed_video": subbed_path,
            "srt": srt_path,
            "thumbnail": thumb_path
        }

video_processor = VideoProcessor()
