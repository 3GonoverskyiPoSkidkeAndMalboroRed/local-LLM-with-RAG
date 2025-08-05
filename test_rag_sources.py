#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала отображения источников в RAG
"""

import requests
import json
import time
import sys

# Конфигурация
API_BASE_URL = "http://localhost:8000"
DEPARTMENT_ID = "5"  # Используем отдел 5 для тестирования

def test_rag_with_sources():
    """Тестирует RAG запрос с отображением источников"""
    
    print("🧪 Тестирование RAG с отображением источников")
    print("=" * 50)
    
    # Тестовый вопрос
    question = "Что такое искусственный интеллект?"
    
    print(f"📝 Вопрос: {question}")
    print(f"🏢 Отдел: {DEPARTMENT_ID}")
    
    try:
        # 1. Создаем задачу
        print("\n1️⃣ Создание задачи...")
        response = requests.post(
            f"{API_BASE_URL}/llm/query",
            json={
                "question": question,
                "department_id": DEPARTMENT_ID
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка создания задачи: {response.status_code}")
            print(response.text)
            return False
            
        task_data = response.json()
        task_id = task_data["task_id"]
        print(f"✅ Задача создана: {task_id}")
        
        # 2. Ожидаем завершения задачи
        print("\n2️⃣ Ожидание завершения задачи...")
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            response = requests.get(
                f"{API_BASE_URL}/llm/query/{task_id}",
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Ошибка получения статуса: {response.status_code}")
                continue
                
            result = response.json()
            status = result["status"]
            
            print(f"   Попытка {attempts}/{max_attempts}: {status}")
            
            if status == "completed":
                print("✅ Задача завершена успешно!")
                break
            elif status == "failed":
                print(f"❌ Задача завершена с ошибкой: {result.get('error', 'Неизвестная ошибка')}")
                return False
            elif status == "processing":
                print("   ⏳ Задача в обработке...")
            else:
                print(f"   ⏳ Статус: {status}")
            
            time.sleep(2)
        else:
            print("❌ Превышено время ожидания")
            return False
        
        # 3. Анализируем результат
        print("\n3️⃣ Анализ результата...")
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        chunks = result.get("chunks", [])
        files = result.get("files", [])
        
        print(f"📄 Ответ ({len(answer)} символов):")
        print(f"   {answer[:200]}...")
        
        print(f"\n📚 Источники:")
        print(f"   - Найдено источников: {len(sources)}")
        print(f"   - Фрагментов: {len(chunks)}")
        print(f"   - Файлов: {len(files)}")
        
        if sources:
            print("\n📋 Детали источников:")
            for i, source in enumerate(sources[:3]):  # Показываем первые 3
                print(f"   {i+1}. {source.get('file_name', 'Неизвестный файл')}")
                print(f"      Путь: {source.get('file_path', 'Неизвестно')}")
                print(f"      ID: {source.get('chunk_id', 'Неизвестно')}")
                if source.get('page_number'):
                    print(f"      Страница: {source['page_number']}")
                if source.get('similarity_score'):
                    print(f"      Релевантность: {source['similarity_score']:.3f}")
                print(f"      Содержание: {source.get('chunk_content', '')[:100]}...")
                print()
        
        # 4. Тестируем API для получения деталей источника
        if sources:
            print("4️⃣ Тестирование API деталей источника...")
            first_source = sources[0]
            chunk_id = first_source.get('chunk_id')
            
            if chunk_id:
                response = requests.get(
                    f"{API_BASE_URL}/llm/source/{task_id}/{chunk_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    source_details = response.json()
                    print(f"✅ Детали источника получены для {chunk_id}")
                    print(f"   Файл: {source_details.get('file_name')}")
                    print(f"   Содержание: {len(source_details.get('chunk_content', ''))} символов")
                else:
                    print(f"❌ Ошибка получения деталей источника: {response.status_code}")
        
        print("\n✅ Тест завершен успешно!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск тестирования RAG с источниками")
    print(f"🌐 API URL: {API_BASE_URL}")
    print()
    
    success = test_rag_with_sources()
    
    if success:
        print("\n🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n💥 Тесты завершились с ошибками!")
        sys.exit(1)

if __name__ == "__main__":
    main() 