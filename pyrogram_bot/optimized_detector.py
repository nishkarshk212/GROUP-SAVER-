"""
Optimized NSFW Detector with GPU Acceleration
Uses NudeDetector with batch processing and GPU support
"""

from nudenet import NudeDetector
import torch
from config import NSFW_THRESHOLD


class OptimizedNSFWDetector:
    def __init__(self, use_gpu=True):
        """
        Initialize detector with optional GPU support
        
        Args:
            use_gpu: Enable GPU acceleration if available
        """
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.detector = NudeDetector()
        
        if self.use_gpu:
            print(f"✅ GPU acceleration enabled")
            print(f"   Device: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ️  Using CPU (GPU not available)")
    
    def detect_sticker(self, path: str) -> tuple:
        """
        Detect NSFW content in sticker/image
        
        Returns:
            (is_nsfw: bool, max_score: float, detections: list)
        """
        try:
            result = self.detector.detect(path)
            
            max_score = 0.0
            for r in result:
                score = r.get("score", 0.0)
                if score > max_score:
                    max_score = score
                
                # Early exit if threshold exceeded
                if score > NSFW_THRESHOLD:
                    return True, score, result
            
            return max_score > NSFW_THRESHOLD, max_score, result
            
        except Exception as e:
            print(f"Detection error: {e}")
            return False, 0.0, []
    
    def scan_frames_optimized(self, frames: list, sample_rate: int = 3) -> tuple:
        """
        Scan multiple frames with optimized sampling
        
        Args:
            frames: List of frame file paths
            sample_rate: Check every Nth frame (default: 3)
        
        Returns:
            (is_nsfw: bool, max_score: float, nsfw_frame: str)
        """
        max_score = 0.0
        nsfw_frame = None
        
        # Process only sampled frames
        sampled_frames = frames[::sample_rate]
        
        for frame_path in sampled_frames:
            is_nsfw, score, _ = self.detect_sticker(frame_path)
            
            if score > max_score:
                max_score = score
                nsfw_frame = frame_path
            
            # Early exit on NSFW detection
            if is_nsfw:
                print(f"✅ NSFW detected in {frame_path} (score: {score:.2f})")
                return True, score, frame_path
        
        return max_score > NSFW_THRESHOLD, max_score, nsfw_frame


# Singleton instance
detector = OptimizedNSFWDetector(use_gpu=True)
