#!/usr/bin/env python3
"""
Скрипт для проверки доступных методов в Yandex Cloud ML SDK
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from yandex_cloud_ml_sdk import AsyncYCloudML
    
    print("🔍 Проверка методов AsyncYCloudML...")
    
    # Создаем экземпляр (без инициализации)
    client = AsyncYCloudML(folder_id="test", auth="test")
    
    print("📋 Доступные методы:")
    methods = [method for method in dir(client) if not method.startswith('_')]
    for method in sorted(methods):
        print(f"   - {method}")
    
    print(f"\n📊 Всего методов: {len(methods)}")
    
    # Проверяем конкретные методы
    print("\n🔍 Проверка конкретных методов:")
    print(f"   generate: {'✅' if hasattr(client, 'generate') else '❌'}")
    print(f"   generate_text: {'✅' if hasattr(client, 'generate_text') else '❌'}")
    print(f"   chat: {'✅' if hasattr(client, 'chat') else '❌'}")
    print(f"   complete: {'✅' if hasattr(client, 'complete') else '❌'}")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}") 