"""Script to remove hard ImportError guards from task files."""
import glob

HARD_GUARD = 'from app.config import settings\nif not settings.is_postgresql_mode:\n    raise ImportError("This module requires PostgreSQL mode. Set DATABASE_URL to enable.")\n\n'

for path in glob.glob("app/tasks/*.py"):
    if "__init__" in path:
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if HARD_GUARD in content:
        content = content.replace(HARD_GUARD, "")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Removed hard guard from {path}")
    else:
        print(f"No hard guard found in {path}")
