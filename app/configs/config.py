import os
from dotenv import load_dotenv


BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


if not BOT_TOKEN or not GEMINI_API_KEY:
    load_dotenv()
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError('Ошибка: не задан BOT_TOKEN/GEMINI_API_KEY. Проверьте файл .env')
