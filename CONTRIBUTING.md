# Contributing to Git Backup S3 Action

Thank you for your interest in contributing to the Git Backup S3 Action! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/ihavespoons/git-backup-s3.git
cd git-backup-s3
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Testing

We use pytest for testing. Run the test suite with:

```bash
pytest tests/
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document functions and classes using docstrings
- Keep lines under 88 characters (we use Black for formatting)

## Submitting Changes

1. Fork the repository
2. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes
4. Run tests and linting:
```bash
pytest tests/
black .
flake8
```

5. Commit your changes:
```bash
git commit -m "feat: description of your changes"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

6. Push to your fork and submit a pull request

## Pull Request Guidelines

- Include tests for new functionality
- Update documentation as needed
- Ensure CI passes
- Link any related issues
- Include a clear description of the changes

## Security

- For security issues, please refer to our [Security Policy](SECURITY.md)
- Do not commit AWS credentials or other secrets
- Use environment variables for sensitive values

## Documentation

- Update README.md for user-facing changes
- Document new features with examples
- Keep security-related documentation up to date

## Questions or Need Help?

- Open a [GitHub Discussion](https://github.com/ihavespoons/git-backup-s3/discussions) for questions
- Open an [Issue](https://github.com/ihavespoons/git-backup-s3/issues) for bugs or feature requests

## License

By contributing, you agree that your contributions will be licensed under the MIT License.