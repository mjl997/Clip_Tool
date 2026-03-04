import subprocess
import os
import logging
import math

logger = logging.getLogger(__name__)

class SubtitleService:
    def generate_ass(self, transcript_segments: list, output_path: str, style: str = "hormozi"):
        """
        Generates .ass subtitle file from transcript segments (word-level).
        segments: list of {word, start, end, confidence} (or similar structure)
        """
        
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 384
PlayResY: 192

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
        # Define styles
        if style == "hormozi":
            # Yellow/Green/White large bold text with black outline
            styles = """Style: Default,Arial,16,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1.5,0,2,10,10,20,1
Style: Highlight,Arial,18,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1.5,0,2,10,10,20,1
"""
        elif style == "minimal":
             styles = """Style: Default,Roboto,12,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,2,10,10,30,1
Style: Highlight,Roboto,12,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,2,10,10,30,1
"""
        else: # Default
            styles = """Style: Default,Arial,16,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
Style: Highlight,Arial,16,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
"""

        events_header = """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        events = []
        
        # Group words into chunks of max 3 words
        # transcript_segments usually comes from 'words' key in whisper result
        
        words = transcript_segments
        chunk_size = 3
        
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i+chunk_size]
            if not chunk: continue
            
            start_time = chunk[0]['start']
            end_time = chunk[-1]['end']
            
            # Convert to ASS time format: H:MM:SS.cc
            def format_time(s):
                h = int(s // 3600)
                m = int((s % 3600) // 60)
                sec = s % 60
                return f"{h}:{m:02d}:{sec:05.2f}"
            
            # For each word in chunk, create an event where that word is highlighted?
            # Or just display the chunk.
            # Hormozi style: often one word at a time or small chunks with active word highlighted.
            # Let's do: display chunk, highlight active word if possible using karaoke tags or multiple events.
            # Simpler approach: Display chunk. If style is hormozi, maybe colorize specific words?
            # Let's just output the text for now.
            
            text_str = " ".join([w['word'] for w in chunk])
            
            # Basic event
            start_fmt = format_time(start_time)
            end_fmt = format_time(end_time)
            
            # Simple Highlight: Just one style for the whole chunk for now
            # To do word-level highlight, we need overlapping events or {\k} tags.
            # Let's keep it simple: Show chunk.
            
            event_line = f"Dialogue: 0,{start_fmt},{end_fmt},Default,,0,0,0,,{text_str}"
            events.append(event_line)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + styles + events_header + "\n".join(events))

    def generate_srt(self, transcript_segments: list, output_path: str):
        # Standard SRT generation
        with open(output_path, "w", encoding="utf-8") as f:
            for i, word in enumerate(transcript_segments):
                # We group by sentences or chunks ideally.
                # Just dumping words for now or reuse chunk logic
                # Let's assume input is already chunked or we chunk it.
                pass 
                # Implementing simple chunking
        
        # Actually, let's reuse the chunking logic
        words = transcript_segments
        chunk_size = 5
        count = 1
        
        with open(output_path, "w", encoding="utf-8") as f:
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i+chunk_size]
                if not chunk: continue
                
                start = chunk[0]['start']
                end = chunk[-1]['end']
                text = " ".join([w['word'] for w in chunk])
                
                def fmt(s):
                    ms = int((s % 1) * 1000)
                    s = int(s)
                    h = s // 3600
                    m = (s % 3600) // 60
                    s = s % 60
                    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                
                f.write(f"{count}\n")
                f.write(f"{fmt(start)} --> {fmt(end)}\n")
                f.write(f"{text}\n\n")
                count += 1

subtitle_service = SubtitleService()
