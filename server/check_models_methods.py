#!/usr/bin/env python3
"""
Скрипт для проверки методов в модуле models Yandex Cloud ML SDK
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from yandex_cloud_ml_sdk import AsyncYCloudML
    
    print("🔍 Проверка методов в модуле models...")
    
    # Создаем экземпляр
    client = AsyncYCloudML(folder_id="test", auth="test")
    
    print("📋 Методы в client.models:")
    if hasattr(client, 'models'):
        models_methods = [method for method in dir(client.models) if not method.startswith('_')]
        for method in sorted(models_methods):
            print(f"   - {method}")
        
        print(f"\n📊 Всего методов в models: {len(models_methods)}")
        
        # Проверяем конкретные методы
        print("\n🔍 Проверка конкретных методов в models:")
        print(f"   generate: {'✅' if hasattr(client.models, 'generate') else '❌'}")
        print(f"   generate_text: {'✅' if hasattr(client.models, 'generate_text') else '❌'}")
        print(f"   chat: {'✅' if hasattr(client.models, 'chat') else '❌'}")
        print(f"   complete: {'✅' if hasattr(client.models, 'complete') else '❌'}")
        print(f"   generate_content: {'✅' if hasattr(client.models, 'generate_content') else '❌'}")
        
    else:
        print("❌ Модуль models не найден")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}") 