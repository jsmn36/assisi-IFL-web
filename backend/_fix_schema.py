import sqlite3

conn = sqlite3.connect("./pms.db")
c = conn.cursor()

# Check current schema for rate_plans
c.execute("SELECT sql FROM sqlite_master WHERE name='rate_plans'")
row = c.fetchone()
if row:
    print("Current schema:")
    print(row[0])

    # Check if room_type_id is NOT NULL
    if (
        "room_type_id" in row[0]
        and "NOT NULL" in row[0].split("room_type_id")[1].split(",")[0]
    ):
        print("\nroom_type_id is NOT NULL - fixing...")

        # SQLite doesn't support ALTER COLUMN, so we need to recreate
        # Step 1: Get existing data
        c.execute("SELECT COUNT(*) FROM rate_plans")
        count = c.fetchone()[0]
        print(f"Existing rows: {count}")

        # Step 2: Rename old table
        c.execute("ALTER TABLE rate_plans RENAME TO rate_plans_old")

        # Step 3: Create new table with nullable room_type_id
        new_schema = row[0].replace(
            "room_type_id INTEGER NOT NULL", "room_type_id INTEGER"
        )
        c.execute(new_schema)

        # Step 4: Copy data
        c.execute("INSERT INTO rate_plans SELECT * FROM rate_plans_old")

        # Step 5: Drop old table
        c.execute("DROP TABLE rate_plans_old")

        conn.commit()
        print("Fixed! room_type_id is now nullable.")

        # Verify
        c.execute("SELECT sql FROM sqlite_master WHERE name='rate_plans'")
        print("\nNew schema:")
        print(c.fetchone()[0])
    else:
        print("\nroom_type_id is already nullable - no fix needed.")
else:
    print("rate_plans table not found!")

conn.close()
