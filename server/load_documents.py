#!/usr/bin/env python3
"""
Скрипт для загрузки документов в векторную базу данных
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_documents_for_department():
    """Загрузка документов для отдела"""
    print("🔍 Загрузка документов в векторную базу данных...")
    
    try:
        from document_loader import load_documents_into_database
        
        department_id = "5"
        documents_path = f"files/ContentForDepartment/{department_id}"
        
        print(f"📁 Путь к документам: {documents_path}")
        print(f"🏢 ID отдела: {department_id}")
        
        # Проверяем существование директории
        if not os.path.exists(documents_path):
            print(f"❌ Директория {documents_path} не существует!")
            return False
        
        # Проверяем наличие файлов
        files = os.listdir(documents_path)
        if not files:
            print(f"❌ В директории {documents_path} нет файлов!")
            return False
        
        print(f"📄 Найдено файлов: {len(files)}")
        for file in files:
            print(f"  - {file}")
        
        # Загружаем документы
        print("\n🔄 Загружаем документы в векторную базу...")
        vectorstore = load_documents_into_database(
            model_name="text-search-doc",
            documents_path=department_id,
            department_id=department_id,
            reload=True  # Принудительно перезагружаем
        )
        
        print("✅ Документы успешно загружены!")
        
        # Проверяем количество документов в базе
        try:
            all_docs = vectorstore.get()
            if all_docs and all_docs.get('documents'):
                print(f"📊 Документов в базе: {len(all_docs['documents'])}")
            else:
                print("📊 База данных пуста")
        except Exception as e:
            print(f"⚠️ Не удалось проверить количество документов: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки документов: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск загрузки документов...")
    
    success = load_documents_for_department()
    
    if success:
        print("\n🎉 Документы успешно загружены! Теперь можно тестировать RAG.")
    else:
        print("\n❌ Ошибка при загрузке документов.")
        sys.exit(1)

if __name__ == "__main__":
    main() 