import re
import os

import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.utils.markdown import hbold#, hcode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from collections import defaultdict

from my_package import Logger, get_model

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

log = Logger(filename=f"logs/app.log", level="info")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_IDS = [int(i) for i in os.getenv("ALLOWED_USER_IDS").split(',') if i != '']
GEMINI_API_KEY, AYGUL_API_KEY = os.getenv("GEMINI_API_KEY"), os.getenv("AYGUL_API_KEY")

API_KEY = GEMINI_API_KEY
MODEL_NAME = "gemini-2.5-flash"

model = get_model(API_KEY, log, MODEL_NAME)

bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))

# Global session storage
user_sessions = {}
user_message_counts = defaultdict(int)

dp = Dispatcher()

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
async def send_welcome(message: Message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USER_IDS:
        await message.reply(f"Hi, {hbold(message.from_user.full_name)}!\nI'm a bot powered by Gemini. How can I help you today?")
    else:
        await message.reply("Sorry, you are not authorized to use this bot.")
        log.warning(f"Unauthorized access attempt by user ID: {user_id}")

@dp.message(Command("new_chat"))
async def new_chat(message: Message):
    user_id = message.from_user.id

    if user_id not in ALLOWED_USER_IDS:
        await message.reply("Sorry, you are not authorized to use this bot.")
        return

    user_sessions[user_id] = model.start_chat()
    user_message_counts[user_id] = 0

    await message.reply("✅ New chat session started. Let's begin!")

@dp.message(Command("change_model"))
async def change_model(message: Message):
    global MODEL_NAME
    user_id = message.from_user.id

    if user_id not in ALLOWED_USER_IDS:
        await message.reply("Sorry, you are not authorized to use this bot.")
        return
    MODEL_NAME = "gemini-2.5-pro" if MODEL_NAME == "gemini-2.5-flash" else "gemini-2.5-flash"
    model = get_model(API_KEY, log, MODEL_NAME=MODEL_NAME)

    user_sessions[user_id] = model.start_chat()
    user_message_counts[user_id] = 0

    await message.reply(f"✅ Model changed to {MODEL_NAME}")

async def format_response(response_text: str) -> str:
    """Format the response to separate code blocks and fix nested bullet indentation."""
    formatted_lines = []

    for line in response_text.split('\n'):
        formatted_lines.append(line)
        # You can add more formatting logic here if needed

    return '\n'.join(formatted_lines)

def split_text_preserving_codeblocks(text, max_len=4000):
    """Improved version that better handles code block boundaries"""
    if len(text) <= max_len:
        return [text]

    # Split by code blocks first
    parts = re.split(r'(```[\s\S]*?```)', text)
    chunks = []
    current_chunk = ""
    
    for part in parts:
        # If adding this part would exceed max_len, finalize current chunk
        if len(current_chunk) + len(part) > max_len:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If part itself is too big (e.g., huge code block), split it
            if len(part) > max_len:
                if part.startswith('```') and part.endswith('```'):
                    # This is a code block - split carefully
                    language = part.split('\n')[0][3:]  # Get language if specified
                    code_content = part[len('```' + language):-3]
                    
                    # Split code content into lines
                    code_lines = code_content.split('\n')
                    temp_code = f"```{language}\n"
                    
                    for line in code_lines:
                        if len(temp_code) + len(line) + 1 > max_len - 3:  # -3 for ```
                            chunks.append(temp_code + "```")
                            temp_code = f"```{language}\n{line}\n"
                        else:
                            temp_code += line + "\n"
                    
                    if temp_code:
                        chunks.append(temp_code + "```")
                else:
                    # Regular text that's too long - split arbitrarily
                    for i in range(0, len(part), max_len):
                        chunks.append(part[i:i+max_len])
            else:
                current_chunk = part
        else:
            current_chunk += part
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

@dp.message(lambda message: message.document and message.document.file_name.endswith(('.py', '.ipynb', 'txt')))
async def handle_code_file(message: types.Message, model=model):
    user_id = message.from_user.id

    if user_id not in ALLOWED_USER_IDS:
        await message.reply("Sorry, you are not authorized to use this bot.")
        return

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
            user_message_counts[user_id] = 0

        chat_session = user_sessions[user_id]

        # Use the message caption or text as the prompt, or a default if empty
        user_prompt = message.caption or message.text or "Please analyze this file"
        
        # Combine the user's prompt with the file content
        prompt = f"""User request: {user_prompt}
                     File content: {file_content}
                  """

        # Send message with managed history
        response = chat_session.send_message(prompt)
        user_message_counts[user_id] += 1

        formatted_response = await format_response(response.text)
        
        # Split and send in chunks preserving Markdown code blocks
        chunks = split_text_preserving_codeblocks(formatted_response)
        for chunk in chunks:
            await message.answer(chunk)

    except Exception as e:
        log.error(f"Error processing file: {e}")
        await message.reply("⚠️ An error occurred while processing your file.")

@dp.message()
async def handle_message(message: types.Message, model=model):
    global API_KEY, MODEL_NAME
    user_id = message.from_user.id

    if user_id not in ALLOWED_USER_IDS:
        await message.reply("Sorry, you are not authorized to use this bot.")
        log.warning(f"Unauthorized message from user ID: {user_id}")
        return

    if not model:
        await message.reply("❌ AI model is not configured. Please contact the administrator.")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Initialize session if not exists
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])
            user_message_counts[user_id] = 0

        chat_session = user_sessions[user_id]

        # Trim history if exceeds 20 messages (10 user + 10 bot responses)
        if len(chat_session.history) >= 10:
            # Remove the oldest 2 messages (1 user + 1 bot)
            chat_session.history = chat_session.history[2:]
            user_message_counts[user_id] -= 1

        # Send message with managed history
        response = chat_session.send_message(message.text)
        user_message_counts[user_id] += 1

        formatted_response = await format_response(response.text)
        
        # Split and send in chunks preserving Markdown code blocks
        chunks = split_text_preserving_codeblocks(formatted_response)
        for chunk in chunks:
            await message.answer(chunk)

    except Exception as e:
        log.error(f"Error processing message: {e}")
        await message.reply("⚠️ An error occurred while processing your request.")
        if any(sub in str(e) for sub in ['Resource has been exhausted', 'service is temporarily unavailable']):
            API_KEY = AYGUL_API_KEY if API_KEY == GEMINI_API_KEY else GEMINI_API_KEY
            model = get_model(AYGUL_API_KEY, log, MODEL_NAME)
            user_sessions[user_id] = model.start_chat(history=[])
            user_message_counts[user_id] = 0
            await message.reply("API_KEY changed.")