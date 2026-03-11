"""
NSFW Detector Module
Uses NudeNet for image classification and detection
"""

from nudenet import NudeDetector, NudeClassifier
from config import NSFW_THRESHOLD


class NSFWDetector:
    def __init__(self):
        self.detector = NudeDetector()
        try:
            self.classifier = NudeClassifier()
        except ImportError:
            self.classifier = None
    
    def is_nsfw(self, image_path: str) -> tuple:
        """
        Check if image is NSFW
        
        Returns:
            (is_nsfw: bool, score: float, method: str)
        """
        if self.classifier:
            # Use classifier for overall score
            result = self.classifier.classify(image_path)
            unsafe_score = list(result.values())[0].get("unsafe", 0.0)
            return unsafe_score > NSFW_THRESHOLD, unsafe_score, "classifier"
        else:
            # Fallback to detector
            detections = self.detector.detect(image_path)
            max_score = 0.0
            
            for item in detections:
                score = item.get("score", 0.0)
                if score > max_score:
                    max_score = score
                
                if score > NSFW_THRESHOLD:
                    return True, score, "detector"
            
            return max_score > NSFW_THRESHOLD, max_score, "detector"
    
    def detect_objects(self, image_path: str) -> list:
        """Detect specific NSFW objects in image"""
        return self.detector.detect(image_path)


# Singleton instance
detector = NSFWDetector()
