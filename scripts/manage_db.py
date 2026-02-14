import os
import sys
import shutil
import sqlalchemy
from pathlib import Path
from alembic.config import Config
from alembic import command

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.config import settings

def reset_database():
    """Drop all tables in the database to ensure a clean slate."""
    # Force use of pymysql for stability with special chars in password
    db_url = settings.database_url.replace("mysql+mysqlconnector", "mysql+pymysql")
    print(f"Connecting to database: {db_url.split('@')[-1]}") # Log safe part
    engine = sqlalchemy.create_engine(db_url)
    meta = sqlalchemy.MetaData()
    
    try:
        meta.reflect(bind=engine)
        print(f"Found {len(meta.tables)} tables. Dropping all...")
        meta.drop_all(bind=engine)
        # Also drop alembic_version table explicitly if it exists (though drop_all usually covers it)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS alembic_version"))
            conn.commit()
        print("Database cleaned.")
    except Exception as e:
        print(f"Error resetting database: {e}")
        # Proceeding anyway as it might be empty

def clear_alembic_versions():
    """Delete all files in alembic/versions/."""
    versions_dir = project_root / "alembic" / "versions"
    if versions_dir.exists():
        print("Clearing alembic/versions/ directory...")
        for file in versions_dir.glob("*.py"):
            file.unlink()
        # Also remove __pycache__
        pycache = versions_dir / "__pycache__"
        if pycache.exists():
            shutil.rmtree(pycache)
    print("Alembic versions cleared.")

def run_alembic_migration():
    """Run `alembic revision --autogenerate` and `alembic upgrade head`."""
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    
    # IMPORTANT: Alembic's env.py typically reads sqlalchemy.url from alembic.ini
    # which usually interpolates from os.environ.
    # We rely on src.config.settings to load the .env file, so the environment variable DATABASE_URL
    # should already be set if python-dotenv is working, OR we explicitly set it here.
    
    # We double-check that os.environ['DATABASE_URL'] is set correctly for alembic to pick it up
    # if alembic.ini uses `sqlalchemy.url = %(DATABASE_URL)s`.
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = settings.database_url

    print(f"DEBUG: Using DATABASE_URL for Alembic: {os.environ['DATABASE_URL']}")

    # However, Python's ConfigParser (used by Alembic) has trouble with '%' in values 
    # if ExtendedInterpolation is on. 
    # To bypass this, we can set the main_option directly in the config object.
    # Escape % to %% for ConfigParser
    safe_url = settings.database_url.replace("%", "%%")
    alembic_cfg.set_main_option("sqlalchemy.url", safe_url)

    print("Generating migration script...")
    # Clean output buffer
    sys.stdout.flush()
    try:
        command.revision(alembic_cfg, autogenerate=True, message="initial_schema_with_badge")
    except Exception as e:
        print(f"Error during revision generation: {e}")
        return

    print("Applying migration...")
    sys.stdout.flush()
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Error during upgrade: {e}")
        return
    print("Migration complete.")

def verify_schema():
    """Check if 'university' table has 'badge' column."""
    engine = sqlalchemy.create_engine(settings.database_url)
    insp = sqlalchemy.inspect(engine)
    columns = [c['name'] for c in insp.get_columns('university')]
    
    if 'badge' in columns:
        print("[SUCCESS] 'badge' column exists in 'university' table.")
    else:
        print(f"[FAILURE] 'badge' column missing. Found: {columns}")

if __name__ == "__main__":
    print("--- Starting DB Reset (SKIPPED - Done via debug script) & Migration ---")
    
    # 1. Reset DB
    # reset_database()
    
    # 2. Clear old migrations
    clear_alembic_versions()
    
    # 3. Run Alembic
    run_alembic_migration()
    
    # 4. Verify
    verify_schema()
