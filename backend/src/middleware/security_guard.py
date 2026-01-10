from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from src.core.security.kill_switch import kill_switch
from src.core.security.rate_limiter import rate_limiter
import os

# Configuration
ADMIN_KEY = os.getenv("ADMIN_KEY", "admin123")  # In prod, this comes from Secrets Manager
DEMO_HEADER = "X-DEMO-MODE"
DEMO_LIMITS = {
    "max_tokens_per_session": 100000,
    "max_upload_size_kb": 200,
}

async def security_guard(request: Request, call_next):
    """
    Consolidated Security Middleware.
    Enforces:
    1. Kill Switch
    2. Rate Limiting
    3. Auth/Role Access Checks
    """
    
    # -----------------------------------------------------------------------
    # 0. Identify Requestor (Admin vs Public/Demo)
    # -----------------------------------------------------------------------
    # Check for Admin Key or Identity Header (Simulated IdP downstream)
    auth_header = request.headers.get("Authorization", "")
    identity_email = request.headers.get("X-User-Email", "") # In prod, from verifiable JWT
    
    is_admin = False
    
    # Method A: Direct Admin Key (Legacy/Service-to-Service)
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token == ADMIN_KEY:
             is_admin = True
             
    # Method B: Identity Resolution (Phase 4 Requirement)
    if identity_email == "founder@thesovereignmechanica.ai":
        # In a real system, we'd verify the JWT signature here.
        # For this stage, we assume the Gateway/LoadBalancer verifies auth
        # and passes trusted headers.
        is_admin = True

    client_ip = request.client.host if request.client else "unknown"

    # -----------------------------------------------------------------------
    # 1. KILL SWITCH CHECK
    # -----------------------------------------------------------------------
    if kill_switch.is_active():
        if not is_admin:
             return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "System is currently locked by admnistrator. Please try again later.", "code": "KILL_SWITCH_ACTIVE"}
            )
    
    # -----------------------------------------------------------------------
    # 2. RATE LIMITING
    # -----------------------------------------------------------------------
    # Admin: No Limit
    # Demo/Public: 60 req/min (1 req/sec average, burst 10)
    if not is_admin:
        if not rate_limiter.is_allowed(client_ip, capacity=10, refill_rate_per_second=1.0):
             return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded.", "code": "RATE_LIMITED"}
            )

    # -----------------------------------------------------------------------
    # 3. DEMO GUARD & ROLE CHECKS
    # -----------------------------------------------------------------------
    path = request.url.path
    method = request.method
    is_demo_mode = request.headers.get(DEMO_HEADER) == "true"

    if is_demo_mode:
        # Block Dangerous Methods
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Whitelist
            allowed_paths = [
                "/api/v1/ingest/upload", 
                "/api/v1/reasoning/analyze",
                "/api/auth/demo-token"
            ]
            if not any(path.startswith(p) for p in allowed_paths):
                 return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Action execution is disabled in Demo Mode.", "code": "DEMO_RESTRICTION"}
                )

    # Proceed
    response = await call_next(request)
    return response
