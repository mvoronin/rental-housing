# Rental Housing

[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.md)
[![ru](https://img.shields.io/badge/lang-ru-green.svg)](README.ru.md)

[![CI](https://github.com/YOUR_USERNAME/rental-housing/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/rental-housing/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/rental-housing/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/rental-housing)

Django application for tracking rental payments: leases, rent rates, payments, and money transactions.

## Features

- Lease management with multi-currency support (RUB, USD, EUR)
- Rent rate history with effective date ranges
- Rent and extra payment tracking
- Money transactions for payment reconciliation
- Russian and English language support
- Automatic dark/light theme (follows system preferences)
- Payment suggestions with auto-calculation (JavaScript)

## Requirements

- Python 3.13+
- uv (package manager)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd rental-housing

# Configure environment
cp .env.example .env

# Install dependencies and create virtual environment
make setup

# Apply migrations
make migrate

# Run development server
make runserver
```

The application will be available at http://127.0.0.1:8000

## Commands

```bash
make setup              # Initial setup
make runserver          # Run server
make migrate            # Apply migrations
make makemigrations     # Create migrations
make test               # Run tests (pytest)
make test-cov           # Tests with coverage report
make lint               # Code linting (ruff)
make format             # Code formatting (ruff)
make audit              # Vulnerability check (pip-audit)
make check              # Lint + audit + tests
```

## Project Structure

```
rental-housing/
├── leases/                 # Main application
│   ├── models.py           # Data models
│   ├── views.py            # Views
│   ├── forms.py            # Forms
│   ├── templates/          # Templates
│   ├── static/             # Static files (CSS, JS)
│   └── tests/              # Tests (pytest)
├── rental_housing/         # Project configuration
├── locale/                 # Translation files
├── .github/workflows/      # GitHub Actions CI
├── conftest.py             # pytest fixtures
└── Makefile                # Development commands
```

## CI/CD

The project uses GitHub Actions for continuous integration:
- Code linting (ruff)
- Dependency security audit (pip-audit)
- Tests with coverage reporting
- Codecov integration

After creating the repository on GitHub:
1. Replace `YOUR_USERNAME` in badges with your username
2. Add `CODECOV_TOKEN` to repository secrets (Settings → Secrets → Actions)

## License

MIT
