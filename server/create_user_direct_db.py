#!/usr/bin/env python3
"""
Скрипт для прямого создания пользователя Pavel2 в базе данных
"""

import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_db import User

# Загружаем переменные окружения
load_dotenv()

# Инициализация хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user_direct():
    """Создает пользователя Pavel2 напрямую в базе данных"""
    
    # Параметры подключения к базе данных
    DATABASE_URL = "mysql+mysqlconnector://root:123123@localhost:3307/db_main"
    
    try:
        # Создание подключения к базе данных
        print("🔌 Подключение к базе данных...")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Проверяем, существует ли уже пользователь с таким логином
        existing_user = db.query(User).filter(User.login == "Pavel2").first()
        if existing_user:
            print("⚠️ Пользователь Pavel2 уже существует!")
            print(f"📋 ID: {existing_user.id}")
            print(f"📋 Логин: {existing_user.login}")
            print(f"📋 Роль: {existing_user.role_id}")
            print(f"📋 Отдел: {existing_user.department_id}")
            print(f"📋 Доступ: {existing_user.access_id}")
            print(f"📋 ФИО: {existing_user.full_name}")
            return
        
        # Хешируем пароль
        hashed_password = pwd_context.hash("123123")
        
        # Создаем нового пользователя
        new_user = User(
            login="Pavel2",
            password=hashed_password,
            role_id=1,
            department_id=5,
            access_id=3,
            full_name="YGF"
        )
        
        # Добавляем пользователя в базу данных
        print("👤 Создание пользователя Pavel2...")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("✅ Пользователь Pavel2 успешно создан!")
        print(f"📋 ID: {new_user.id}")
        print(f"📋 Логин: {new_user.login}")
        print(f"📋 Роль: {new_user.role_id}")
        print(f"📋 Отдел: {new_user.department_id}")
        print(f"📋 Доступ: {new_user.access_id}")
        print(f"📋 ФИО: {new_user.full_name}")
        print(f"📋 Дата создания: {new_user.created_at}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {str(e)}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🚀 Запуск прямого создания пользователя Pavel2 в базе данных...")
    create_user_direct()
