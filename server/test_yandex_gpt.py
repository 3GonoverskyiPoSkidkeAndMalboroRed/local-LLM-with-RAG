#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Yandex GPT эндпоинтов
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Конфигурация
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/yandex"

def test_yandex_config():
    """Тест получения конфигурации Yandex Cloud"""
    print("🔧 Тестирование конфигурации Yandex Cloud...")
    
    try:
        response = requests.get(f"{API_BASE}/config")
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            config = response.json()
            print(f"Конфигурация: {json.dumps(config, indent=2, ensure_ascii=False)}")
            return config.get("is_configured", False)
        else:
            print(f"Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка при тестировании конфигурации: {e}")
        return False

def test_yandex_health():
    """Тест проверки здоровья Yandex Cloud API"""
    print("\n🏥 Тестирование здоровья Yandex Cloud API...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            health = response.json()
            print(f"Состояние: {json.dumps(health, indent=2, ensure_ascii=False)}")
            return health.get("status") == "healthy"
        else:
            print(f"Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка при тестировании здоровья: {e}")
        return False

def test_yandex_models():
    """Тест получения списка моделей"""
    print("\n🤖 Тестирование получения списка моделей...")
    
    try:
        response = requests.get(f"{API_BASE}/models")
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"Модели: {json.dumps(models, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка при получении моделей: {e}")
        return False

def test_yandex_generate():
    """Тест генерации текста"""
    print("\n📝 Тестирование генерации текста...")
    
    payload = {
        "prompt": "Расскажи кратко о преимуществах искусственного интеллекта",
        "model": "yandexgpt",
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Результат генерации:")
            print(f"Текст: {result.get('text', '')}")
            print(f"Модель: {result.get('model', '')}")
            print(f"Время ответа: {result.get('response_time', 0):.2f} сек")
            return True
        else:
            print(f"Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка при генерации текста: {e}")
        return False

def test_yandex_chat():
    """Тест чата"""
    print("\n💬 Тестирование чата...")
    
    payload = {
        "messages": [
            {"role": "system", "content": "Ты полезный ассистент."},
            {"role": "user", "content": "Привет! Как дела?"}
        ],
        "model": "yandexgpt",
        "temperature": 0.1,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Результат чата:")
            print(f"Сообщение: {result.get('message', '')}")
            print(f"Модель: {result.get('model', '')}")
            print(f"Время ответа: {result.get('response_time', 0):.2f} сек")
            return True
        else:
            print(f"Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка при чате: {e}")
        return False

def test_yandex_stream():
    """Тест потоковой генерации"""
    print("\n🌊 Тестирование потоковой генерации...")
    
    payload = {
        "prompt": "Напиши короткое стихотворение о программировании",
        "model": "yandexgpt",
        "temperature": 0.7,
        "max_tokens": 200,
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/generate/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            print("Потоковый ответ:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # Убираем 'data: '
                        if data == '[DONE]':
                            print("\n[Генерация завершена]")
                            break
                        elif data.startswith('error: '):
                            print(f"\nОшибка: {data[7:]}")
                            return False
                        else:
                            print(data, end='', flush=True)
            return True
        else:
            print(f"Ошибка: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка при потоковой генерации: {e}")
        return False

def check_environment_variables():
    """Проверка переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = ["YANDEX_API_KEY", "YANDEX_FOLDER_ID"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Скрываем значение для безопасности
            masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "***"
            print(f"✅ {var}: {masked_value}")
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {missing_vars}")
        print("Создайте файл .env в папке server/ с необходимыми переменными")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование Yandex GPT эндпоинтов")
    print("=" * 50)
    
    # Проверяем переменные окружения
    if not check_environment_variables():
        print("\n❌ Тестирование прервано из-за отсутствующих переменных окружения")
        return
    
    # Запускаем тесты
    tests = [
        ("Конфигурация", test_yandex_config),
        ("Здоровье API", test_yandex_health),
        ("Список моделей", test_yandex_models),
        ("Генерация текста", test_yandex_generate),
        ("Чат", test_yandex_chat),
        ("Потоковая генерация", test_yandex_stream)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 50)
    print("📊 Итоги тестирования:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте настройки и логи.")

if __name__ == "__main__":
    main() 