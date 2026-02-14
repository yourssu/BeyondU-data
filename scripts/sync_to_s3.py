import os
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.config import settings

def sync_to_s3():
    """
    Sync local data/raw to S3.
    Uses credentials from .env via src.config.settings to run aws s3 sync.
    """
    # 1. Determine S3 bucket
    # Prefer the bucket from settings, but if it looks like the default and the user said otherwise,
    # we might want to be careful. For now, trusting settings or allowing an override arg would match best practices.
    # However, based on the user's command 's3://beyondu-data/raw/', we should ensure we target that if settings differs.
    
    bucket_name = settings.aws_s3_bucket
    # Basic check: if settings has the default "beyondu-raw-data" but user used "beyondu-data",
    # we might warn, but let's assume .env is correct for now.
    
    # We will use the user's specific target if provided in args, else settings.
    if len(sys.argv) > 1:
        target_s3_uri = sys.argv[1]
    else:
        target_s3_uri = f"s3://{bucket_name}/raw/"

    local_dir = project_root / "data" / "raw"

    print(f"Configuration:")
    print(f"  Local: {local_dir}")
    print(f"  Remote: {target_s3_uri}")
    print(f"  AWS Region: {settings.aws_region}")
    print("-" * 30)

    if not local_dir.exists():
        print(f"Error: Local directory '{local_dir}' does not exist.")
        return

    # 2. Prepare Environment with Credentials
    env = os.environ.copy()
    
    # Inject credentials from settings if available
    if settings.aws_access_key_id:
        env["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
        print("  [+] AWS_ACCESS_KEY_ID found in settings")
    else:
        print("  [!] AWS_ACCESS_KEY_ID NOT found in settings")

    if settings.aws_secret_access_key:
        env["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
        print("  [+] AWS_SECRET_ACCESS_KEY found in settings")
    else:
         print("  [!] AWS_SECRET_ACCESS_KEY NOT found in settings")

    if settings.aws_region:
        env["AWS_DEFAULT_REGION"] = settings.aws_region

    # 3. Run AWS CLI command
    cmd = ["aws", "s3", "sync", str(local_dir), target_s3_uri]
    
    print(f"\nExecuting: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, env=env, check=True)
        print("\n✅ Sync completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Sync failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("\n❌ Error: 'aws' command not found. Please ensure AWS CLI is installed and in PATH.")
        sys.exit(1)

if __name__ == "__main__":
    sync_to_s3()
