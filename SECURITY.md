# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Security Features

1. **OIDC Authentication**: This action uses OpenID Connect (OIDC) for secure authentication with AWS, eliminating the need for long-term AWS credentials.

2. **Temporary Credentials**: All AWS credentials are temporary and automatically rotated through AWS STS (Security Token Service).

3. **Minimal IAM Permissions**: The action requires only the minimum necessary S3 permissions to function:
   - `s3:PutObject`
   - `s3:ListBucket`
   - `s3:DeleteObject`

## Security Considerations

### AWS IAM Configuration

1. Always follow the principle of least privilege when configuring the IAM role
2. Restrict the role's trust relationship to your specific GitHub organization/repository
3. Consider adding condition keys in the trust policy:
   ```json
   {
     "Condition": {
       "StringLike": {
         "token.actions.githubusercontent.com:sub": "repo:your-org/your-repo:*"
       }
     }
   }
   ```

### Repository Security

1. Enable "Require reviewers" for workflow changes
2. Use specific version tags (e.g., `@v1`) rather than `@main` to prevent supply chain attacks
3. Regularly review workflow permissions and access controls

## Reporting a Vulnerability

If you discover a security vulnerability in this action:

1. **Do not** open a public GitHub issue
2. Email the details to [INSERT YOUR SECURITY EMAIL]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)

We will respond within 48 hours and work with you to address the vulnerability.

## Disclosure Policy

- Security vulnerabilities will be patched as quickly as possible
- A security advisory will be published for confirmed vulnerabilities
- Credit will be given to the reporter if desired

## Security Best Practices for Users

1. Always specify a version tag when using this action:
   ```yaml
   uses: ihavespoons/git-backup-s3@v1
   ```

2. Review the S3 bucket permissions and ensure public access is blocked

3. Enable S3 server-side encryption for your backup bucket

4. Monitor your AWS CloudTrail logs for any suspicious activity

5. Regularly rotate your backup versions using the `keep-versions` parameter

## Secure Configuration Example

```yaml
name: Secure Backup
permissions:
  id-token: write
  contents: read

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Backup Repository
        uses: ihavespoons/git-backup-s3@v1
        with:
          target-bucket: ${{ secrets.BACKUP_BUCKET }}
          bucket-region: 'us-east-1'
          role-arn: ${{ secrets.AWS_ROLE_ARN }}
          keep-versions: '5'
```

## Additional Resources

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)
- [OIDC in GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)