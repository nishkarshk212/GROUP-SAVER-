"""
Frame Extraction Module
Extract frames from GIFs, videos, and animated stickers
"""

import cv2
from PIL import Image
import os
from config import TEMP_DIR, GIF_FRAME_SAMPLE, FRAME_SAMPLE_RATE


def extract_gif_frames(path: str, sample_rate: int = GIF_FRAME_SAMPLE) -> list:
    """
    Extract frames from animated GIF/WebP
    
    Args:
        path: Path to GIF file
        sample_rate: Extract every Nth frame (default: 4)
    
    Returns:
        List of frame file paths
    """
    frames = []
    img = Image.open(path)
    
    try:
        for i in range(img.n_frames):
            img.seek(i)
            
            # Sample every Nth frame
            if i % sample_rate == 0:
                frame_path = os.path.join(TEMP_DIR, f"frame_{i}.png")
                img.save(frame_path, "PNG")
                frames.append(frame_path)
        
        print(f"Extracted {len(frames)} frames from GIF ({img.n_frames} total)")
    except Exception as e:
        print(f"Error extracting GIF frames: {e}")
    finally:
        img.close()
    
    return frames


def extract_video_frames(video_path: str, sample_rate: int = FRAME_SAMPLE_RATE) -> list:
    """
    Extract frames from video file
    
    Args:
        video_path: Path to video file
        sample_rate: Extract every Nth frame (default: 5)
    
    Returns:
        List of frame file paths
    """
    frames = []
    cap = cv2.VideoCapture(video_path)
    count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample every Nth frame
            if count % sample_rate == 0:
                frame_path = os.path.join(TEMP_DIR, f"video_frame_{count}.jpg")
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
            
            count += 1
        
        print(f"Extracted {len(frames)} frames from video ({count} total)")
    except Exception as e:
        print(f"Error extracting video frames: {e}")
    finally:
        cap.release()
    
    return frames


def convert_tgs_to_gif(tgs_path: str) -> str:
    """
    Convert Telegram TGS (Lottie) animated sticker to GIF
    
    Args:
        tgs_path: Path to .tgs file
    
    Returns:
        Path to converted GIF file
    """
    try:
        from lottie.importers.tgs import import_tgs
        from lottie.exporters.gif import export_gif
        
        gif_path = tgs_path.replace(".tgs", ".gif")
        animation = import_tgs(tgs_path)
        export_gif(animation, gif_path)
        print(f"Converted TGS to GIF: {gif_path}")
        return gif_path
    except ImportError:
        print("Lottie library not available")
        return None
    except Exception as e:
        print(f"Error converting TGS: {e}")
        return None


def cleanup_files(file_list: list) -> None:
    """Remove temporary files"""
    for file_path in file_list:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}")
