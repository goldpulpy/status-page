<div align="center">

![Status Page Banner](/assets/banner.png)

**Open Source ❤️, Simple and Self-Hosted Monitoring Platform**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-22+-green.svg)](https://nodejs.org/en/download/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

[Features](#features) • [Quick Start](#quick-start) • [Contributing](#contributing)

</div>

## Overview

Status Page is a lightweight, self-hosted monitoring platform designed to provide real-time visibility into your infrastructure's health.

<div align="center">

![Login page](/assets/status.png)

</div>

<details>

<summary>Admin panel screenshots</summary>

<div align="center">

![Login page](/assets/login.png)
![Groups page](/assets/groups.png)
![Monitors page](/assets/monitors.png)

</div>
</details>

### Key Highlights

- **User-Friendly Interface** - Easy setup and configuration
- **Real-time Monitoring** - Instant updates on service availability
- **Easy Deployment** - Docker support with comprehensive configuration options
- **Flexible Monitoring** - HTTP endpoint checks with customizable validation rules

## Features

- [x] **HTTP Endpoint Monitoring** - Track service availability with configurable health checks
- [ ] **Additional Protocols** - TCP, DNS, ICMP and more monitoring
- [x] **Custom Error Mapping** - Define specific error conditions and responses
- [x] **Status Validation** - Verify response codes, content patterns, and latency thresholds
- [x] **Service Grouping** - Organize monitors into logical groups for better visibility
- [ ] **Notifications** - Notify when incidents occur

### Technologies

- FastAPI (API/SSR)
- SQLAlchemy/Alembic
- Dependency Injector
- Jinja2 + AlpineJS
- TailwindCSS (PostCSS)

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+ (npm 11+)
- Docker and Docker Compose (optional)
- Make (for development commands)

### Installation

_⚠️ Important: Review [.env.example](.env.example) and update all credentials before deployment_

<details>

<summary>Option 1: Docker Compose (Pre-built)</summary>

```bash
mkdir -p status-page && cd status-page
wget https://raw.githubusercontent.com/goldpulpy/status-page/main/docker-compose.yaml
wget https://raw.githubusercontent.com/goldpulpy/status-page/main/.env.example
cp .env.example .env

nano .env  # ⚠️ Update credentials and settings

docker compose up -d

# Verify installation
docker compose ps
```

</details>

<details>

<summary>Option 2: Docker Compose (Self-Build)</summary>

```bash
git clone https://github.com/goldpulpy/status-page
cd status-page
cp .env.example .env

nano .env  # ⚠️ Update credentials and settings

docker compose up -d --build

# Verify installation
docker compose ps
```

</details>

<details>

<summary>Option 3: Manual Deployment</summary>

```bash
git clone https://github.com/goldpulpy/status-page
cd status-page
make install && make build
cp .env.example .env

nano .env  # ⚠️ Update credentials and settings

make migrate
make run
```

</details>

## Development

<details>
<summary>Make Commands</summary>

```bash
# Install all dependencies
make install

# Run development server
make run

# Build assets (JavaScript and CSS)
make build

# Code quality checks
make format        # Format code with ruff
make lint          # Lint code
make type-check    # Type checking with pyright
make security      # Security analysis with bandit

# Database operations
make migrate                    # Apply migrations
make create-migration m="..."   # Create new migration
make rollback-migration         # Rollback last migration
make migration-history          # View migration history

# Utilities
make clean         # Clean development artifacts
make requirements  # Export requirements.txt
make help          # Show all commands
```

</details>

<details>

<summary>PostgreSQL</summary>

#### Run PostgreSQL container

From the project root, execute:

```bash
docker compose -f dev/postgres/docker-compose.yaml up -d
```

This will start a PostgreSQL container with the configured environment.

**Default configuration:**

- Host: `localhost`
- Port: `5432`
- User: `root`
- Password: `toor`
- Database: `db`

You can access the Adminer UI at http://localhost:8080

Select the PostgreSQL database and log in with the provided credentials.

#### Stop and remove PostgreSQL container

```bash
docker compose -f docker/postgres/docker-compose.yaml down

# or if you want to remove data

docker compose -f docker/postgres/docker-compose.yaml down --volumes
```

</details>

<details>

<summary>Database Management</summary>

```bash
# Create a migration after model changes
make create-migration m="Add user authentication"

# Apply pending migrations
make migrate

# Rollback if needed
make rollback-migration
```

</details>

## API Documentation

Interactive API documentation is available in development mode:

- **Scalar API Reference** - `http://localhost:5000/docs`

_Note: Documentation endpoints are disabled in production for security_

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Run** quality checks (`make format lint type-check`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

Please ensure all tests pass and code quality checks succeed before submitting.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- **Issues** - Report bugs or request features via GitHub Issues
- **Documentation** - Comprehensive guides available in `/docs`
