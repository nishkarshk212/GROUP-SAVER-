"""
Queue Manager for Redis-based task distribution
This replaces direct RQ usage with custom queue management
"""

from redis import Redis
import json
from config import REDIS_HOST, REDIS_PORT, REDIS_DB


class NSFWQueue:
    def __init__(self):
        self.redis_conn = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        self.queue_name = "nsfw_detection_queue"
    
    def enqueue(self, task_data: dict) -> str:
        """Add task to queue"""
        task_id = f"task_{self.redis_conn.incr('task_counter')}"
        task_data['id'] = task_id
        task_data['timestamp'] = self.redis_conn.time()[0]
        
        # Push to queue
        self.redis_conn.lpush(self.queue_name, json.dumps(task_data))
        
        print(f"Enqueued task {task_id}")
        return task_id
    
    def dequeue(self, timeout: int = 0) -> dict:
        """Get next task from queue (blocking)"""
        result = self.redis_conn.brpop(self.queue_name, timeout=timeout)
        
        if result:
            _, task_json = result
            return json.loads(task_json)
        return None
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.redis_conn.llen(self.queue_name)
    
    def clear_queue(self) -> None:
        """Clear all tasks from queue"""
        self.redis_conn.delete(self.queue_name)
        print("Queue cleared")


# Singleton instance
queue_manager = NSFWQueue()
