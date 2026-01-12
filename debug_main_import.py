import sys
import os
import logging

# Ensure backend is in path
sys.path.append(os.path.abspath("backend"))

from backend.src.main import app, admin

print(f"Admin module loaded: {admin}")
print("Registered Routes:")
for route in app.routes:
    if hasattr(route, "path"):
        if "/api/admin" in route.path:
            print(route.path)
