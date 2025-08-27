#!/usr/bin/env python3
"""
Скрипт для исправления AUTO_INCREMENT в таблицах
"""

from database import get_db
from sqlalchemy import text

def fix_auto_increment():
    """Исправляет AUTO_INCREMENT в таблицах"""
    print("🔧 Исправляем AUTO_INCREMENT в таблицах...")
    
    db = next(get_db())
    
    try:
        # Список таблиц для исправления
        tables = [
            "department",
            "access", 
            "tags",
            "role"
        ]
        
        for table in tables:
            print(f"📋 Исправляем таблицу {table}...")
            
            # Проверяем текущую структуру
            result = db.execute(text(f"DESCRIBE {table}"))
            columns = result.fetchall()
            
            id_column = None
            for col in columns:
                if col[0] == 'id':
                    id_column = col
                    break
            
            if id_column and 'auto_increment' not in str(id_column).lower():
                print(f"   🔄 Добавляем AUTO_INCREMENT для {table}.id...")
                
                # Временно отключаем проверку внешних ключей
                db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                
                # Добавляем AUTO_INCREMENT
                db.execute(text(f"ALTER TABLE {table} MODIFY id INT AUTO_INCREMENT"))
                
                # Включаем проверку внешних ключей
                db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                
                print(f"   ✅ AUTO_INCREMENT добавлен для {table}")
            else:
                print(f"   ✅ {table} уже имеет AUTO_INCREMENT")
        
        db.commit()
        print("✅ Все таблицы исправлены!")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_auto_increment()
