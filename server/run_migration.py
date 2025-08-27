#!/usr/bin/env python3
"""
Скрипт для выполнения миграции добавления поля file_path в таблицу content_proposals
"""

import os
import sys
from sqlalchemy import create_engine, text

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Выполняет миграцию для добавления поля file_path в таблицу предложений"""
    
    # Получаем параметры подключения к базе данных
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "db")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "123123")
    
    # Создаем строку подключения
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        # Создаем подключение к базе данных
        engine = create_engine(connection_string)
        
        with engine.connect() as connection:
            print("🔄 Начинаем миграцию для добавления поля file_path в таблицу предложений...")
            
            # Проверяем, существует ли уже поле file_path
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'content_proposals' 
                AND COLUMN_NAME = 'file_path'
            """), {"db_name": db_name})
            
            if result.fetchone():
                print("   ✅ Поле file_path уже существует в таблице content_proposals")
                return
            
            # Проверяем, существует ли таблица content_proposals
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'content_proposals'
            """), {"db_name": db_name})
            
            if result.fetchone()[0] == 0:
                print("   ❌ Таблица content_proposals не существует. Сначала запустите основное приложение для создания таблиц.")
                return
            
            # Добавляем поле file_path
            print("📋 Добавляем поле file_path в таблицу content_proposals...")
            
            connection.execute(text("""
                ALTER TABLE `content_proposals` 
                ADD COLUMN `file_path` VARCHAR(500) NULL 
                COMMENT 'Путь к загруженному файлу' 
                AFTER `review_comment`
            """))
            
            print("   ✅ Поле file_path успешно добавлено в таблицу content_proposals")
            
            # Создаем директорию для предложений, если её нет
            proposals_dir = "/app/files/proposals"
            if not os.path.exists(proposals_dir):
                os.makedirs(proposals_dir, exist_ok=True)
                print(f"   ✅ Создана директория для предложений: {proposals_dir}")
            
            print("🎉 Миграция успешно завершена!")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
