#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции OnlyOffice
"""

import requests
import json
import os

# Настройки
BASE_URL = "http://localhost:8000"
ONLYOFFICE_URL = "http://localhost:8082"

def test_onlyoffice_connection():
    """Тестирует подключение к OnlyOffice Document Server"""
    try:
        response = requests.get(f"{ONLYOFFICE_URL}/healthcheck", timeout=10)
        if response.status_code == 200:
            print("✅ OnlyOffice Document Server доступен")
            return True
        else:
            print(f"❌ OnlyOffice недоступен. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к OnlyOffice: {e}")
        return False

def test_backend_connection():
    """Тестирует подключение к backend API"""
    try:
        response = requests.get(f"{BASE_URL}/check_db_connection", timeout=10)
        if response.status_code == 200:
            print("✅ Backend API доступен")
            return True
        else:
            print(f"❌ Backend недоступен. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Backend: {e}")
        return False

def test_onlyoffice_config_endpoint():
    """Тестирует endpoint для получения конфигурации OnlyOffice"""
    try:
        # Сначала получаем список контента
        response = requests.get(f"{BASE_URL}/content/all", timeout=10)
        if response.status_code == 200:
            contents = response.json()
            if contents:
                # Берем первый документ для тестирования
                content_id = contents[0]['id']
                
                # Тестируем endpoint конфигурации OnlyOffice
                config_response = requests.get(
                    f"{BASE_URL}/content/onlyoffice/{content_id}",
                    params={
                        "user_id": 1,
                        "user_name": "Test User",
                        "mode": "view"
                    },
                    timeout=10
                )
                
                if config_response.status_code == 200:
                    config = config_response.json()
                    print("✅ Endpoint конфигурации OnlyOffice работает")
                    print(f"   - Документ: {config['document_info']['title']}")
                    print(f"   - Тип файла: {config['config']['document']['fileType']}")
                    return True
                else:
                    print(f"❌ Ошибка получения конфигурации OnlyOffice: {config_response.status_code}")
                    print(f"   Ответ: {config_response.text}")
                    return False
            else:
                print("⚠️  Нет документов для тестирования")
                return False
        else:
            print(f"❌ Ошибка получения списка контента: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка тестирования endpoint конфигурации: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🔍 Тестирование интеграции OnlyOffice...")
    print("=" * 50)
    
    # Тест 1: Подключение к OnlyOffice
    onlyoffice_ok = test_onlyoffice_connection()
    
    # Тест 2: Подключение к Backend
    backend_ok = test_backend_connection()
    
    # Тест 3: Endpoint конфигурации OnlyOffice
    config_ok = False
    if backend_ok:
        config_ok = test_onlyoffice_config_endpoint()
    
    print("=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   OnlyOffice Document Server: {'✅' if onlyoffice_ok else '❌'}")
    print(f"   Backend API: {'✅' if backend_ok else '❌'}")
    print(f"   OnlyOffice Config Endpoint: {'✅' if config_ok else '❌'}")
    
    if all([onlyoffice_ok, backend_ok, config_ok]):
        print("\n🎉 Все тесты пройдены! OnlyOffice интеграция работает корректно.")
        print("\n📝 Следующие шаги:")
        print("   1. Откройте http://localhost:8080 в браузере")
        print("   2. Войдите в систему")
        print("   3. Загрузите Word документ")
        print("   4. Нажмите кнопку 'Просмотр' для открытия в OnlyOffice")
    else:
        print("\n⚠️  Некоторые тесты не пройдены. Проверьте:")
        print("   1. Запущены ли все сервисы: docker-compose up -d")
        print("   2. Доступны ли порты 8000 и 8082")
        print("   3. Правильно ли настроены переменные окружения")

if __name__ == "__main__":
    main() 