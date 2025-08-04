#!/usr/bin/env python3
"""
Скрипт для тестирования конфигурации Yandex Cloud
Используется для проверки правильности настройки переменных окружения
"""

import asyncio
import sys
import logging
from config_utils import validate_all_config, print_config_summary, check_env_completeness
from yandex_cloud_adapter import YandexCloudAdapter, YandexCloudConfig

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_yandex_cloud_connection():
    """Тест подключения к Yandex Cloud API"""
    try:
        print("\n🔍 Тестирование подключения к Yandex Cloud...")
        
        # Создаем конфигурацию
        config = YandexCloudConfig.from_env()
        print(f"✅ Конфигурация создана успешно")
        
        # Создаем адаптер
        async with YandexCloudAdapter(config) as adapter:
            print(f"✅ Адаптер инициализирован")
            
            # Тестируем простую генерацию текста
            print("🧪 Тестирование генерации текста...")
            try:
                response = await adapter.generate_text(
                    "Привет! Это тест подключения к YandexGPT.",
                    max_tokens=50
                )
                print(f"✅ Генерация текста работает!")
                print(f"📝 Ответ: {response[:100]}{'...' if len(response) > 100 else ''}")
            except Exception as e:
                print(f"❌ Ошибка генерации текста: {e}")
                return False
            
            # Тестируем создание эмбеддингов
            print("🧪 Тестирование создания эмбеддингов...")
            try:
                embeddings = await adapter.create_embeddings([
                    "Тестовый текст для эмбеддинга",
                    "Еще один тестовый текст"
                ])
                print(f"✅ Создание эмбеддингов работает!")
                print(f"📊 Создано {len(embeddings)} эмбеддингов, размерность: {len(embeddings[0]) if embeddings else 0}")
            except Exception as e:
                print(f"❌ Ошибка создания эмбеддингов: {e}")
                return False
            
            # Показываем метрики
            metrics = adapter.get_metrics()
            print(f"\n📈 Метрики:")
            print(f"   Всего запросов: {metrics['total_requests']}")
            print(f"   Успешных: {metrics['successful_requests']}")
            print(f"   Неуспешных: {metrics['failed_requests']}")
            print(f"   Использовано токенов: {metrics['total_tokens_used']}")
            print(f"   Среднее время ответа: {metrics['average_response_time']:.2f}с")
            
        print("✅ Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

async def main():
    """Главная функция"""
    print("🚀 Запуск тестирования конфигурации Yandex Cloud")
    print("="*60)
    
    try:
        # Проверяем конфигурацию
        print_config_summary()
        check_env_completeness()
        
        # Валидируем конфигурацию
        config = validate_all_config()
        
        # Если Yandex Cloud включен, тестируем подключение
        if config["yandex_cloud"].get("use_yandex_cloud"):
            success = await test_yandex_cloud_connection()
            if success:
                print("\n🎉 Конфигурация Yandex Cloud работает корректно!")
                return 0
            else:
                print("\n💥 Обнаружены проблемы с конфигурацией Yandex Cloud")
                return 1
        else:
            print("\n⚠️  Yandex Cloud отключен (USE_YANDEX_CLOUD=false)")
            print("Для тестирования установите USE_YANDEX_CLOUD=true")
            return 0
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)