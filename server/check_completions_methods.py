#!/usr/bin/env python3
"""
Скрипт для проверки методов в модуле completions Yandex Cloud ML SDK
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from yandex_cloud_ml_sdk import AsyncYCloudML
    
    print("🔍 Проверка методов в модуле completions...")
    
    # Создаем экземпляр
    client = AsyncYCloudML(folder_id="test", auth="test")
    
    print("📋 Методы в client.models.completions:")
    if hasattr(client, 'models') and hasattr(client.models, 'completions'):
        completions_methods = [method for method in dir(client.models.completions) if not method.startswith('_')]
        for method in sorted(completions_methods):
            print(f"   - {method}")
        
        print(f"\n📊 Всего методов в completions: {len(completions_methods)}")
        
        # Проверяем конкретные методы
        print("\n🔍 Проверка конкретных методов в completions:")
        print(f"   create: {'✅' if hasattr(client.models.completions, 'create') else '❌'}")
        print(f"   generate: {'✅' if hasattr(client.models.completions, 'generate') else '❌'}")
        print(f"   complete: {'✅' if hasattr(client.models.completions, 'complete') else '❌'}")
        
    else:
        print("❌ Модуль completions не найден")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}") 