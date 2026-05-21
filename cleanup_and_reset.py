import os
import glob

print("Starting cleanup and database reset...")

# 1. Delete the database
db_path = "db.sqlite3"
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"[\u2713] Deleted {db_path}")
    except Exception as e:
        print(f"[!] Error deleting {db_path}: {e}")

# 2. Delete migration files (except __init__.py)
migration_dir = os.path.join("incubator", "migrations")
if os.path.exists(migration_dir):
    for filename in os.listdir(migration_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            file_path = os.path.join(migration_dir, filename)
            try:
                os.remove(file_path)
                print(f"[\u2713] Deleted migration: {filename}")
            except Exception as e:
                print(f"[!] Error deleting {filename}: {e}")

# 3. Delete unnecessary temporary scripts
unnecessary_files = ["fix_js.py"]
for f in unnecessary_files:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"[\u2713] Deleted temporary file: {f}")
        except Exception as e:
            print(f"[!] Error deleting {f}: {e}")

print("\nCleanup complete! To finish the reset, run the following commands:")
print("  1. python manage.py makemigrations")
print("  2. python manage.py migrate")
print("  3. python manage.py createsuperuser")
print("  4. python populate_rl.py")
