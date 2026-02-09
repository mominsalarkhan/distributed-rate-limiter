from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import time
from app.rate_limiter import RateLimiter
from app.config import settings

app = FastAPI(title="Distributed Rate Limiter")

# Initialize rate limiter
rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to check rate limits on all requests."""
    
    # Skip rate limiting for stats and health endpoints
    if request.url.path.startswith("/stats/") or request.url.path == "/health":
        return await call_next(request)
    
    # Extract user_id from query params or headers
    user_id = request.query_params.get("user_id") or request.headers.get("X-User-ID")
    
    if not user_id:
        return JSONResponse(
            status_code=400,
            content={"error": "user_id required (query param or X-User-ID header)"}
        )
    
    # Check rate limit
    is_allowed, remaining = rate_limiter.check_rate_limit(user_id)
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "limit": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window,
                "retry_after": settings.rate_limit_window
            },
            headers={
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + settings.rate_limit_window)),
                "Retry-After": str(settings.rate_limit_window)
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "rate-limiter"}

@app.get("/api/data")
async def get_data():
    """Sample API endpoint that's rate limited."""
    return {
        "message": "Success! This request was allowed.",
        "timestamp": time.time()
    }

@app.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get rate limit stats for a specific user."""
    stats = rate_limiter.get_stats(user_id)
    return stats

@app.get("/health")
async def health_check():
    """Health check that bypasses rate limiting."""
    try:
        # Check Redis connection
        rate_limiter.redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "redis": "disconnected", "error": str(e)}
        )