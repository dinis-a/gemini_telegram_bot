from unittest.mock import MagicMock, patch

from gemini_bot.model import get_model


class TestGetModel:
    def test_returns_model_on_success(self):
        with patch("gemini_bot.model.genai.configure"), \
             patch("gemini_bot.model.genai.GenerativeModel") as mock_gen:
            mock_model = MagicMock()
            mock_gen.return_value = mock_model
            logger = MagicMock()
            result = get_model("fake-key", logger, "gemini-2.5-flash")
            assert result is mock_model

    def test_returns_none_on_failure(self):
        with patch("gemini_bot.model.genai.configure", side_effect=Exception("API error")):
            logger = MagicMock()
            result = get_model("bad-key", logger, "gemini-2.5-flash")
            assert result is None
            logger.error.assert_called_once()


class TestLogger:
    def test_creates_logger(self):
        from gemini_bot.logger import Logger
        log = Logger(filename="test.log", level="info")
        assert log is not None
        assert log.name == "test.log"

    def test_reuses_same_logger(self):
        from gemini_bot.logger import Logger
        log1 = Logger(filename="reuse_test.log", level="info")
        log2 = Logger(filename="reuse_test.log", level="debug")
        assert log1 is log2

    def test_level_mapping(self):
        from gemini_bot.logger import Logger
        assert Logger.level_relations["debug"] == 10
        assert Logger.level_relations["info"] == 20
        assert Logger.level_relations["warning"] == 30
        assert Logger.level_relations["error"] == 40
        assert Logger.level_relations["crit"] == 50
