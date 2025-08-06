#!/usr/bin/env python3
"""
Отладочный скрипт для проверки инициализации Yandex Cloud ML SDK
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("🔍 Отладка Yandex Cloud ML SDK...")

# Проверяем переменные окружения
api_key = os.getenv('YANDEX_API_KEY') or os.getenv('YC_API_KEY')
folder_id = os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID')

print(f"API Key: {'✅ Установлен' if api_key else '❌ Не установлен'}")
print(f"Folder ID: {'✅ Установлен' if folder_id else '❌ Не установлен'}")

if api_key:
    print(f"API Key (первые 10 символов): {api_key[:10]}...")
if folder_id:
    print(f"Folder ID: {folder_id}")

# Проверяем все переменные окружения, связанные с Yandex
yandex_vars = [key for key in os.environ.keys() if 'YANDEX' in key.upper() or 'YC_' in key.upper()]
print(f"\nНайденные переменные Yandex: {yandex_vars}")

for var in yandex_vars:
    value = os.getenv(var)
    if value:
        if 'KEY' in var.upper():
            print(f"{var}: {value[:10]}...")
        else:
            print(f"{var}: {value}")

# Пробуем инициализировать SDK
if api_key and folder_id:
    try:
        from yandex_cloud_ml_sdk import AsyncYCloudML
        print("\n🔄 Пробуем инициализировать Yandex Cloud ML SDK...")
        
        ml_client = AsyncYCloudML(
            folder_id=folder_id,
            auth=api_key
        )
        
        print("✅ Yandex Cloud ML SDK успешно инициализирован!")
        print(f"Client: {ml_client}")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации Yandex Cloud ML SDK: {e}")
        print(f"Тип ошибки: {type(e)}")
else:
    print("\n❌ Недостаточно переменных окружения для инициализации SDK") 