import logging
import os
import tempfile
from functools import wraps
from typing import Any, cast

import telegramify_markdown
import tiktoken
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from chatgpt_md_converter import telegram_format
from dotenv import load_dotenv
from telegram_text_splitter import split_markdown_into_chunks
from telegramify_markdown.config import get_runtime_config

from .logger import Logger
from .model import get_model

# Customize symbols (optional)
markdown_symbol = get_runtime_config().markdown_symbol
markdown_symbol.heading_level_1 = "\U0001f4cc"
markdown_symbol.link = "\U0001f517"

load_dotenv(os.path.join(os.getcwd(), ".env"))

log = cast(logging.Logger, Logger(filename="logs/app.log", level="info"))

_admin_id = os.getenv("ADMIN_ID")
assert _admin_id is not None, "ADMIN_ID not set"
ADMIN_ID = int(_admin_id)

_telegram_token = os.getenv("TELEGRAM_TOKEN")
assert _telegram_token is not None, "TELEGRAM_TOKEN not set"
TELEGRAM_TOKEN = _telegram_token

_allowed_ids = os.getenv("ALLOWED_USER_IDS")
assert _allowed_ids is not None, "ALLOWED_USER_IDS not set"
ALLOWED_USER_IDS = [int(i) for i in _allowed_ids.split(",") if i != ""]

_gemini_key = os.getenv("GEMINI_API_KEY")
assert _gemini_key is not None, "GEMINI_API_KEY not set"
GEMINI_API_KEY = _gemini_key
AYGUL_API_KEY = os.getenv("AYGUL_API_KEY")

API_KEY = GEMINI_API_KEY
MODEL_NAME = "gemini-2.5-flash"

model = get_model(API_KEY, log, MODEL_NAME)

bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Global session storage
user_sessions: dict[int, Any] = {}

dp = Dispatcher()


def trim_history_by_tokens(history, max_history_tokens=700_000, encoding_name="gpt2", prompt=None):
    """Trim chat history to fit within token limits."""
    encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(text):
        return len(encoding.encode(text))

    prompt_tokens = count_tokens(prompt)
    max_tokens = max_history_tokens - prompt_tokens

    trimmed_history = []
    total_tokens = 0

    for msg in reversed(history):
        text = getattr(msg, "text", str(msg))
        tokens = count_tokens(text)
        if total_tokens + tokens > max_tokens:
            break
        trimmed_history.insert(0, msg)
        total_tokens += tokens

    return trimmed_history


def authorized_only(handler):
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        assert message.from_user is not None
        user_id = message.from_user.id
        if user_id not in ALLOWED_USER_IDS:
            await message.reply("Sorry, you are not authorized to use this bot.")
            log.warning(f"Unauthorized access attempt by user ID: {user_id}")
            return
        return await handler(message, *args, **kwargs)

    return wrapper


async def download_file(bot: Bot, file_id: str) -> str:
    """Download file from Telegram and return its path."""
    file = await bot.get_file(file_id)
    file_path = file.file_path
    assert file_path is not None

    suffix = os.path.splitext(file_path)[1] or ".txt"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_path = temp_file.name

    await bot.download_file(file_path, destination=temp_path)
    return temp_path


async def read_file_content(file_path: str) -> str:
    """Read file content and return as string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


@dp.message(CommandStart())
@authorized_only
async def send_welcome(message: Message):
    assert message.from_user is not None
    await message.reply(
        f"Hi, {message.from_user.full_name}!\n"
        f"I'm a bot powered by Gemini. How can I help you today?"
    )


@dp.message(Command("new_chat"))
@authorized_only
async def new_chat(message: Message):
    assert message.from_user is not None
    user_id = message.from_user.id
    if user_id in user_sessions:
        old_session = user_sessions[user_id]
        if hasattr(old_session, "history"):
            old_session.history.clear()
        del user_sessions[user_id]

    user_sessions[user_id] = model.start_chat()
    await message.reply("✅ New chat session started. Let's begin!")


@dp.message(Command("change_model"))
@authorized_only
async def change_model(message: Message):
    global MODEL_NAME, model
    assert message.from_user is not None
    user_id = message.from_user.id
    MODEL_NAME = "gemini-2.5-pro" if MODEL_NAME == "gemini-2.5-flash" else "gemini-2.5-flash"
    model = get_model(API_KEY, log, MODEL_NAME)

    user_sessions[user_id] = model.start_chat()
    await message.reply(f"✅ Model changed to {MODEL_NAME}")


@dp.message(
    lambda message: message.document
    and message.document.file_name.endswith((".py", ".ipynb", "txt"))
)
@authorized_only
async def handle_code_file(message: types.Message, model=model):
    assert message.from_user is not None
    user_id = message.from_user.id
    if not model:
        await message.reply("❌ AI model is not configured. Please contact the administrator.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        assert message.document is not None
        file_path = await download_file(bot, message.document.file_id)
        file_content = await read_file_content(file_path)
        os.unlink(file_path)

        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])

        chat_session = user_sessions[user_id]
        user_prompt = message.caption or message.text or "Please analyze this file"
        prompt = f"User request: {user_prompt}\nFile content: {file_content}"

        chat_session.history = trim_history_by_tokens(chat_session.history, prompt=prompt)
        response = chat_session.send_message(prompt)

        for chunk in split_markdown_into_chunks(telegram_format(response.text)):
            await message.answer(telegramify_markdown.markdownify(chunk), parse_mode="MarkdownV2")

    except Exception as e:
        log.error(f"Error processing file: {e}")
        await message.reply("⚠️ An error occurred while processing your file.")


@dp.message()
@authorized_only
async def handle_message(message: types.Message, model=model):
    global API_KEY
    assert message.from_user is not None
    user_id = message.from_user.id

    if not model:
        await message.reply("❌ AI model is not configured. Please contact the administrator.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])

        chat_session = user_sessions[user_id]

        chat_session.history = trim_history_by_tokens(chat_session.history, prompt=message.text)
        response = chat_session.send_message(message.text)
        for chunk in split_markdown_into_chunks(response.text):
            await message.answer(telegramify_markdown.markdownify(chunk), parse_mode="MarkdownV2")

    except Exception as e:
        log.error(f"Error processing message: {e}")
        await message.reply("⚠️ An error occurred while processing your request")
        if any(
            sub in str(e)
            for sub in ["Resource has been exhausted", "service is temporarily unavailable"]
        ):
            API_KEY = (
                AYGUL_API_KEY if API_KEY == GEMINI_API_KEY else GEMINI_API_KEY
            ) or GEMINI_API_KEY
            model = get_model(AYGUL_API_KEY, log, MODEL_NAME)
            user_sessions[user_id] = model.start_chat(history=[])
            await message.reply("API_KEY changed")


async def start_bot(bot: Bot):
    BotName = await bot.get_my_name()
    await bot.send_message(ADMIN_ID, text=f"Бот {BotName.name} запущен", disable_notification=True)


async def stop_bot(bot: Bot):
    BotName = await bot.get_my_name()
    await bot.send_message(ADMIN_ID, text=f"Бот {BotName.name} выключен", disable_notification=True)
