import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем .env

token = os.getenv("TOKEN")  # Получаем токен
allowed_user_id = set(int(uid) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip().isdigit())
