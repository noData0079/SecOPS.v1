# Access Control Documentation

## Overview
TSM99 implements a robust access control mechanism leveraging **Supabase Authentication (JWT)** and **Role-Based Access Control (RBAC)** to secure API endpoints and resources.

## Authentication Mechanism
Authentication is enforced via Bearer Tokens (JWT). The system validates tokens using the Supabase Authentication service.

**Evidence Source:** `backend/src/api/deps.py`

### Token Validation
- All protected routes require a valid HTTP Bearer token.
- Tokens are decoded and validated for signature and expiration.
- **Fail-safe**: Invalid or missing tokens result in `401 Unauthorized`.

```python
# backend/src/api/deps.py

async def get_supabase_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # ...
    payload = decode_supabase_jwt(token)
    # ...
    return {
        "id": user_id,
        "role": payload.get("role", "authenticated"),
        # ...
    }
```

## Role-Based Access Control (RBAC)
The system defines clear roles and privileges to restrict access to sensitive operations.

### Roles
1.  **Authenticated**: Standard user access.
2.  **Service Role**: System-level access for internal services.
3.  **Admin / Superadmin**: Elevated privileges for configuration and emergency actions.

### Enforcement
Critical endpoints are guarded by the `require_admin` dependency, ensuring only authorized roles can execute sensitive actions.

```python
# backend/src/api/deps.py

async def require_admin(user: Dict[str, Any] = Depends(get_supabase_user)):
    role = user.get("role")
    if role not in ("service_role", "admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
```

## Emergency Access ("Break Glass")
For critical incidents, an emergency access protocol is defined.

- **Trigger**: `/emergency-access` endpoint.
- **Auditing**: All emergency actions are logged with `Severity: CRITICAL`.
- **Policy**: `GOVERNANCE_BINDER.md` (Section 3.3).

## Data Isolation
- **Tenant Isolation**: Data is scoped to the authenticated user/organization (via `org_id` context).
- **Execution Boundary**: All execution occurs within a sandboxed environment, separate from the control plane.
