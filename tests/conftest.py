import os


def pytest_configure():
    """Set environment variables needed for module imports during testing."""
    os.environ.setdefault("ADMIN_ID", "123456789")
    os.environ.setdefault("TELEGRAM_TOKEN", "123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    os.environ.setdefault("ALLOWED_USER_IDS", "123,456")
    os.environ.setdefault("GEMINI_API_KEY", "test_gemini_key")
