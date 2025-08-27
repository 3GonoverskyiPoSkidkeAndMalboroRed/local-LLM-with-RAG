#!/usr/bin/env python3
"""
Тестовый скрипт для проверки прав пользователя "Ответственный отдела"
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_responsible_user():
    """Тестирование пользователя с ролью 'Ответственный отдела'"""
    print("🚀 Тестирование пользователя 'Ответственный отдела'...")
    
    # Вход как ответственный отдела
    login_data = {
        "login": "resp_it",
        "password": "resp123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Вход успешен!")
            print(f"   Пользователь: {data['user']['login']}")
            print(f"   Роль ID: {data['user']['role_id']}")
            token = data['access_token']
        else:
            print(f"❌ Ошибка входа: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Проверяем разрешения
    print("\n🔑 Проверка разрешений...")
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
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тестируем создание предложения контента
    print("\n📋 Тестирование создания предложения контента...")
    proposal_data = {
        "title": "Тестовый документ",
        "description": "Описание тестового документа",
        "access_level": 1,
        "department_id": 1,
        "tag_id": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/proposals/", json=proposal_data, headers=headers)
        if response.status_code == 201:
            data = response.json()
            print("✅ Предложение создано успешно!")
            print(f"   ID предложения: {data['id']}")
            print(f"   Статус: {data['status']}")
            proposal_id = data['id']
        else:
            print(f"❌ Ошибка создания предложения: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Проверяем список предложений
    print("\n📋 Проверка списка предложений...")
    try:
        response = requests.get(f"{BASE_URL}/proposals/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Список предложений получен! Количество: {len(data)}")
            for proposal in data:
                print(f"   - {proposal['title']} (статус: {proposal['status']})")
        else:
            print(f"❌ Ошибка получения предложений: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тестируем попытку доступа к управлению пользователями (должно быть запрещено)
    print("\n👥 Тестирование доступа к управлению пользователями...")
    try:
        response = requests.get(f"{BASE_URL}/user/users", headers=headers)
        if response.status_code == 403:
            print("✅ Доступ к управлению пользователями правильно запрещен!")
        else:
            print(f"❌ Неожиданный ответ: {response.status_code}")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    test_responsible_user()
