import os
import re

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))

count_files = 0
count_lines = 0


def process_file(filepath):
    global count_files, count_lines
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Match `datetime.utcnow()` -> `datetime.now(timezone.utc)`
    # Match `datetime.utcnow` (e.g., in default=...) -> `lambda: datetime.now(timezone.utc)`

    if "datetime.utcnow" in content:
        # First we add `timezone` import if `datetime` is imported but not `timezone`
        if "from datetime import" in content and "timezone" not in content:
            content = re.sub(
                r"(from datetime import [a-zA-Z0-9_, ]+)",
                r"\1, timezone",
                content,
                count=1,
            )
        elif "import datetime" in content and "timezone" not in content:
            content = content.replace(
                "import datetime", "import datetime\nfrom datetime import timezone"
            )

        # Now replace function calls
        # `datetime.utcnow()`
        new_content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
        # `datetime.utcnow` (without parens, common in SQLAlchemy defaults)
        # But wait, we might have just replaced `datetime.utcnow()` so the ones left are without parens
        new_content = new_content.replace(
            "datetime.utcnow", "lambda: datetime.now(timezone.utc)"
        )

        # In case we created `lambda: datetime.now(timezone.utc)()` by mistake if someone else did something weird:
        new_content = new_content.replace(
            "lambda: datetime.now(timezone.utc)()", "datetime.now(timezone.utc)"
        )

        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            count_files += 1


for root, _, files in os.walk(base_dir):
    for f in files:
        if f.endswith(".py") and not f.startswith("__"):
            process_file(os.path.join(root, f))

print(f"Updated {count_files} files.")
