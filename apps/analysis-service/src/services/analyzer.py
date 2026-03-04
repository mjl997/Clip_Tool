from .llm import llm_service
from .audio import audio_service
import logging

logger = logging.getLogger(__name__)

class AnalyzerService:
    async def analyze(self, transcript_data: dict, audio_path: str, job_id: str):
        # 1. Audio Analysis
        audio_stats = audio_service.analyze_audio(audio_path)
        
        # 2. LLM Analysis
        # We pass the full text from transcript_data
        transcript_text = transcript_data.get("text", "")
        # Or reconstruct from words if needed
        
        llm_segments = await llm_service.analyze_transcript(transcript_text)
        
        # 3. Merge & Refine
        final_segments = []
        for seg in llm_segments:
            # Map LLM approximate timestamps to actual word timestamps
            # This logic needs to be robust. 
            # Ideally LLM returns text snippets, and we match them to 'words' in transcript_data
            
            # For this MVP, we assume LLM returns reasonable timestamps or we trust them.
            # But "Merge scores: LLM (70%) + Audio (30%)"
            
            llm_score = seg.get("score", 0)
            
            # Calculate audio score for this segment
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            
            # Check energy in this interval
            # audio_stats has 'rms_curve' (downsampled) or we can't easily map back without raw data
            # Let's use simple logic: if peak inside, boost score
            
            audio_boost = 0
            if "peaks" in audio_stats:
                peaks = [p for p in audio_stats["peaks"] if start <= p <= end]
                if peaks:
                    audio_boost = 20 # Arbitrary boost for high energy
            
            # Weighted merge
            # If LLM score is 0-100
            # Audio score could be normalized 0-100 based on energy relative to avg
            
            audio_score = min(100, (audio_stats.get("avg_energy", 0) * 1000)) # very rough
            if audio_boost:
                audio_score = 100
                
            final_score = (llm_score * 0.7) + (audio_score * 0.3)
            
            seg["score"] = round(final_score, 1)
            seg["audio_score"] = round(audio_score, 1)
            
            final_segments.append(seg)
            
        # Sort by score
        final_segments.sort(key=lambda x: x["score"], reverse=True)
        
        return final_segments[:10] # Top 10

analyzer = AnalyzerService()
