"""
One-Time Sticker Detection Check
Checks each sticker only once and caches the result
Uses Redis for persistent caching
"""

from redis import Redis
import hashlib
from typing import Optional, Tuple
from config import REDIS_HOST, REDIS_PORT, REDIS_DB


class StickerCache:
    """Cache for sticker NSFW detection results"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        self.cache_prefix = "sticker_check:"
        self.cache_ttl = 86400 * 7  # Cache for 7 days
    
    def get_sticker_hash(self, file_id: str, file_path: str) -> str:
        """
        Generate unique hash for sticker
        
        Args:
            file_id: Telegram file ID
            file_path: Path to downloaded file
        
        Returns:
            SHA256 hash of sticker
        """
        # Combine file_id with file content hash
        hasher = hashlib.sha256()
        
        # Add file_id to hash
        hasher.update(file_id.encode())
        
        # Add file content to hash
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
        except Exception as e:
            print(f"Error reading file for hash: {e}")
        
        return hasher.hexdigest()
    
    def check_cached_result(self, sticker_hash: str) -> Optional[Tuple[bool, float]]:
        """
        Check if sticker has been analyzed before
        
        Args:
            sticker_hash: Unique hash of sticker
        
        Returns:
            (is_nsfw, score) if cached, None if not found
        """
        cache_key = f"{self.cache_prefix}{sticker_hash}"
        
        try:
            result = self.redis.get(cache_key)
            if result:
                is_nsfw_str, score_str = result.split(':')
                is_nsfw = is_nsfw_str == 'True'
                score = float(score_str)
                print(f"✅ Cache hit for sticker: NSFW={is_nsfw}, Score={score:.2f}")
                return is_nsfw, score
        except Exception as e:
            print(f"Cache read error: {e}")
        
        return None
    
    def cache_result(self, sticker_hash: str, is_nsfw: bool, score: float):
        """
        Cache detection result for future reference
        
        Args:
            sticker_hash: Unique hash of sticker
            is_nsfw: Detection result
            score: Confidence score
        """
        cache_key = f"{self.cache_prefix}{sticker_hash}"
        result_value = f"{is_nsfw}:{score}"
        
        try:
            # Store with 7 day expiration
            self.redis.setex(
                cache_key,
                self.cache_ttl,
                result_value
            )
            print(f"💾 Cached result: NSFW={is_nsfw}, Score={score:.2f} (7 days)")
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        try:
            keys = self.redis.keys(f"{self.cache_prefix}*")
            total_cached = len(keys)
            
            return {
                'total_cached': total_cached,
                'cache_ttl_days': self.cache_ttl // 86400
            }
        except Exception as e:
            return {
                'total_cached': 0,
                'cache_ttl_days': 7,
                'error': str(e)
            }
    
    def clear_cache(self):
        """Clear all cached sticker results"""
        try:
            keys = self.redis.keys(f"{self.cache_prefix}*")
            if keys:
                self.redis.delete(*keys)
                print(f"🗑️ Cleared {len(keys)} cached stickers")
        except Exception as e:
            print(f"Error clearing cache: {e}")


# Singleton instance
sticker_cache = StickerCache()


async def check_sticker_once(file_id: str, file_path: str, detector_func) -> Tuple[bool, float, str]:
    """
    Check sticker for NSFW content (only once per unique sticker)
    
    This function:
    1. Generates unique hash for the sticker
    2. Checks cache for previous analysis
    3. If cached → returns cached result immediately
    4. If not cached → runs detection, caches result, then returns
    
    Args:
        file_id: Telegram file ID
        file_path: Path to downloaded sticker file
        detector_func: Async function to detect NSFW content
    
    Returns:
        (is_nsfw, score, method) tuple
    """
    from optimized_detector import detector
    
    # Generate hash
    sticker_hash = sticker_cache.get_sticker_hash(file_id, file_path)
    
    # Check cache first
    cached_result = sticker_cache.check_cached_result(sticker_hash)
    
    if cached_result:
        is_nsfw, score = cached_result
        return is_nsfw, score, "cached_result"
    
    # Not in cache - run detection
    print("🔍 Running fresh NSFW detection...")
    
    # Run detector
    is_nsfw, max_score, _ = detector.detect_sticker(file_path)
    
    # Cache the result
    sticker_cache.cache_result(sticker_hash, is_nsfw, max_score)
    
    return is_nsfw, max_score, "fresh_detection"


def get_cache_info_text() -> str:
    """Get formatted cache info text"""
    stats = sticker_cache.get_cache_stats()
    
    text = "💾 **Sticker Cache Statistics**\n\n"
    text += f"**Total Stickers Cached:** {stats['total_cached']}\n"
    text += f"**Cache Duration:** {stats['cache_ttl_days']} days\n\n"
    text += "**Benefits:**\n"
    text += "• Same sticker checked only once\n"
    text += "• Instant response for known stickers\n"
    text += "• Reduces server load significantly\n"
    
    return text
