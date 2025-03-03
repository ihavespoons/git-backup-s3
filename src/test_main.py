import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
from datetime import datetime
from src.main import (
    get_and_validate_inputs,
    setup_aws_credentials,
    create_backup_archive,
    sync_to_s3,
    cleanup_old_backups,
    cleanup,
    run,
    TEMP_DIR
)

@pytest.fixture
def mock_env():
    env = {
        "INPUT_TARGETBUCKET": "test-bucket",          # Changed from TARGET-BUCKET
        "INPUT_BUCKET-REGION": "us-east-1",
        "INPUT_ROLE-ARN": "arn:aws:iam::123456789012:role/test-role",
        "INPUT_OIDC-AUDIENCE": "sts.amazonaws.com",
        "INPUT_KEEP-VERSIONS": "3",
        "INPUT_BACKUP-PREFIX": "backup",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "token123",
        "GITHUB_REPOSITORY": "test-org/test-repo",
        "GITHUB_WORKSPACE": "/workspace"
    }
    with patch.dict(os.environ, env, clear=True):
        yield env

def test_get_and_validate_inputs_success(mock_env):
    inputs = get_and_validate_inputs()
    assert inputs["target_bucket"] == "test-bucket"
    assert inputs["bucket_region"] == "us-east-1"
    assert inputs["role_arn"] == "arn:aws:iam::123456789012:role/test-role"
    assert inputs["backup_prefix"] == "backup"
    assert inputs["keep_versions"] == 3  # Add this assertion

def test_get_and_validate_inputs_with_versions(mock_env):
    inputs = get_and_validate_inputs()
    assert inputs["target_bucket"] == "test-bucket"
    assert inputs["bucket_region"] == "us-east-1"
    assert inputs["role_arn"] == "arn:aws:iam::123456789012:role/test-role"
    assert inputs["backup_prefix"] == "backup"
    assert inputs["keep_versions"] == 3

def test_get_and_validate_inputs_invalid_versions():
    env = {
        "INPUT_TARGETBUCKET": "test-bucket",          # Changed from TARGET-BUCKET
        "INPUT_BUCKET-REGION": "us-east-1",
        "INPUT_ROLE-ARN": "arn:aws:iam::123456789012:role/test-role",
        "INPUT_OIDC-AUDIENCE": "sts.amazonaws.com",
        "INPUT_BACKUP-PREFIX": "backup",
        "INPUT_KEEP-VERSIONS": "0",  # Invalid value
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "token123",
        "GITHUB_REPOSITORY": "test-org/test-repo",
        "GITHUB_WORKSPACE": "/workspace"
    }
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError, match=r"keep-versions must be greater than 0"):
            get_and_validate_inputs()

def test_get_and_validate_inputs_missing():
    with pytest.raises(ValueError):
        with patch.dict(os.environ, {}, clear=True):
            get_and_validate_inputs()

@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        yield mock_s3

@pytest.fixture
def mock_backups():
    return {
        'Contents': [
            {
                'Key': 'backup_repo_20240301120000.tar.gz',
                'LastModified': datetime(2024, 3, 1, 12, 0, 0)
            },
            {
                'Key': 'backup_repo_20240301110000.tar.gz',
                'LastModified': datetime(2024, 3, 1, 11, 0, 0)
            },
            {
                'Key': 'backup_repo_20240301100000.tar.gz',
                'LastModified': datetime(2024, 3, 1, 10, 0, 0)
            },
            {
                'Key': 'backup_repo_20240301090000.tar.gz',
                'LastModified': datetime(2024, 3, 1, 9, 0, 0)
            }
        ]
    }

def test_cleanup_old_backups(mock_s3_client, mock_backups):
    # Setup mock paginator
    mock_paginator = MagicMock()
    mock_s3_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [mock_backups]

    # Test cleanup with keep_versions=2
    cleanup_old_backups(mock_s3_client, "test-bucket", "backup", 2)

    # Verify the correct objects were deleted
    mock_s3_client.delete_objects.assert_called_once()
    delete_call = mock_s3_client.delete_objects.call_args[1]
    assert delete_call["Bucket"] == "test-bucket"
    assert len(delete_call["Delete"]["Objects"]) == 2
    assert delete_call["Delete"]["Objects"][0]["Key"] == "backup_repo_20240301100000.tar.gz"
    assert delete_call["Delete"]["Objects"][1]["Key"] == "backup_repo_20240301090000.tar.gz"

@patch('boto3.client')
def test_setup_aws_credentials(mock_boto, mock_env):
    mock_sts = MagicMock()
    mock_boto.return_value = mock_sts
    mock_sts.assume_role_with_web_identity.return_value = {
        'Credentials': {
            'AccessKeyId': 'test-key',
            'SecretAccessKey': 'test-secret',
            'SessionToken': 'test-token'
        }
    }
    
    inputs = {
        "bucket_region": "us-east-1",
        "role_arn": "arn:aws:iam::123456789012:role/test-role"  # Added missing role_arn
    }
    
    with patch('builtins.open', mock_open(read_data="test-token")):
        setup_aws_credentials(inputs)

@patch('boto3.client')
def test_sync_to_s3_with_version_management(mock_boto, tmp_path):
    # Setup mock S3 client
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    
    # Create test archive
    test_archive = tmp_path / "backup_test_20240301120000.tar.gz"
    test_archive.write_text("test content")
    
    # Test sync with version management
    sync_to_s3("test-bucket", str(test_archive), 2)
    
    # Verify upload was called
    mock_s3.upload_fileobj.assert_called_once()
    
    # Verify cleanup was triggered
    mock_s3.get_paginator.assert_called_once_with('list_objects_v2')

def test_complete_backup_flow(mock_env, mock_s3_client, tmp_path):
    # Setup mock paginator for cleanup
    mock_paginator = MagicMock()
    mock_s3_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [{'Contents': []}]  # Empty backup list
    
    # Mock the STS assume role call
    mock_s3_client.assume_role_with_web_identity.return_value = {
        'Credentials': {
            'AccessKeyId': 'test-key',
            'SecretAccessKey': 'test-secret',
            'SessionToken': 'test-token'
        }
    }
    
    with patch('src.main.create_backup_archive') as mock_create_archive, \
         patch('builtins.open', mock_open(read_data="test-token")):
        
        test_archive = str(tmp_path / "backup_test_20240301120000.tar.gz")
        mock_create_archive.return_value = test_archive
        
        run()
        
        # Verify backup was created
        mock_create_archive.assert_called_once()
        
        # Verify upload to S3
        mock_s3_client.upload_fileobj.assert_called_once()
        
        # Verify cleanup was attempted
        mock_s3_client.get_paginator.assert_called_once_with('list_objects_v2')