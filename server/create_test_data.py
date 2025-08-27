#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных в базе данных
"""

import os
import sys
from sqlalchemy.orm import Session
from database import get_db
from models_db import User, Department, Access, Content, Tag
from passlib.context import CryptContext

# Инициализация хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_data():
    """Создает тестовые данные в базе данных"""
    print("🚀 Создание тестовых данных...")
    
    db = next(get_db())
    
    try:
        # 1. Создаем отделы (только если их нет)
        print("📁 Создание отделов...")
        department_names = ["IT отдел", "HR отдел", "Финансовый отдел", "Маркетинг", "Общий отдел"]
        
        for dept_name in department_names:
            existing = db.query(Department).filter(Department.department_name == dept_name).first()
            if not existing:
                dept = Department(department_name=dept_name)
                db.add(dept)
                print(f"   ✅ Создан отдел: {dept_name}")
            else:
                print(f"   ⚠️ Отдел уже существует: {dept_name}")
        
        db.commit()
        
        # 2. Создаем уровни доступа (только если их нет)
        print("🔐 Создание уровней доступа...")
        access_names = ["Публичный", "Внутренний", "Конфиденциальный", "Секретный"]
        
        for access_name in access_names:
            existing = db.query(Access).filter(Access.access_name == access_name).first()
            if not existing:
                access = Access(access_name=access_name)
                db.add(access)
                print(f"   ✅ Создан уровень доступа: {access_name}")
            else:
                print(f"   ⚠️ Уровень доступа уже существует: {access_name}")
        
        db.commit()
        
        # 3. Создаем пользователей
        print("👥 Создание пользователей...")
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
                "login": "Pavel2",
                "password": "123123",
                "role_id": 2,  # Обычный пользователь
                "department_id": 5,  # Общий отдел
                "access_id": 3,  # Конфиденциальный
                "full_name": "Павел Петров"
            },
            {
                "login": "user1",
                "password": "user123",
                "role_id": 2,  # Обычный пользователь
                "department_id": 2,  # HR отдел
                "access_id": 2,  # Внутренний
                "full_name": "Иван Иванов"
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
                print(f"   ✅ Создан пользователь: {user_data['login']} ({user_data['full_name']})")
            else:
                print(f"   ⚠️ Пользователь уже существует: {user_data['login']}")
        
        db.commit()
        
        # 4. Создаем теги
        print("🏷️ Создание тегов...")
        tags = [
            Tag(tag_name="Документация"),
            Tag(tag_name="Политики"),
            Tag(tag_name="Процедуры"),
            Tag(tag_name="Обучение")
        ]
        
        for tag in tags:
            existing = db.query(Tag).filter(Tag.tag_name == tag.tag_name).first()
            if not existing:
                db.add(tag)
                print(f"   ✅ Создан тег: {tag.tag_name}")
            else:
                print(f"   ⚠️ Тег уже существует: {tag.tag_name}")
        
        db.commit()
        
        # 5. Создаем тестовые документы
        print("📄 Создание тестовых документов...")
        
        # Создаем тестовый текстовый файл
        test_file_path = "test_document.txt"
        test_content = """
# Руководство по использованию системы

## Введение
Данное руководство описывает основные принципы работы с корпоративной системой управления документами.

## Основные функции
1. Загрузка документов
2. Поиск по содержимому
3. Категоризация документов
4. Управление доступом

## Процесс загрузки
Для загрузки документа необходимо:
- Выбрать файл в формате PDF, DOCX или TXT
- Указать название документа
- Выбрать отдел и уровень доступа
- Добавить описание (опционально)

## Поиск документов
Система поддерживает:
- Полнотекстовый поиск
- Поиск по тегам
- Фильтрация по отделам
- Сортировка по дате

## Безопасность
Все документы защищены системой аутентификации и авторизации.
Доступ к документам контролируется на уровне отделов и ролей пользователей.

## Поддержка
При возникновении вопросов обращайтесь в IT отдел.
        """
        
        # Сохраняем тестовый файл
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Создаем запись в базе данных
        existing_content = db.query(Content).filter(Content.title == "Руководство по использованию системы").first()
        if not existing_content:
            content = Content(
                title="Руководство по использованию системы",
                description="Подробное руководство по работе с системой управления документами",
                file_path=test_file_path,
                access_level=2,  # Внутренний
                department_id=5,  # Общий отдел
                tag_id=1  # Документация
            )
            db.add(content)
            print(f"   ✅ Создан документ: {content.title}")
        else:
            print(f"   ⚠️ Документ уже существует: {existing_content.title}")
        
        db.commit()
        
        print("\n✅ Тестовые данные успешно созданы!")
        print("\n📋 Созданные данные:")
        print(f"   - Отделов: {db.query(Department).count()}")
        print(f"   - Уровней доступа: {db.query(Access).count()}")
        print(f"   - Пользователей: {db.query(User).count()}")
        print(f"   - Тегов: {db.query(Tag).count()}")
        print(f"   - Документов: {db.query(Content).count()}")
        
        print("\n🔑 Данные для входа:")
        print("   - Логин: Pavel2, Пароль: 123123")
        print("   - Логин: admin, Пароль: admin123")
        print("   - Логин: user1, Пароль: user123")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
