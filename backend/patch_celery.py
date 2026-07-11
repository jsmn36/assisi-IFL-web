import os
from pathlib import Path

backend_dir = Path(r"c:\Users\akash\pms-hotel-desktop\backend\app")

files_to_gate = [
    backend_dir / "core" / "celery_app.py",
    backend_dir / "core" / "celery_config.py",
    backend_dir / "tasks" / "base.py",
    backend_dir / "tasks" / "emails.py",
    backend_dir / "tasks" / "core.py",
    backend_dir / "tasks" / "email_tasks.py",
    backend_dir / "tasks" / "maintenance.py",
    backend_dir / "tasks" / "reports.py",
    backend_dir / "tasks" / "notifications.py",
    backend_dir / "tasks" / "template_emails.py",
    backend_dir / "tasks" / "__init__.py",
]

guard_str = """from app.config import settings
if not settings.is_postgresql_mode:
    raise ImportError("This module requires PostgreSQL mode. Set DATABASE_URL to enable.")

"""

for f in files_to_gate:
    if f.exists():
        content = f.read_text("utf-8")
        if "is_postgresql_mode" not in content:
            f.write_text(guard_str + content, "utf-8")
            print(f"Gated {f}")

# Also need to manually fix cm/worker.py, cm/worker_sync.py, core/cache.py and api/v1/system_health.py
