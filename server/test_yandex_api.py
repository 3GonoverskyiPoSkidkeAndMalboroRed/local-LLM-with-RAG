#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Yandex Cloud API
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yandex_ai_service import YandexAIService

async def test_yandex_api():
    """Тестирование Yandex Cloud API"""
    print("🧪 Тестирование Yandex Cloud API...")
    
    # Создаем экземпляр сервиса
    service = YandexAIService()
    
    print(f"📋 Конфигурация:")
    print(f"   API Key: {'✅ Установлен' if service.api_key else '❌ Не установлен'}")
    print(f"   Folder ID: {'✅ Установлен' if service.folder_id else '❌ Не установлен'}")
    
    if not service.api_key:
        print("❌ API ключ не установлен!")
        return False
    
    if not service.folder_id:
        print("❌ Folder ID не установлен!")
        return False
    
    # Тестовый запрос
    print("\n🚀 Отправка тестового запроса...")
    
    test_prompt = "Привет"
    test_model = "yandexgpt-lite"
    test_max_tokens = 1000
    test_temperature = 0.6
    
    print(f"📝 Запрос:")
    print(f"   Prompt: {test_prompt}")
    print(f"   Model: {test_model}")
    print(f"   Max tokens: {test_max_tokens}")
    print(f"   Temperature: {test_temperature}")
    
    try:
        result = await service.generate_text(
            prompt=test_prompt,
            model=test_model,
            max_tokens=test_max_tokens,
            temperature=test_temperature
        )
        
        print(f"\n📊 Результат:")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"   Text: {result.get('text', 'N/A')}")
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   SDK Used: {result.get('sdk_used', 'N/A')}")
            print(f"   SDK Type: {result.get('sdk_type', 'N/A')}")
            
            if result.get('usage'):
                print(f"   Usage: {result.get('usage')}")
            
            print("\n✅ Тест прошел успешно!")
            return True
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print("\n❌ Тест не прошел!")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Запуск теста Yandex Cloud API...")
    success = asyncio.run(test_yandex_api())
    
    if success:
        print("\n🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n💥 Тесты не прошли!")
        sys.exit(1) 