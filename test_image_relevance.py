"""
Тестовый скрипт для проверки улучшенной функциональности работы с изображениями
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.yandex_rag_service import YandexRAGService
from server.utils.image_extractor import ImageExtractor

async def test_image_relevance():
    """Тестирует улучшенную функциональность работы с изображениями"""
    
    print("🧪 Тестирование улучшенной функциональности работы с изображениями")
    print("=" * 70)
    
    # Создаем экземпляр RAG сервиса
    rag_service = YandexRAGService()
    image_extractor = ImageExtractor()
    
    # Тестируем извлечение изображений из тестового документа
    test_file = "test_document_with_images.txt"
    
    if os.path.exists(test_file):
        print(f"📄 Тестируем извлечение изображений из файла: {test_file}")
        
        # Читаем содержимое файла
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Тестируем извлечение изображений
        images = image_extractor.extract_images_from_file(test_file, content)
        
        print(f"📊 Найдено изображений: {len(images)}")
        
        for i, image in enumerate(images):
            relevance = image.get('relevance_score', 0.0)
            context = image.get('context', 'Без контекста')
            print(f"  Изображение {i+1}:")
            print(f"    Релевантность: {relevance:.2f} ({relevance*100:.1f}%)")
            print(f"    Контекст: {context[:100]}...")
            print()
    
    # Тестируем RAG запрос с изображениями
    print("🔍 Тестируем RAG запрос с изображениями")
    
    # Создаем тестовый отдел (если нужно)
    department_id = 1
    
    try:
        # Инициализируем RAG систему
        print("📚 Инициализация RAG системы...")
        init_result = await rag_service.initialize_rag(department_id, force_reload=True)
        print(f"✅ Результат инициализации: {init_result}")
        
        # Тестируем запрос
        test_questions = [
            "Какие изображения есть в документах?",
            "Покажи диаграммы и графики",
            "Есть ли схемы в документах?",
            "Какие типы изображений поддерживаются?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Вопрос: {question}")
            print("-" * 50)
            
            try:
                result = await rag_service.query_rag(department_id, question)
                
                print(f"📝 Ответ: {result.get('answer', 'Нет ответа')[:200]}...")
                print(f"📊 Источников: {result.get('sources_count', 0)}")
                
                # Проверяем изображения в источниках
                sources = result.get('sources', [])
                total_images = 0
                
                for i, source in enumerate(sources):
                    images = source.get('images', [])
                    if images:
                        total_images += len(images)
                        print(f"  📷 Источник {i+1}: {len(images)} изображений")
                        
                        for j, img in enumerate(images):
                            relevance = img.get('relevance_score', 0.0)
                            context = img.get('context', 'Без контекста')
                            print(f"    Изображение {j+1}: релевантность {relevance:.2f}")
                
                print(f"📈 Всего изображений в ответе: {total_images}")
                
            except Exception as e:
                print(f"❌ Ошибка при запросе: {e}")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_image_relevance())
