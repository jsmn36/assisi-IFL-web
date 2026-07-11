import os
import re

def fix_timezone_imports(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        if "venv" in dirpath or ".pytest_cache" in dirpath or "__pycache__" in dirpath:
            continue
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if timezone is used
            if "timezone.utc" in content and "timezone" not in content[:content.find("timezone.utc")]:
                # It's an issue if "from datetime import ... timezone" or "import timezone" is missing.
                if not re.search(r"import\s+.*timezone", content) and not re.search(r"from\s+datetime\s+import\s+.*timezone", content):
                    print(f"Fixing {filepath}")
                    # Try to replace from datetime import datetime
                    if "from datetime import datetime" in content:
                        if "from datetime import datetime, timezone" not in content:
                            content = content.replace("from datetime import datetime", "from datetime import datetime, timezone")
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(content)
                    elif "import datetime" in content:
                        content = content.replace("import datetime", "import datetime\nfrom datetime import timezone")
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                    else:
                        print(f"Warning: Could not auto-fix imports for {filepath}, manual fix needed.")

if __name__ == "__main__":
    fix_timezone_imports("backend/app")
    fix_timezone_imports("backend/tests")
