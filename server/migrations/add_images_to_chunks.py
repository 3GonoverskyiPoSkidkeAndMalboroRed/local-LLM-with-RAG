"""
Миграция для добавления колонки images в таблицу document_chunks
"""

from sqlalchemy import create_engine, text
import os

def run_migration():
    """Выполняет миграцию для добавления колонки images"""
    
    # Настройки подключения к базе данных
    DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+mysqlconnector://root:123123@localhost:3306/db_main")
    
    engine = create_engine(DATABASE_URL)
    
    # SQL для добавления колонки images
    add_images_column = """
    ALTER TABLE document_chunks 
    ADD COLUMN images JSON NULL 
    AFTER embedding_vector;
    """
    
    try:
        with engine.connect() as connection:
            # Проверяем, существует ли уже колонка images
            check_column = """
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'db_main' 
            AND TABLE_NAME = 'document_chunks' 
            AND COLUMN_NAME = 'images';
            """
            
            result = connection.execute(text(check_column))
            column_exists = result.fetchone()[0] > 0
            
            if not column_exists:
                # Добавляем колонку images
                connection.execute(text(add_images_column))
                connection.commit()
                print("✅ Колонка images успешно добавлена в таблицу document_chunks!")
            else:
                print("ℹ️ Колонка images уже существует в таблице document_chunks")
            
    except Exception as e:
        print(f"❌ Ошибка при добавлении колонки images: {e}")
        raise

if __name__ == "__main__":
    run_migration()
