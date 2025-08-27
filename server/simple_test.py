#!/usr/bin/env python3
"""
Простой тест для проверки API предложений
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple():
    """Простой тест"""
    print("🔐 Тестирование входа...")
    
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
            token = data['access_token']
        else:
            print(f"❌ Ошибка входа: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Тестируем создание предложения
    print("\n📋 Тестирование создания предложения...")
    
    # Создаем тестовый файл
    test_file_content = b"This is a test document content for proposal testing."
    
    try:
        files = {
            'file': ('test_document.txt', test_file_content, 'text/plain')
        }
        data = {
            'title': 'Test Document',
            'description': 'Test Description',
            'access_level': 1,
            'department_id': 1
        }
        
        response = requests.post(f"{BASE_URL}/proposals/", files=files, data=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Предложение создано!")
        else:
            print("❌ Ошибка создания предложения")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_simple()
