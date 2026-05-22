# Gemini Telegram Bot

[![CI](https://github.com/dinis-a/new_gemini_bot/actions/workflows/ci.yml/badge.svg)](https://github.com/dinis-a/new_gemini_bot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/dinisak/gemini_bot)

A Telegram bot powered by **Google Gemini AI** that provides intelligent conversations, code analysis, and multi-session chat management. Deployed via Docker with persistent logging.

## Features

- **AI-Powered Chat** -- Conversational AI using Gemini 2.5 Flash and Pro models
- **Multi-Session Support** -- Isolated chat sessions via `/new_chat`
- **Model Switching** -- Toggle between Flash and Pro on the fly (`/change_model`)
- **Code File Analysis** -- Upload `.py`, `.ipynb`, or `.txt` files for AI code review
- **Access Control** -- Restrict usage to authorized Telegram user IDs
- **Smart History** -- Token-aware trimming keeps conversations within Gemini's context window
- **API Key Rotation** -- Automatic fallback to a secondary API key on rate-limit errors

## Quick Start

### 1. Clone & Configure

```bash
git clone git@github.com:dinis-a/new_gemini_bot.git
cd new_gemini_bot
cp example.env .env
# Edit .env with your Telegram bot token and Gemini API key
```

### 2. Run with Docker

```bash
mkdir -p logs && chmod 777 logs
docker compose up -d
```

### 3. Or Run Locally

```bash
pip install -r requirements.txt
python main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message |
| `/new_chat` | Start a new chat session (clears history) |
| `/change_model` | Toggle between Gemini Flash and Pro |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_TOKEN` | Yes | Telegram bot token from [BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | Yes | Primary [Gemini API key](https://aistudio.google.com/app/apikey) |
| `ALLOWED_USER_IDS` | Yes | Comma-separated list of allowed Telegram user IDs |
| `ADMIN_ID` | Yes | Telegram user ID that receives bot start/stop notifications |
| `AYGUL_API_KEY` | No | Fallback API key used when primary hits rate limits |

## Project Structure

```
.
├── gemini_bot/            # Application package
│   ├── __init__.py
│   ├── handlers.py        # Telegram message handlers and bot logic
│   ├── logger.py          # Rotating file + console logging
│   └── model.py           # Gemini AI model configuration
├── tests/                 # Unit tests
├── .github/workflows/     # CI pipeline (lint, type-check, test)
├── main.py                # Entry point
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml         # Project metadata and tool configs
├── requirements.txt
├── example.env
├── LICENSE
└── CHANGELOG.md
```

## Development

```bash
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=gemini_bot --cov-report=term

# Lint and format
black . && isort . && flake8 . && mypy gemini_bot/
```

## CI Pipeline

On every push and pull request to `main`, GitHub Actions runs **black**, **isort**, **flake8**, **mypy**, and **pytest** with coverage.

## License

MIT -- see [LICENSE](LICENSE).
