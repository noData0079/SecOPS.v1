from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import os

# Configuration
DEMO_LIMITS = {
    "max_tokens_per_session": 100000,
    "max_upload_size_kb": 200,
    "allow_execution": False,
    "demo_header": "X-DEMO-MODE"
}

# Simple in-memory usage tracking (In production use Redis)
_demo_usage = {}

async def demo_token_guard(request: Request, call_next):
    """
    Middleware to intercept 'X-DEMO-MODE' requests and enforce limits.
    """
    is_demo = request.headers.get(DEMO_LIMITS["demo_header"]) == "true"
    
    if is_demo:
        # 1. Block Execution Endpoints
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # List of forbidden paths for demo users (e.g., executing actions)
            # For now, we block ALL non-GET modifications unless whitelisted
            # Whitelisted: /upload (checked separately), /analyze (reasoning allowed)
            path = request.url.path
            allowed_paths = ["/api/v1/ingest/upload", "/api/v1/reasoning/analyze", "/api/v1/auth/demo-token"]
            
            if not any(path.startswith(p) for p in allowed_paths):
                 return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Action execution is disabled in Demo Mode."}
                )

        # 2. Token Accounting (Placeholder logic)
        # Real logic would extract session ID and check Redis
        # For now, we just pass through but logging usage
        # print(f"Demo Request: {request.url.path}")

    response = await call_next(request)
    return response

def validate_demo_upload(file_size: int):
    """
    Utility to validate file size for demo uploads.
    """
    limit_bytes = DEMO_LIMITS["max_upload_size_kb"] * 1024
    if file_size > limit_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Demo upload limit exceeded. Max size: {DEMO_LIMITS['max_upload_size_kb']}KB"
        )
