import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем .env

token = os.getenv("TOKEN")  # Получаем токен
allowed_user_id = set(map(int, filter(None, os.getenv("ALLOWED_USERS", "").split(","))))

