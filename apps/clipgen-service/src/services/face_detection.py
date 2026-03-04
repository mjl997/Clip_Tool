import cv2
import mediapipe as mp
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FaceDetectionService:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    def detect_face_center(self, frame):
        """
        Detects the center x-coordinate of the most prominent face.
        Returns normalized x (0.0 - 1.0). If no face, returns 0.5 (center).
        """
        results = self.face_detection.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if not results.detections:
            return 0.5
            
        # Find the largest face (closest to camera usually)
        max_area = 0
        center_x = 0.5
        
        for detection in results.detections:
            bboxC = detection.location_data.relative_bounding_box
            area = bboxC.width * bboxC.height
            if area > max_area:
                max_area = area
                center_x = bboxC.xmin + (bboxC.width / 2)
                
        return center_x

    def analyze_video_for_cropping(self, video_path: str, interval_sec: float = 1.0) -> list:
        """
        Analyzes video at intervals to determine crop centers over time.
        Returns list of (timestamp, center_x).
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        centers = []
        current_sec = 0
        
        while True:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_sec * 1000)
            ret, frame = cap.read()
            if not ret:
                break
                
            center_x = self.detect_face_center(frame)
            centers.append((current_sec, center_x))
            
            current_sec += interval_sec
            if current_sec > duration:
                break
                
        cap.release()
        return centers

face_service = FaceDetectionService()
