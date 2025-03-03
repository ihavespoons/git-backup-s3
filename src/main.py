import os
import boto3
import tarfile
from datetime import datetime
from pathlib import Path

# Constants
TEMP_DIR = "tmp/backup"
ARCHIVE_EXTENSION = ".tar.gz"

def get_and_validate_inputs():
    """Get and validate the inputs from GitHub Actions environment"""
    target_bucket = os.environ.get("INPUT_TARGETBUCKET")
    bucket_region = os.environ.get("INPUT_BUCKET-REGION")
    role_arn = os.environ.get("INPUT_ROLE-ARN")
    oidc_audience = os.environ.get("INPUT_OIDC-AUDIENCE")
    backup_prefix = os.environ.get("INPUT_BACKUP-PREFIX", "backup")
    keep_versions = int(os.environ.get("INPUT_KEEP-VERSIONS", "5"))

    if not all([target_bucket, bucket_region, role_arn]):
        raise ValueError("Missing required inputs")
    
    if keep_versions < 1:
        raise ValueError("keep-versions must be greater than 0")

    return {
        "target_bucket": target_bucket,
        "bucket_region": bucket_region,
        "role_arn": role_arn,
        "oidc_audience": oidc_audience,
        "backup_prefix": backup_prefix,
        "keep_versions": keep_versions
    }

def setup_aws_credentials(inputs):
    """Setup AWS credentials using OIDC"""
    os.environ["AWS_REGION"] = inputs["bucket_region"]
    
    # Get GitHub OIDC token
    with open(os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]) as f:
        id_token = f.read().strip()

    # Setup STS client
    sts = boto3.client('sts')
    
    # Assume role with web identity
    response = sts.assume_role_with_web_identity(
        RoleArn=inputs["role_arn"],
        RoleSessionName="deploy-s3-python-action",
        WebIdentityToken=id_token,
        DurationSeconds=3600
    )

    # Set AWS credentials in environment
    credentials = response['Credentials']
    os.environ["AWS_ACCESS_KEY_ID"] = credentials["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = credentials["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = credentials["SessionToken"]

def create_backup_archive(prefix):
    """Create a backup archive of the repository"""
    # Get repository name from GitHub context
    repo_name = os.environ["GITHUB_REPOSITORY"].split("/")[-1]
    
    # Create temp directory if it doesn't exist
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    # Generate archive name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archive_name = f"{prefix}_{repo_name}_{timestamp}{ARCHIVE_EXTENSION}"
    archive_path = str(Path(TEMP_DIR) / archive_name)
    
    # Create tar archive
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(os.environ["GITHUB_WORKSPACE"], arcname=".")
    
    return archive_path

def cleanup_old_backups(s3_client, bucket, prefix, keep_versions):
    """Clean up old backups keeping only the specified number of versions"""
    print(f"Checking for old backups to clean up...")
    
    # List all objects with the given prefix
    paginator = s3_client.get_paginator('list_objects_v2')
    all_backups = []
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            all_backups.extend(page['Contents'])
    
    # Sort backups by last modified time (newest first)
    sorted_backups = sorted(all_backups, 
                          key=lambda x: x['LastModified'],
                          reverse=True)
    
    # If we have more backups than we want to keep
    if len(sorted_backups) > keep_versions:
        backups_to_delete = sorted_backups[keep_versions:]
        print(f"Deleting {len(backups_to_delete)} old backup(s)")
        
        # Delete old backups
        objects_to_delete = [{'Key': obj['Key']} for obj in backups_to_delete]
        s3_client.delete_objects(
            Bucket=bucket,
            Delete={'Objects': objects_to_delete}
        )

def sync_to_s3(bucket, archive_path, keep_versions):
    """Sync the backup archive to S3 and manage versions"""
    s3 = boto3.client('s3')
    archive_name = Path(archive_path).name
    prefix = archive_name.split('_')[0]  # Get prefix from archive name
    
    print(f"Syncing backup to S3 bucket s3://{bucket}/")
    with open(archive_path, 'rb') as archive:
        s3.upload_fileobj(
            archive,
            bucket,
            archive_name
        )
    
    # Clean up old backups if keep_versions is specified
    cleanup_old_backups(s3, bucket, prefix, keep_versions)

def cleanup():
    """Cleanup temporary files"""
    print("Cleaning up temporary files...")
    if Path(TEMP_DIR).exists():
        import shutil
        shutil.rmtree(TEMP_DIR)

def run():
    """Main function to run the action"""
    try:
        inputs = get_and_validate_inputs()
        setup_aws_credentials(inputs)
        archive_path = create_backup_archive(inputs["backup_prefix"])
        sync_to_s3(
            inputs["target_bucket"], 
            archive_path, 
            inputs["keep_versions"]
        )
    except Exception as error:
        print(f"::error::Action failed: {str(error)}")
        exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    run()