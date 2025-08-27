#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой системы ролей
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Тестирование входа в систему"""
    print("🔐 Тестирование входа в систему...")
    
    login_data = {
        "login": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Вход успешен!")
            print(f"   Пользователь: {data['user']['login']}")
            print(f"   Роль ID: {data['user']['role_id']}")
            return data['access_token']
        else:
            print(f"❌ Ошибка входа: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def test_user_info(token):
    """Тестирование получения информации о пользователе"""
    print("\n👤 Тестирование получения информации о пользователе...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Информация о пользователе получена!")
            print(f"   Роль: {data.get('role_name', 'Неизвестно')}")
            print(f"   Разрешения: {json.dumps(data.get('permissions', {}), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка получения информации: {response.status_code}")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def test_permissions(token):
    """Тестирование получения разрешений"""
    print("\n🔑 Тестирование получения разрешений...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/permissions", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Разрешения получены!")
            print(f"   Роль: {data.get('role_name', 'Неизвестно')}")
            print(f"   Может управлять пользователями: {data.get('can_manage_users', False)}")
            print(f"   Может управлять контентом: {data.get('can_manage_content', False)}")
            print(f"   Может предлагать контент: {data.get('can_propose_content', False)}")
            print(f"   Может рассматривать предложения: {data.get('can_review_proposals', False)}")
        else:
            print(f"❌ Ошибка получения разрешений: {response.status_code}")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def test_proposals_api(token):
    """Тестирование API предложений"""
    print("\n📋 Тестирование API предложений...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Получение списка предложений
    try:
        response = requests.get(f"{BASE_URL}/proposals/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Список предложений получен! Количество: {len(data)}")
        else:
            print(f"❌ Ошибка получения предложений: {response.status_code}")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def test_users_api(token):
    """Тестирование API пользователей"""
    print("\n👥 Тестирование API пользователей...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Список пользователей получен! Количество: {len(data)}")
            for user in data:
                print(f"   - {user.get('login', 'Неизвестно')} ({user.get('role_name', 'Неизвестно')})")
        else:
            print(f"❌ Ошибка получения пользователей: {response.status_code}")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 Начинаем тестирование новой системы ролей...")
    
    # Тестируем вход
    token = test_login()
    if not token:
        print("❌ Не удалось получить токен. Тестирование прервано.")
        return
    
    # Тестируем получение информации о пользователе
    test_user_info(token)
    
    # Тестируем получение разрешений
    test_permissions(token)
    
    # Тестируем API предложений
    test_proposals_api(token)
    
    # Тестируем API пользователей
    test_users_api(token)
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    main()
