"""
Миграция для создания таблиц RAG системы
"""

from sqlalchemy import create_engine, text
import os

def run_migration():
    """Выполняет миграцию для создания таблиц RAG системы"""
    
    # Настройки подключения к базе данных
    DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+mysqlconnector://root:123123@localhost:3307/db_main")
    
    engine = create_engine(DATABASE_URL)
    
    # SQL для создания таблиц
    create_document_chunks_table = """
    CREATE TABLE IF NOT EXISTS document_chunks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        content_id INT NOT NULL,
        department_id INT NOT NULL,
        chunk_text TEXT NOT NULL,
        chunk_index INT NOT NULL,
        embedding_vector JSON,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE,
        INDEX idx_content_id (content_id),
        INDEX idx_department_id (department_id)
    );
    """
    
    create_rag_sessions_table = """
    CREATE TABLE IF NOT EXISTS rag_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        department_id INT NOT NULL,
        is_initialized BOOLEAN DEFAULT FALSE,
        documents_count INT DEFAULT 0,
        chunks_count INT DEFAULT 0,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE,
        UNIQUE KEY unique_department (department_id)
    );
    """
    
    try:
        with engine.connect() as connection:
            # Создаем таблицы
            connection.execute(text(create_document_chunks_table))
            connection.execute(text(create_rag_sessions_table))
            connection.commit()
            
            print("✅ Таблицы RAG системы успешно созданы!")
            
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise

if __name__ == "__main__":
    run_migration()