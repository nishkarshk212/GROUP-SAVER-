"""
Redis Queue Worker
Processes NSFW detection tasks asynchronously
"""

from redis import Redis
from rq import Queue, Worker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, TEMP_DIR
from detector import NSFWDetector
from frames import extract_gif_frames, extract_video_frames, convert_tgs_to_gif, cleanup_files


def process_media_task(task_data: dict) -> dict:
    """
    Process a single media file for NSFW content
    
    Args:
        task_data: {
            'file_path': str,
            'media_type': str,  # 'photo', 'animation', 'video', 'sticker'
            'message_id': int,
            'chat_id': int,
            'user_id': int
        }
    
    Returns:
        {
            'is_nsfw': bool,
            'score': float,
            'method': str,
            'frames_analyzed': int
        }
    """
    file_path = task_data.get('file_path')
    media_type = task_data.get('media_type')
    
    detector = NSFWDetector()
    result = {
        'is_nsfw': False,
        'score': 0.0,
        'method': '',
        'frames_analyzed': 0
    }
    
    try:
        if media_type == 'photo' or media_type == 'sticker':
            # Single image analysis
            is_nsfw, score, method = detector.is_nsfw(file_path)
            result.update({
                'is_nsfw': is_nsfw,
                'score': score,
                'method': method,
                'frames_analyzed': 1
            })
        
        elif media_type == 'animation':
            # Animated GIF/WebP - extract and scan frames
            frames = extract_gif_frames(file_path, sample_rate=4)
            result['frames_analyzed'] = len(frames)
            
            # Scan each frame
            max_score = 0.0
            for frame in frames:
                is_nsfw, score, _ = detector.is_nsfw(frame)
                if score > max_score:
                    max_score = score
                
                if is_nsfw:
                    result.update({
                        'is_nsfw': True,
                        'score': score,
                        'method': 'animated_frame_analysis'
                    })
                    cleanup_files(frames)
                    return result
            
            result.update({
                'is_nsfw': max_score > 0.7,
                'score': max_score,
                'method': 'animated_frame_analysis'
            })
            cleanup_files(frames)
        
        elif media_type == 'video':
            # Video - extract and scan frames
            frames = extract_video_frames(file_path, sample_rate=5)
            result['frames_analyzed'] = len(frames)
            
            # Scan each frame
            max_score = 0.0
            for frame in frames:
                is_nsfw, score, _ = detector.is_nsfw(frame)
                if score > max_score:
                    max_score = score
                
                if is_nsfw:
                    result.update({
                        'is_nsfw': True,
                        'score': score,
                        'method': 'video_frame_analysis'
                    })
                    cleanup_files(frames)
                    return result
            
            result.update({
                'is_nsfw': max_score > 0.7,
                'score': max_score,
                'method': 'video_frame_analysis'
            })
            cleanup_files(frames)
        
        # Cleanup original file
        try:
            os.remove(file_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        print(f"Error processing task: {e}")
        result['error'] = str(e)
        return result


def start_worker():
    """Start the RQ worker"""
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    
    # Create queues
    nsfw_queue = Queue('nsfw_detection', connection=redis_conn)
    
    print("🚀 Starting NSFW Detection Worker...")
    print(f"   Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"   Queue: nsfw_detection")
    
    # Start worker
    worker = Worker([nsfw_queue], connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    start_worker()
