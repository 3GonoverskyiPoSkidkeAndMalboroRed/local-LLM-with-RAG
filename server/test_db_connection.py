#!/usr/bin/env python3
"""
Тест подключения к базе данных
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("🔍 Проверка подключения к базе данных...")

# Проверяем переменные окружения
database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL из переменных окружения: {database_url}")

# Проверяем подключение
try:
    from database import engine, check_connection
    print(f"Engine URL: {engine.url}")
    check_connection()
except Exception as e:
    print(f"❌ Ошибка подключения к базе данных: {e}")

# Проверяем, есть ли таблицы
try:
    from database import SessionLocal
    from models_db import Department
    
    db = SessionLocal()
    departments = db.query(Department).all()
    print(f"✅ Подключение к базе данных успешно! Найдено отделов: {len(departments)}")
    db.close()
    
except Exception as e:
    print(f"❌ Ошибка при работе с базой данных: {e}") 