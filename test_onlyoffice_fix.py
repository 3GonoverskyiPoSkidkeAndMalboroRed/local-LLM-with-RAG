#!/usr/bin/env python3
"""
Тест для проверки исправления OnlyOffice
"""

import requests
import time

def test_onlyoffice_access():
    """Тестирует доступность OnlyOffice"""
    print("🔍 Тестирование OnlyOffice...")
    
    # Тест 1: Проверка OnlyOffice сервиса
    try:
        response = requests.get("http://localhost:8082/healthcheck", timeout=10)
        if response.status_code == 200:
            print("✅ OnlyOffice Document Server доступен")
        else:
            print(f"❌ OnlyOffice недоступен. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к OnlyOffice: {e}")
        return False
    
    # Тест 2: Проверка JavaScript API
    try:
        response = requests.get("http://localhost:8082/web-apps/apps/api/documents/api.js", timeout=10)
        if response.status_code == 200:
            print("✅ OnlyOffice JavaScript API доступен")
        else:
            print(f"❌ OnlyOffice JavaScript API недоступен. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к OnlyOffice JavaScript API: {e}")
        return False
    
    # Тест 3: Проверка Backend
    try:
        response = requests.get("http://localhost:8000/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Backend API доступен")
        else:
            print(f"❌ Backend недоступен. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Backend: {e}")
        return False
    
    # Тест 4: Проверка Nginx
    try:
        response = requests.get("http://localhost:8081/", timeout=10)
        if response.status_code == 200:
            print("✅ Nginx прокси доступен")
        else:
            print(f"❌ Nginx недоступен. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Nginx: {e}")
        return False
    
    print("\n🎉 Все сервисы работают корректно!")
    print("\n📝 Теперь попробуйте:")
    print("   1. Откройте http://localhost:8083 в браузере")
    print("   2. Войдите в систему")
    print("   3. Найдите документ с ID 50 (или любой другой)")
    print("   4. Нажмите кнопку 'Просмотр' для открытия в OnlyOffice")
    print("   5. Проверьте, что документ загружается без ошибок")
    
    return True

if __name__ == "__main__":
    test_onlyoffice_access() 