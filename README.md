# Gemini Telegram Bot

[![CI](https://github.com/dinisak/gemini-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/dinisak/gemini-telegram-bot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/dinisak/gemini_bot)

A production-ready Telegram bot powered by **Google Gemini AI** that provides intelligent conversations, code analysis, and multi-session chat management. Deployed via Docker with zero-downtime restarts.

## Features

- **AI-Powered Chat** -- Conversational AI using Google Gemini (Flash and Pro models)
- **Multi-Session Support** -- Each user gets an isolated chat session with `/new_chat`
- **Model Switching** -- Toggle between Gemini 2.5 Flash and Pro with `/change_model`
- **Code File Analysis** -- Upload `.py`, `.ipynb`, or `.txt` files for AI-powered code review
- **Access Control** -- Restrict bot usage to authorized Telegram user IDs
- **Smart History Management** -- Token-aware trimming keeps conversations within Gemini's context window
- **API Key Rotation** -- Automatic fallback to a secondary API key on rate-limit errors
- **Docker Deployment** -- One-command deployment via docker-compose with persistent logging

## Prerequisites

- Python 3.12+
- A [Telegram Bot Token](https://t.me/BotFather) from BotFather
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- Docker and docker-compose (for containerized deployment)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/dinisak/gemini-telegram-bot.git
cd gemini-telegram-bot
```

### 2. Set Up Environment

```bash
cp example.env .env
```

Edit `.env` with your credentials:

```ini
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
ALLOWED_USER_IDS=123456789,987654321
ADMIN_ID=123456789
```

### 3. Run with Docker

```bash
docker-compose up -d
```

### Or Run Locally

```bash
pip install -r requirements.txt
python main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and see welcome message |
| `/new_chat` | Start a new chat session (clears history) |
| `/change_model` | Toggle between Gemini Flash and Pro |

## Project Structure

```
.
├── gemini_bot/            # Application package
│   ├── __init__.py        # Package exports
│   ├── handlers.py        # Telegram message handlers and bot logic
│   ├── logger.py          # Rotating file + console logging setup
│   └── model.py           # Gemini AI model configuration
├── tests/                 # Unit tests
│   ├── test_handlers.py   # Handler and authorization tests
│   └── test_model.py      # Model and logger tests
├── .github/workflows/     # CI pipeline
│   └── ci.yml             # Linting, type checking, and testing
├── main.py                # Application entry point
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata and tool configs
├── example.env            # Environment variables template
├── .dockerignore          # Docker build exclusions
├── LICENSE                # MIT License
└── CHANGELOG.md           # Release history
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=gemini_bot --cov-report=term

# Format code
black .
isort .

# Lint
flake8 .

# Type check
mypy gemini_bot/
```

## CI Pipeline

On every push and pull request, GitHub Actions runs:

- **black** -- code formatting check
- **isort** -- import ordering check
- **flake8** -- style guide enforcement
- **mypy** -- static type checking
- **pytest** -- unit tests with coverage reporting

## License

This project is licensed under the MIT License -- see the [LICENSE](LICENSE) file for details.
