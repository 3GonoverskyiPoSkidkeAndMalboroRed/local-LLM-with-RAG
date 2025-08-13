"""
Простой тест Rate Limiting
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_login_rate_limit():
    """
    Тестирует rate limiting для эндпоинта логина
    """
    print("🧪 Тест Rate Limiting для логина")
    print("=" * 40)
    
    login_data = {"login": "test", "password": "test"}
    
    for i in range(15):  # Пытаемся сделать 15 запросов (больше лимита в 10)
        try:
            response = requests.post(f"{BASE_URL}/user/login", json=login_data)
            print(f"Запрос {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print(f"✅ Rate limit сработал на запросе {i+1}")
                print(f"   Ответ: {response.json()}")
                break
            elif response.status_code == 401:
                print(f"   Неверные учетные данные (ожидаемо)")
            else:
                print(f"   Неожиданный статус: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Сервер не запущен. Запустите сервер командой: python -m uvicorn app:app --reload")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            break
    
    print("=" * 40)

def test_register_rate_limit():
    """
    Тестирует rate limiting для эндпоинта регистрации
    """
    print("\n🧪 Тест Rate Limiting для регистрации")
    print("=" * 40)
    
    register_data = {
        "login": "testuser",
        "password": "testpass",
        "role_id": 2,
        "department_id": 1,
        "access_id": 1,
        "full_name": "Test User"
    }
    
    for i in range(7):  # Пытаемся сделать 7 запросов (больше лимита в 5)
        try:
            response = requests.post(f"{BASE_URL}/user/register", json=register_data)
            print(f"Запрос {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print(f"✅ Rate limit сработал на запросе {i+1}")
                print(f"   Ответ: {response.json()}")
                break
            elif response.status_code == 400:
                print(f"   Пользователь уже существует (ожидаемо)")
            else:
                print(f"   Неожиданный статус: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Сервер не запущен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            break
    
    print("=" * 40)

if __name__ == "__main__":
    test_login_rate_limit()
    test_register_rate_limit()

