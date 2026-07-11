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

            # Check if timezone.utc is used
            if "timezone.utc" in content:
                # Check if timezone is explicitly imported
                has_tz_import = re.search(r"import\s+.*timezone", content) or re.search(r"from\s+datetime\s+import\s+.*timezone", content)
                if not has_tz_import:
                    print(f"Fixing {filepath}")
                    if "from datetime import datetime\n" in content:
                        content = content.replace("from datetime import datetime\n", "from datetime import datetime, timezone\n")
                    elif "from datetime import datetime, " in content:
                        pass # complicated, might need manual check
                    elif "import datetime" in content:
                        content = content.replace("import datetime", "import datetime\nfrom datetime import timezone")
                    else:
                        content = "from datetime import timezone\n" + content
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)

if __name__ == "__main__":
    fix_timezone_imports("backend/app")
    fix_timezone_imports("backend/tests")
