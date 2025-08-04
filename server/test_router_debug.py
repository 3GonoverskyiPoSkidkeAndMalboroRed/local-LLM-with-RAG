#!/usr/bin/env python3
"""
Тест для отладки роутера yandex_routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_router_import():
    """Тест импорта роутера"""
    print("🔍 Тестирование импорта роутера...")
    
    try:
        from routes.yandex_routes import generate_text, YandexGenerateRequest
        print("✅ Импорт роутера успешен")
        
        # Создаем тестовый запрос
        request = YandexGenerateRequest(
            prompt="Тестовый запрос",
            model="yandexgpt",
            temperature=0.1,
            max_tokens=100
        )
        print(f"✅ Тестовый запрос создан: {request}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_creation():
    """Тест создания LLM"""
    print("\n🔍 Тестирование создания LLM...")
    
    try:
        from yandex_llm import create_yandex_llm
        
        llm = create_yandex_llm(
            model="yandexgpt",
            temperature=0.1,
            max_tokens=100
        )
        
        print(f"✅ LLM создан: {llm}")
        print(f"✅ model: {llm.model}")
        print(f"✅ temperature: {llm.temperature}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания LLM: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_router_import()
    test_llm_creation() 