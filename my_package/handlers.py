import os
from chatgpt_md_converter import telegram_format
import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from collections import defaultdict
from my_package import Logger, get_model
from dotenv import load_dotenv
from telegram_text_splitter import split_markdown_into_chunks
import telegramify_markdown
from telegramify_markdown.customize import get_runtime_config
from functools import wraps
import tiktoken  

# Customize symbols (optional)
markdown_symbol = get_runtime_config().markdown_symbol
markdown_symbol.head_level_1 = "📌"  # Customize the first level title symbol
markdown_symbol.link = "🔗"  # Customize the link symbol

load_dotenv(os.path.join(os.getcwd(), '.env'))

log = Logger(filename=f"logs/app.log", level="info")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_IDS = [int(i) for i in os.getenv("ALLOWED_USER_IDS").split(',') if i != '']
GEMINI_API_KEY, AYGUL_API_KEY = os.getenv("GEMINI_API_KEY"), os.getenv("AYGUL_API_KEY")

API_KEY = GEMINI_API_KEY
MODEL_NAME = "gemini-2.5-flash"

model = get_model(API_KEY, log, MODEL_NAME)

bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Global session storage
user_sessions = {}

dp = Dispatcher()

def trim_history_by_tokens(history, max_history_tokens=700_000, encoding_name="gpt2", prompt=None):
    """
    Обрезает историю сообщений так, чтобы суммарное количество токенов не превышало max_tokens.
    history: список сообщений chat_session.history
    max_tokens: максимальное количество токенов для всей истории
    """
    encoding = tiktoken.get_encoding(encoding_name)
    
    def count_tokens(text):
        return len(encoding.encode(text))
    
    prompt_tokens = count_tokens(prompt)
    max_tokens = max_history_tokens - prompt_tokens

    trimmed_history = []
    total_tokens = 0
    
    # идем с конца (сохраняем последние сообщения)
    for msg in reversed(history):
        # msg может быть объектом, берем только текст
        text = getattr(msg, "text", str(msg))
        tokens = count_tokens(text)
        if total_tokens + tokens > max_tokens:
            break
        trimmed_history.insert(0, msg)  # вставляем в начало, чтобы сохранить порядок
        total_tokens += tokens
        
    return trimmed_history

def authorized_only(handler):
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in ALLOWED_USER_IDS:
            await message.reply("Sorry, you are not authorized to use this bot.")
            log.warning(f"Unauthorized access attempt by user ID: {user_id}")
            return
        return await handler(message, *args, **kwargs)
    return wrapper

async def download_file(bot: Bot, file_id: str) -> str:
    """Download file from Telegram and return its path"""
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    # Create a temporary file
    suffix = os.path.splitext(file_path)[1] if os.path.splitext(file_path)[1] else '.txt'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_path = temp_file.name
    
    await bot.download_file(file_path, destination=temp_path)
    return temp_path

async def read_file_content(file_path: str) -> str:
    """Read file content and return as string"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

@dp.message(CommandStart())
@authorized_only
async def send_welcome(message: Message):
    await message.reply(f"Hi, {message.from_user.full_name}!\nI'm a bot powered by Gemini. How can I help you today?")

@dp.message(Command("new_chat"))
@authorized_only
async def new_chat(message: Message):
    user_id = message.from_user.id
    # Clear old session if exists
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
    global MODEL_NAME
    user_id = message.from_user.id
    MODEL_NAME = "gemini-2.5-pro" if MODEL_NAME == "gemini-2.5-flash" else "gemini-2.5-flash"
    model = get_model(API_KEY, log, MODEL_NAME=MODEL_NAME)

    user_sessions[user_id] = model.start_chat()

    await message.reply(f"✅ Model changed to {MODEL_NAME}")



@dp.message(lambda message: message.document and message.document.file_name.endswith(('.py', '.ipynb', 'txt')))
@authorized_only
async def handle_code_file(message: types.Message, model=model):
    user_id = message.from_user.id
    if not model:
        await message.reply("❌ AI model is not configured. Please contact the administrator.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Download the file
        file_path = await download_file(bot, message.document.file_id)
        file_content = await read_file_content(file_path)
        
        # Clean up the temporary file
        os.unlink(file_path)

        # Initialize session if not exists
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])

        chat_session = user_sessions[user_id]

        # Use the message caption or text as the prompt, or a default if empty
        user_prompt = message.caption or message.text or "Please analyze this file"
        
        # Combine the user's prompt with the file content
        prompt = f"""User request: {user_prompt}
                     File content: {file_content}
                  """

        # Send message with managed history
        chat_session.history = trim_history_by_tokens(chat_session.history, prompt=prompt)
        response = chat_session.send_message(prompt)
        
        for chunk in split_markdown_into_chunks(telegram_format(response.text)):
            await message.answer(telegramify_markdown.markdownify(chunk), parse_mode='MarkdownV2')
            

    except Exception as e:
        log.error(f"Error processing file: {e}")
        await message.reply("⚠️ An error occurred while processing your file.")

@dp.message()
@authorized_only
async def handle_message(message: types.Message, model=model):
    global API_KEY, MODEL_NAME
    user_id = message.from_user.id

    if not model:
        await message.reply("❌ AI model is not configured. Please contact the administrator.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Initialize session if not exists
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])

        chat_session = user_sessions[user_id]


        # Send message with managed history
        chat_session.history = trim_history_by_tokens(chat_session.history, prompt=message.text)
        response = chat_session.send_message(message.text)
        for chunk in split_markdown_into_chunks(response.text):
            await message.answer(telegramify_markdown.markdownify(chunk), parse_mode='MarkdownV2')

    except Exception as e:
        log.error(f"Error processing message: {e}")
        await message.reply("⚠️ An error occurred while processing your request")
        if any(sub in str(e) for sub in ['Resource has been exhausted', 'service is temporarily unavailable']):
            API_KEY = AYGUL_API_KEY if API_KEY == GEMINI_API_KEY else GEMINI_API_KEY
            model = get_model(AYGUL_API_KEY, log, MODEL_NAME)
            user_sessions[user_id] = model.start_chat(history=[])
            await message.reply("API_KEY changed")


async def start_bot(bot: Bot):
    BotName = await bot.get_my_name()
    await bot.send_message(ADMIN_ID, 
                           text=f"Бот {BotName.name} запущен", 
                           disable_notification=True)
    
async def stop_bot(bot: Bot):
    BotName = await bot.get_my_name()
    await bot.send_message(ADMIN_ID, 
                           text=f"Бот {BotName.name} выключен", 
                           disable_notification=True)
