"""
Тестирование Rate Limiting
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_rate_limiting():
    """
    Тестирует различные сценарии rate limiting
    """
    print("🧪 Тестирование Rate Limiting")
    print("=" * 50)
    
    # Тест 1: Проверка статуса rate limiting
    print("\n1. Проверка статуса rate limiting:")
    try:
        response = requests.get(f"{BASE_URL}/rate-limit-status")
        if response.status_code == 200:
            print("✅ Статус rate limiting получен успешно")
            print(f"   IP: {response.json().get('client_ip')}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тест 2: Тест логина (должен быть ограничен 10 запросами в минуту)
    print("\n2. Тест rate limiting для логина:")
    login_data = {"login": "test", "password": "test"}
    
    for i in range(12):  # Пытаемся сделать 12 запросов (больше лимита)
        try:
            response = requests.post(f"{BASE_URL}/user/login", json=login_data)
            if response.status_code == 429:
                print(f"✅ Rate limit сработал на запросе {i+1}: {response.json()}")
                break
            elif response.status_code == 401:
                print(f"   Запрос {i+1}: Неверные учетные данные (ожидаемо)")
            else:
                print(f"   Запрос {i+1}: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка на запросе {i+1}: {e}")
            break
    
    # Тест 3: Тест регистрации (должен быть ограничен 5 запросами в минуту)
    print("\n3. Тест rate limiting для регистрации:")
    register_data = {
        "login": "testuser",
        "password": "testpass",
        "role_id": 2,
        "department_id": 1,
        "access_id": 1,
        "full_name": "Test User"
    }
    
    for i in range(7):  # Пытаемся сделать 7 запросов (больше лимита)
        try:
            response = requests.post(f"{BASE_URL}/user/register", json=register_data)
            if response.status_code == 429:
                print(f"✅ Rate limit сработал на запросе {i+1}: {response.json()}")
                break
            elif response.status_code == 400:
                print(f"   Запрос {i+1}: Пользователь уже существует (ожидаемо)")
            else:
                print(f"   Запрос {i+1}: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка на запросе {i+1}: {e}")
            break
    
    # Тест 4: Тест глобального rate limiting
    print("\n4. Тест глобального rate limiting:")
    for i in range(105):  # Пытаемся сделать 105 запросов (больше глобального лимита)
        try:
            response = requests.get(f"{BASE_URL}/check_db_connection")
            if response.status_code == 429:
                print(f"✅ Глобальный rate limit сработал на запросе {i+1}: {response.json()}")
                break
            elif response.status_code == 200:
                print(f"   Запрос {i+1}: OK")
            else:
                print(f"   Запрос {i+1}: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка на запросе {i+1}: {e}")
            break
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")

def test_rate_limit_headers():
    """
    Тестирует заголовки rate limiting
    """
    print("\n📋 Проверка заголовков rate limiting:")
    
    try:
        response = requests.get(f"{BASE_URL}/rate-limit-status")
        
        # Проверяем наличие заголовков rate limiting
        headers = response.headers
        rate_limit_headers = [
            'X-RateLimit-Limit',
            'X-RateLimit-Remaining', 
            'X-RateLimit-Reset'
        ]
        
        for header in rate_limit_headers:
            if header in headers:
                print(f"✅ {header}: {headers[header]}")
            else:
                print(f"⚠️  {header}: отсутствует")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_rate_limiting()
    test_rate_limit_headers()

