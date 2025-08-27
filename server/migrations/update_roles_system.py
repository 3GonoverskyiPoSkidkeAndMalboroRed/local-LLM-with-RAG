#!/usr/bin/env python3
"""
Миграция для обновления системы ролей доступа
Добавляет новые роли: Глава отдела, Ответственный отдела
Создает таблицу для системы предложений контента
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from database import Base
from models_db import User, Department, Access, Content, Tag

# Настройки подключения к базе данных
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+mysqlconnector://root:123123@localhost:3306/db_main")

# Создание движка и сессии
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_migration():
    """Выполняет миграцию для обновления системы ролей"""
    print("🔄 Начинаем миграцию системы ролей...")
    
    with engine.connect() as connection:
        try:
            # 1. Обновляем таблицу ролей
            print("📝 Обновляем таблицу ролей...")
            
            # Проверяем существование таблицы role
            inspector = inspect(engine)
            if 'role' not in inspector.get_table_names():
                # Создаем таблицу role если её нет
                connection.execute(text("""
                    CREATE TABLE `role` (
                        `id` int NOT NULL,
                        `role_name` varchar(45) NOT NULL,
                        PRIMARY KEY (`id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """))
                print("   ✅ Создана таблица role")
            
            # Очищаем существующие роли и добавляем новые
            connection.execute(text("DELETE FROM `role`"))
            connection.execute(text("""
                INSERT INTO `role` VALUES 
                (1, 'Админ'),
                (2, 'Пользователь'),
                (3, 'Глава отдела'),
                (4, 'Ответственный отдела')
            """))
            print("   ✅ Обновлены роли в системе")
            
            # 2. Создаем таблицу для предложений контента
            print("📋 Создаем таблицу предложений контента...")
            
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS `content_proposals` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `title` varchar(255) NOT NULL,
                    `description` text,
                    `access_level` int NOT NULL,
                    `department_id` int NOT NULL,
                    `tag_id` int,
                    `proposed_by` int NOT NULL,
                    `status` enum('pending', 'approved', 'rejected') DEFAULT 'pending',
                    `reviewed_by` int,
                    `review_comment` text,
                    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    KEY `fk_proposal_department_idx` (`department_id`),
                    KEY `fk_proposal_access_idx` (`access_level`),
                    KEY `fk_proposal_tag_idx` (`tag_id`),
                    KEY `fk_proposal_user_idx` (`proposed_by`),
                    KEY `fk_proposal_reviewer_idx` (`reviewed_by`),
                    CONSTRAINT `fk_proposal_access` FOREIGN KEY (`access_level`) REFERENCES `access` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
                    CONSTRAINT `fk_proposal_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
                    CONSTRAINT `fk_proposal_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
                    CONSTRAINT `fk_proposal_user` FOREIGN KEY (`proposed_by`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
                    CONSTRAINT `fk_proposal_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
            """))
            print("   ✅ Создана таблица content_proposals")
            
            # 3. Добавляем поле для отслеживания создателя контента
            print("👤 Добавляем поле creator_id в таблицу content...")
            
            # Проверяем существование поля creator_id
            columns = [col['name'] for col in inspector.get_columns('content')]
            if 'creator_id' not in columns:
                connection.execute(text("""
                    ALTER TABLE `content` 
                    ADD COLUMN `creator_id` int NULL,
                    ADD COLUMN `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                    ADD COLUMN `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    ADD KEY `fk_content_creator_idx` (`creator_id`),
                    ADD CONSTRAINT `fk_content_creator` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
                """))
                print("   ✅ Добавлено поле creator_id в таблицу content")
            
            # 4. Добавляем поле для отслеживания статуса контента
            if 'status' not in columns:
                connection.execute(text("""
                    ALTER TABLE `content` 
                    ADD COLUMN `status` enum('active', 'inactive', 'archived') DEFAULT 'active'
                """))
                print("   ✅ Добавлено поле status в таблицу content")
            
            connection.commit()
            print("✅ Миграция системы ролей завершена успешно!")
            
        except Exception as e:
            connection.rollback()
            print(f"❌ Ошибка при выполнении миграции: {e}")
            raise

if __name__ == "__main__":
    run_migration()
