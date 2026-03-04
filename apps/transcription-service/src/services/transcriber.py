from faster_whisper import WhisperModel
from ..config import settings
import logging
import json
import os

logger = logging.getLogger(__name__)

class TranscriberService:
    def __init__(self):
        self.model_size = settings.WHISPER_MODEL_SIZE
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE
        logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path: str, job_id: str):
        segments, info = self.model.transcribe(audio_path, word_timestamps=True)
        
        logger.info(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        transcript = []
        full_text = ""
        
        # Generator to list
        for segment in segments:
            for word in segment.words:
                transcript.append({
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "confidence": word.probability
                })
            full_text += segment.text
            
        result = {
            "language": info.language,
            "duration": info.duration,
            "text": full_text,
            "words": transcript
        }
        
        return result

transcriber = TranscriberService()
