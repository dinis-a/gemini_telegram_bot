from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gemini_bot.handlers import authorized_only, trim_history_by_tokens


class TestTrimHistoryByTokens:
    def test_empty_history(self):
        result = trim_history_by_tokens([], prompt="test")
        assert result == []

    def test_history_within_limit(self):
        history = [MagicMock(text="short message")]
        result = trim_history_by_tokens(history, max_history_tokens=700_000, prompt="test")
        assert len(result) == 1

    def test_trims_long_history(self):
        long_text = "a" * 10000
        history = [MagicMock(text=long_text) for _ in range(10)]
        result = trim_history_by_tokens(history, max_history_tokens=100, prompt="")
        assert len(result) < 10

    def test_keeps_most_recent_messages(self):
        history = [MagicMock(text="first msg"), MagicMock(text="last msg")]
        result = trim_history_by_tokens(history, max_history_tokens=700_000, prompt="test")
        assert result[-1].text == "last msg"


class TestAuthorizedOnly:
    @pytest.mark.asyncio
    async def test_authorized_user(self):
        handler_called = False

        async def dummy_handler(message):
            nonlocal handler_called
            handler_called = True

        with patch("gemini_bot.handlers.ALLOWED_USER_IDS", [123]):
            wrapped = authorized_only(dummy_handler)
            message = AsyncMock()
            message.from_user.id = 123
            await wrapped(message)
            assert handler_called

    @pytest.mark.asyncio
    async def test_unauthorized_user(self):
        handler_called = False

        async def dummy_handler(message):
            nonlocal handler_called
            handler_called = True

        with patch("gemini_bot.handlers.ALLOWED_USER_IDS", [123]):
            wrapped = authorized_only(dummy_handler)
            message = AsyncMock()
            message.from_user.id = 999
            await wrapped(message)
            assert not handler_called
