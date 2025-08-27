#!/usr/bin/env python3
"""
Скрипт для создания тестовых пользователей с разными ролями
"""

import os
import sys
from sqlalchemy.orm import Session
from database import get_db
from models_db import User, Department, Access
from passlib.context import CryptContext

# Инициализация хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users():
    """Создает тестовых пользователей с разными ролями"""
    print("👥 Создание тестовых пользователей...")
    
    db = next(get_db())
    
    try:
        # Создаем пользователей с разными ролями
        users_data = [
            {
                "login": "admin",
                "password": "admin123",
                "role_id": 1,  # Администратор
                "department_id": 1,  # IT отдел
                "access_id": 1,  # Публичный
                "full_name": "Администратор системы"
            },
            {
                "login": "head_it",
                "password": "head123",
                "role_id": 3,  # Глава отдела
                "department_id": 1,  # IT отдел
                "access_id": 2,  # Внутренний
                "full_name": "Глава IT отдела"
            },
            {
                "login": "head_hr",
                "password": "head123",
                "role_id": 3,  # Глава отдела
                "department_id": 2,  # HR отдел
                "access_id": 2,  # Внутренний
                "full_name": "Глава HR отдела"
            },
            {
                "login": "resp_it",
                "password": "resp123",
                "role_id": 4,  # Ответственный отдела
                "department_id": 1,  # IT отдел
                "access_id": 2,  # Внутренний
                "full_name": "Ответственный IT отдела"
            },
            {
                "login": "resp_hr",
                "password": "resp123",
                "role_id": 4,  # Ответственный отдела
                "department_id": 2,  # HR отдел
                "access_id": 2,  # Внутренний
                "full_name": "Ответственный HR отдела"
            },
            {
                "login": "user1",
                "password": "user123",
                "role_id": 2,  # Обычный пользователь
                "department_id": 1,  # IT отдел
                "access_id": 1,  # Публичный
                "full_name": "Пользователь IT отдела"
            },
            {
                "login": "user2",
                "password": "user123",
                "role_id": 2,  # Обычный пользователь
                "department_id": 2,  # HR отдел
                "access_id": 1,  # Публичный
                "full_name": "Пользователь HR отдела"
            }
        ]
        
        for user_data in users_data:
            existing = db.query(User).filter(User.login == user_data["login"]).first()
            if not existing:
                # Хешируем пароль
                hashed_password = pwd_context.hash(user_data["password"])
                
                user = User(
                    login=user_data["login"],
                    password=hashed_password,
                    role_id=user_data["role_id"],
                    department_id=user_data["department_id"],
                    access_id=user_data["access_id"],
                    full_name=user_data["full_name"]
                )
                
                db.add(user)
                print(f"   ✅ Создан пользователь: {user_data['login']} (роль: {user_data['role_id']})")
            else:
                print(f"   ⚠️ Пользователь уже существует: {user_data['login']}")
        
        db.commit()
        print("✅ Тестовые пользователи созданы успешно!")
        
        # Выводим список созданных пользователей
        print("\n📋 Список пользователей:")
        users = db.query(User).all()
        for user in users:
            role_names = {1: "Админ", 2: "Пользователь", 3: "Глава отдела", 4: "Ответственный отдела"}
            role_name = role_names.get(user.role_id, "Неизвестно")
            print(f"   - {user.login} ({role_name}) - {user.full_name}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании пользователей: {e}")
        raise

if __name__ == "__main__":
    create_test_users()
