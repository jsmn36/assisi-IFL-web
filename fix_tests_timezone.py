import os
import re

def fix_tests_utc(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        if "venv" in dirpath or ".pytest_cache" in dirpath or "__pycache__" in dirpath:
            continue
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if "datetime.utcnow()" in content or "datetime.utcnow" in content:
                print(f"Fixing {filepath}")
                content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
                content = content.replace("datetime.utcnow", "datetime.now(timezone.utc)")
                
                # Make sure timezone is imported
                if "import timezone" not in content and "from datetime import datetime, timezone" not in content:
                    if "from datetime import datetime\n" in content:
                        content = content.replace("from datetime import datetime\n", "from datetime import datetime, timezone\n")
                    elif "import datetime\n" in content:
                        content = content.replace("import datetime\n", "import datetime\nfrom datetime import timezone\n")
                    else:
                        content = "from datetime import timezone\n" + content
                        
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

if __name__ == "__main__":
    fix_tests_utc("backend/tests")
