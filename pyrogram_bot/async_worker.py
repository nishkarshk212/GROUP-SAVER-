"""
Async Worker Pool for Media Processing
Uses asyncio for concurrent NSFW detection tasks
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict
import os

from optimized_detector import detector
from frames import extract_gif_frames, extract_video_frames, convert_tgs_to_gif, cleanup_files


class AsyncMediaWorker:
    def __init__(self, max_workers: int = 4):
        """
        Initialize async worker pool
        
        Args:
            max_workers: Maximum concurrent workers (default: 4)
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        print(f"🚀 Async worker pool initialized ({max_workers} workers)")
    
    async def process_photo(self, file_path: str) -> Dict:
        """
        Process photo asynchronously
        
        Returns:
            {is_nsfw: bool, score: float, method: str}
        """
        loop = asyncio.get_event_loop()
        
        # Run CPU-intensive detection in thread pool
        is_nsfw, score, _ = await loop.run_in_executor(
            self.executor,
            detector.detect_sticker,
            file_path
        )
        
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            'is_nsfw': is_nsfw,
            'score': score,
            'method': 'GPU-accelerated' if detector.use_gpu else 'CPU',
            'frames_analyzed': 1
        }
    
    async def process_animated_sticker(self, file_path: str, sample_rate: int = 3) -> Dict:
        """
        Process animated sticker (GIF/WebP) with frame extraction
        
        Args:
            file_path: Path to animated sticker
            sample_rate: Check every Nth frame (default: 3)
        
        Returns:
            {is_nsfw: bool, score: float, method: str, frames_analyzed: int}
        """
        loop = asyncio.get_event_loop()
        
        # Extract frames
        frames = await loop.run_in_executor(
            self.executor,
            extract_gif_frames,
            file_path,
            sample_rate  # Already samples in extraction
        )
        
        # Scan frames with optimized sampling
        is_nsfw, max_score, nsfw_frame = await loop.run_in_executor(
            self.executor,
            detector.scan_frames_optimized,
            frames,
            sample_rate  # Additional sampling layer
        )
        
        # Cleanup all frames
        cleanup_files(frames)
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            'is_nsfw': is_nsfw,
            'score': max_score,
            'method': f'Animated frame analysis ({len(frames)} frames)',
            'frames_analyzed': len(frames)
        }
    
    async def process_tgs_sticker(self, file_path: str, sample_rate: int = 3) -> Dict:
        """
        Process TGS (Lottie) animated sticker
        
        Args:
            file_path: Path to .tgs file
            sample_rate: Frame sampling rate
        
        Returns:
            Detection result dict
        """
        loop = asyncio.get_event_loop()
        
        # Convert TGS to GIF
        gif_path = file_path.replace('.tgs', '.gif')
        converted = await loop.run_in_executor(
            self.executor,
            convert_tgs_to_gif,
            file_path,
            gif_path
        )
        
        if not converted:
            return {'is_nsfw': False, 'score': 0.0, 'method': 'TGS conversion failed'}
        
        # Process as animated GIF
        result = await self.process_animated_sticker(gif_path, sample_rate)
        result['method'] = f'TGS → GIF → Frames ({result["frames_analyzed"]} frames)'
        
        return result
    
    async def process_video_sticker(self, file_path: str, sample_rate: int = 5) -> Dict:
        """
        Process video sticker (WebM) with frame extraction
        
        Args:
            file_path: Path to video file
            sample_rate: Extract every Nth frame (default: 5)
        
        Returns:
            Detection result dict
        """
        loop = asyncio.get_event_loop()
        
        # Extract frames from video
        frames = await loop.run_in_executor(
            self.executor,
            extract_video_frames,
            file_path,
            sample_rate
        )
        
        # Scan frames
        is_nsfw, max_score, nsfw_frame = await loop.run_in_executor(
            self.executor,
            detector.scan_frames_optimized,
            frames,
            sample_rate  # Double sampling for videos
        )
        
        # Cleanup
        cleanup_files(frames)
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            'is_nsfw': is_nsfw,
            'score': max_score,
            'method': f'Video frame analysis ({len(frames)} frames)',
            'frames_analyzed': len(frames)
        }
    
    async def process_media(self, file_path: str, media_type: str) -> Dict:
        """
        Universal media processor
        
        Args:
            file_path: Path to media file
            media_type: One of 'photo', 'animation', 'sticker', 'video'
        
        Returns:
            Detection result dict
        """
        print(f"📊 Processing {media_type}: {file_path}")
        
        if media_type == 'photo':
            return await self.process_photo(file_path)
        
        elif media_type == 'animation':
            return await self.process_animated_sticker(file_path)
        
        elif media_type == 'sticker':
            # Auto-detect sticker type
            if file_path.endswith('.tgs'):
                return await self.process_tgs_sticker(file_path)
            elif file_path.endswith('.webm'):
                return await self.process_video_sticker(file_path)
            else:
                # Static or animated WebP
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    if hasattr(img, 'n_frames') and img.n_frames > 1:
                        return await self.process_animated_sticker(file_path)
                    else:
                        return await self.process_photo(file_path)
                except:
                    return await self.process_photo(file_path)
        
        elif media_type == 'video':
            return await self.process_video_sticker(file_path)
        
        else:
            return {'is_nsfw': False, 'score': 0.0, 'method': f'Unknown type: {media_type}'}
    
    def shutdown(self):
        """Cleanup worker pool"""
        self.executor.shutdown(wait=True)


# Singleton instance
worker_pool = AsyncMediaWorker(max_workers=4)
