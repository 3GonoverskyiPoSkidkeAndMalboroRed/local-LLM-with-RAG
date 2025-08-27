#!/usr/bin/env python3
"""
Полный тест системы ролей
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_login():
    """Тест авторизации админа"""
    print("🔐 Тестируем авторизацию админа...")
    
    login_data = {
        "login": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/user/login", json=login_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Авторизация админа успешна")
        return data.get('access_token')
    else:
        print(f"❌ Ошибка авторизации админа: {response.text}")
        return None

def test_responsible_login():
    """Тест авторизации ответственного"""
    print("\n🔐 Тестируем авторизацию ответственного...")
    
    login_data = {
        "login": "resp_it",
        "password": "resp123"
    }
    
    response = requests.post(f"{BASE_URL}/user/login", json=login_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Авторизация ответственного успешна")
        return data.get('access_token')
    else:
        print(f"❌ Ошибка авторизации ответственного: {response.text}")
        return None

def test_user_info(token, user_type):
    """Тест получения информации о пользователе"""
    print(f"\n👤 Тестируем получение информации о {user_type}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/me", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Информация получена")
        print(f"Пользователь: {data.get('full_name')}")
        print(f"Роль: {data.get('role_name')}")
        print(f"Отдел: {data.get('department_name')}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_permissions(token, user_type):
    """Тест получения разрешений"""
    print(f"\n🔑 Тестируем получение разрешений {user_type}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/permissions", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Разрешения получены")
        print(f"Ключевые разрешения:")
        for key, value in data.items():
            if value:  # Показываем только активные разрешения
                print(f"  - {key}: {value}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_users_list(token, user_type):
    """Тест получения списка пользователей"""
    print(f"\n👥 Тестируем получение списка пользователей ({user_type})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/users", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Список пользователей получен")
        print(f"Количество пользователей: {len(data)}")
        for user in data[:3]:  # Показываем первые 3
            print(f"  - {user.get('full_name')} ({user.get('role_name')})")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_create_proposal(token, user_type):
    """Тест создания предложения контента"""
    print(f"\n📝 Тестируем создание предложения контента ({user_type})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Создаем тестовый файл
    test_file_content = f"This is a test document content from {user_type}.".encode('utf-8')
    
    files = {
        'file': (f'test_document_{user_type}.txt', test_file_content, 'text/plain')
    }
    data = {
        'title': f'Тестовый документ от {user_type}',
        'description': f'Описание тестового документа от {user_type}',
        'access_level': 1,
        'department_id': 1
    }
    
    response = requests.post(f"{BASE_URL}/proposals/", files=files, data=data, headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Предложение создано")
        print(f"ID: {data.get('id')}")
        print(f"Название: {data.get('title')}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_proposals_list(token, user_type):
    """Тест получения списка предложений"""
    print(f"\n📋 Тестируем получение списка предложений ({user_type})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/proposals/", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Список предложений получен")
        print(f"Количество предложений: {len(data)}")
        if data:
            for proposal in data[:2]:  # Показываем первые 2
                print(f"  - {proposal.get('title')} (статус: {proposal.get('status')})")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_proposal_review(admin_token, proposal_id):
    """Тест рассмотрения предложения админом"""
    print(f"\n👨‍⚖️ Тестируем рассмотрение предложения админом...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    review_data = {
        "status": "approved",
        "review_comment": "Одобрено для тестирования"
    }
    
    response = requests.put(f"{BASE_URL}/proposals/{proposal_id}/review", json=review_data, headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Предложение рассмотрено")
        print(f"Статус: {data.get('status')}")
        print(f"Комментарий: {data.get('review_comment')}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def main():
    print("🚀 Начинаем полное тестирование системы ролей...")
    
    # Тест авторизации админа
    admin_token = test_admin_login()
    if not admin_token:
        print("❌ Не удалось получить токен админа. Прерываем тестирование.")
        return
    
    # Тест авторизации ответственного
    resp_token = test_responsible_login()
    if not resp_token:
        print("❌ Не удалось получить токен ответственного. Прерываем тестирование.")
        return
    
    # Тест информации о пользователях
    admin_info = test_user_info(admin_token, "админа")
    resp_info = test_user_info(resp_token, "ответственного")
    
    # Тест разрешений
    admin_permissions = test_permissions(admin_token, "админа")
    resp_permissions = test_permissions(resp_token, "ответственного")
    
    # Тест списка пользователей
    admin_users = test_users_list(admin_token, "админа")
    resp_users = test_users_list(resp_token, "ответственного")
    
    # Тест создания предложений
    admin_proposal = test_create_proposal(admin_token, "админа")
    resp_proposal = test_create_proposal(resp_token, "ответственного")
    
    # Тест списка предложений
    admin_proposals = test_proposals_list(admin_token, "админа")
    resp_proposals = test_proposals_list(resp_token, "ответственного")
    
    # Тест рассмотрения предложения
    if resp_proposal:
        review_result = test_proposal_review(admin_token, resp_proposal.get('id'))
    
    print("\n✅ Полное тестирование завершено!")

if __name__ == "__main__":
    main()
