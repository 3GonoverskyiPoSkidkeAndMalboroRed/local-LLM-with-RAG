#!/usr/bin/env python3
"""
Тест загрузки документов
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_document_loading():
    """Тестирование загрузки документов"""
    print("🔍 Тестирование загрузки документов...")
    
    try:
        from document_loader import load_documents
        
        path = "files/ContentForDepartment/5"
        
        print(f"📁 Загружаем документы из: {path}")
        
        documents = load_documents(path)
        
        print(f"📄 Загружено документов: {len(documents)}")
        
        for i, doc in enumerate(documents):
            print(f"\n📝 Документ {i+1}:")
            print(f"  Источник: {doc.metadata.get('source', 'unknown')}")
            print(f"  Длина текста: {len(doc.page_content)}")
            print(f"  Начало текста: {doc.page_content[:100]}...")
            
            # Проверяем, что текст не пустой
            if not doc.page_content.strip():
                print("  ⚠️ Текст пустой!")
            else:
                print("  ✅ Текст не пустой")
        
        return len(documents) > 0
        
    except Exception as e:
        print(f"❌ Ошибка загрузки документов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_loader_direct():
    """Прямое тестирование TextLoader"""
    print("\n🔍 Прямое тестирование TextLoader...")
    
    try:
        from langchain_community.document_loaders import TextLoader
        
        file_path = "files/ContentForDepartment/5/test_document.txt"
        
        print(f"📄 Загружаем файл: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            print(f"❌ Файл не существует: {file_path}")
            return False
        
        # Читаем файл напрямую
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📝 Содержимое файла (первые 100 символов): {content[:100]}...")
            print(f"📏 Длина файла: {len(content)} символов")
        
        # Используем TextLoader
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        
        print(f"📄 TextLoader загрузил документов: {len(documents)}")
        
        for i, doc in enumerate(documents):
            print(f"  Документ {i+1}:")
            print(f"    Источник: {doc.metadata.get('source', 'unknown')}")
            print(f"    Длина текста: {len(doc.page_content)}")
            print(f"    Начало: {doc.page_content[:50]}...")
        
        return len(documents) > 0
        
    except Exception as e:
        print(f"❌ Ошибка TextLoader: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск тестирования загрузки документов...")
    
    tests = [
        ("Загрузка документов", test_document_loading),
        ("TextLoader", test_text_loader_direct),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Выводим результаты
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("="*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\nВсего тестов: {len(results)}")
    print(f"Успешно: {success_count}")
    print(f"Провалено: {len(results) - success_count}")
    
    if success_count == len(results):
        print("\n🎉 Все тесты пройдены! Документы загружаются корректно.")
        return True
    else:
        print(f"\n⚠️ {len(results) - success_count} тестов провалено.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 