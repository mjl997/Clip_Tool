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
        # Construct transcript with timestamps for better LLM context
        # Format: [00:00.000 -> 00:05.000] Text segment
        formatted_transcript = ""
        if "segments" in transcript_data:
            for s in transcript_data["segments"]:
                start = s.get("start", 0)
                end = s.get("end", 0)
                text = s.get("text", "").strip()
                formatted_transcript += f"[{self._format_time(start)} -> {self._format_time(end)}] {text}\n"
        else:
            formatted_transcript = transcript_text

        # Pass audio context if available
        audio_context = ""
        if "high_energy_events" in audio_stats:
            audio_context = "SEÑALES DE AUDIO DETECTADAS:\n"
            for event in audio_stats["high_energy_events"]:
                audio_context += f"- [{self._format_time(event['start'])} -> {self._format_time(event['end'])}] Pico de energía alta\n"

        llm_segments = await llm_service.analyze_transcript(formatted_transcript, audio_context=audio_context)
        
        # 3. Merge & Refine
        final_segments = []
        for seg in llm_segments:
            # Validation logic
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            
            # Validate duration (15s - 60s)
            duration = end - start
            if duration < 15 or duration > 60:
                logger.warning(f"Discarding segment {start}-{end}: Invalid duration {duration}s")
                continue
                
            # Validate boundaries against video duration
            if end > audio_stats.get("duration", end + 1):
                 logger.warning(f"Discarding segment {start}-{end}: Ends after video duration")
                 continue

            llm_score = seg.get("score", 0)
            
            # Calculate audio score for this segment
            audio_score = 0
            if "high_energy_events" in audio_stats:
                # Check overlap with energy events
                for event in audio_stats["high_energy_events"]:
                    # Simple overlap check
                    if max(start, event["start"]) < min(end, event["end"]):
                        audio_score = 20 # Boost for energy overlap
                        break
            
            # Weighted merge (LLM dominates, Audio boosts)
            # LLM score is already 0-100 based on virality criteria
            # We add a small boost for audio energy confirmation, capped at 100
            final_score = min(100, llm_score + audio_score)
            
            seg["score"] = round(final_score, 1)
            seg["audio_boost"] = audio_score
            
            final_segments.append(seg)
            
        # Check overlaps and keep highest score
        # Sort by score descending
        final_segments.sort(key=lambda x: x["score"], reverse=True)
        
        non_overlapping = []
        for seg in final_segments:
            overlap = False
            for kept in non_overlapping:
                # Check overlap
                if max(seg["start"], kept["start"]) < min(seg["end"], kept["end"]):
                    overlap = True
                    break
            if not overlap:
                non_overlapping.append(seg)
        
        return non_overlapping[:8] # Top 8 as requested

    def _format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{mins:02d}:{secs:02d}.{ms:03d}"

analyzer = AnalyzerService()
