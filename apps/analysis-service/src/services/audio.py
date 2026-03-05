import librosa
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AudioService:
    def analyze_audio(self, audio_path: str):
        try:
            y, sr = librosa.load(audio_path)
            
            # 1. Energy Peaks (RMS)
            hop_length = 512
            frame_length = 2048
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Normalize RMS
            rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
            
            # Detect peaks (high energy)
            peaks = np.where(rms_norm > 0.8)[0]
            peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
            
            # 2. Silence detection
            non_silent_intervals = librosa.effects.split(y, top_db=20) # Intervals of non-silence
            # We can infer silence from this, but simpler: check low RMS
            silence_mask = rms_norm < 0.1
            
            # 3. Laugh/Applause detection (Simplistic heuristic based on spectral flatness/centroid)
            # This is hard without a trained model.
            # We will use simple stats for now: high spectral centroid often correlates with brightness (laughter)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            
            # Summary stats
            duration = librosa.get_duration(y=y, sr=sr)
            avg_energy = np.mean(rms)
            max_energy = np.max(rms)
            
            # Group peaks into events (if peaks are close, merge them)
            # Simple clustering: if peaks are within 2 seconds, keep start of first and end of last
            events = []
            if len(peak_times) > 0:
                current_event = {"start": peak_times[0], "end": peak_times[0]}
                for t in peak_times[1:]:
                    if t - current_event["end"] < 2.0:
                        current_event["end"] = t
                    else:
                        events.append(current_event)
                        current_event = {"start": t, "end": t}
                events.append(current_event)

            logger.info(f"Audio analysis complete. Duration: {duration}s. Found {len(events)} energy events.")
            
            return {
                "duration": duration,
                "high_energy_events": events,
                "avg_energy": float(avg_energy),
                "max_energy": float(max_energy)
            }
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return {}

audio_service = AudioService()
