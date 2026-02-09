import redis
import time
from typing import Tuple
from app.config import settings

class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if user has exceeded rate limit using sliding window.
        
        Returns:
            Tuple[bool, int]: (is_allowed, remaining_requests)
        """
        key = f"rate_limit:{user_id}"
        current_time = time.time()
        window_start = current_time - settings.rate_limit_window
        
        # Remove old entries outside the time window
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        request_count = self.redis_client.zcard(key)
        
        if request_count < settings.rate_limit_requests:
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, settings.rate_limit_window)
            
            remaining = settings.rate_limit_requests - request_count - 1
            return True, remaining
        else:
            remaining = 0
            return False, remaining
    
    def get_stats(self, user_id: str) -> dict:
        """Get current rate limit stats for a user."""
        key = f"rate_limit:{user_id}"
        current_time = time.time()
        window_start = current_time - settings.rate_limit_window
        
        # Clean old entries
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        request_count = self.redis_client.zcard(key)
        remaining = max(0, settings.rate_limit_requests - request_count)
        
        return {
            "user_id": user_id,
            "limit": settings.rate_limit_requests,
            "window_seconds": settings.rate_limit_window,
            "requests_made": request_count,
            "requests_remaining": remaining
        }