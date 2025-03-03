# Backup to AWS S3 GitHub Action

A GitHub Action that automatically backs up your repository to AWS S3 using OIDC (OpenID Connect) authentication.

## Features

- 🔐 Secure authentication using AWS OIDC provider
- 📦 Creates compressed tar archives of your repository
- ⏱️ Timestamps backups for version tracking
- 🧹 Automatic cleanup of old backup versions
- 🔄 Configurable number of backup versions to retain

## Usage

```yaml
name: Backup Repository
on:
  schedule:
    - cron: '0 0 * * *'  # Daily backup at midnight
  workflow_dispatch:      # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    name: Backup to S3
    steps:
      - name: Backup Repository
        uses: ihavespoons/git-backup-s3@v1
        with:
          target-bucket: 'your-backup-bucket'
          bucket-region: 'us-east-1'
          role-arn: 'arn:aws:iam::123456789012:role/BackupRole'
          backup-prefix: 'backup'           # Optional, defaults to 'backup'
          keep-versions: '5'               # Optional, defaults to 5
          oidc-audience: 'sts.amazonaws.com' # Optional
```

## Prerequisites

1. An S3 bucket to store backups
2. An IAM role with appropriate permissions and trust relationship for GitHub Actions OIDC
3. GitHub Actions workflow permissions configured for OIDC

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `target-bucket` | Name of the S3 bucket | Yes | - |
| `bucket-region` | AWS region of the bucket | Yes | - |
| `role-arn` | ARN of the IAM role to assume | Yes | - |
| `backup-prefix` | Prefix for backup file names | No | `backup` |
| `keep-versions` | Number of backup versions to retain | No | `5` |
| `oidc-audience` | OIDC audience value | No | `sts.amazonaws.com` |

## How It Works

1. Authenticates with AWS using OIDC provider
2. Creates a compressed tar archive of the repository
3. Uploads the archive to S3 with timestamp
4. Manages backup versions by cleaning up old backups
5. Cleans up temporary files

## IAM Role Requirements

The IAM role needs the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.