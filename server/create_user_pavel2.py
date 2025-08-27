#!/usr/bin/env python3
"""
Скрипт для создания пользователя Pavel2 с указанными параметрами
"""

import requests
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def create_user():
    """Создает пользователя Pavel2 с указанными параметрами"""
    
    # Параметры пользователя
    user_data = {
        "login": "Pavel2",
        "password": "123123",
        "role_id": 1,
        "department_id": 5,
        "access_id": 3,
        "full_name": "YGF"
    }
    
    # URL API (берем из переменных окружения или используем значение по умолчанию)
    api_url = os.getenv("API_URL", "http://localhost:8000")
    
    # Сначала нужно получить токен администратора для создания пользователя
    # Попробуем войти как администратор
    admin_login_data = {
        "login": "admin",
        "password": "admin123"
    }
    
    try:
        # Вход как администратор
        print("🔐 Вход как администратор...")
        login_response = requests.post(f"{api_url}/user/login", json=admin_login_data)
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                print("✅ Успешный вход как администратор")
                
                # Создаем пользователя
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                print("👤 Создание пользователя Pavel2...")
                create_response = requests.post(
                    f"{api_url}/user/register", 
                    json=user_data,
                    headers=headers
                )
                
                if create_response.status_code == 200:
                    print("✅ Пользователь Pavel2 успешно создан!")
                    print(f"📋 Детали: {create_response.json()}")
                else:
                    print(f"❌ Ошибка при создании пользователя: {create_response.status_code}")
                    print(f"📄 Ответ: {create_response.text}")
                    
            else:
                print("❌ Не удалось получить токен доступа")
        else:
            print(f"❌ Ошибка входа как администратор: {login_response.status_code}")
            print(f"📄 Ответ: {login_response.text}")
            
            # Попробуем создать пользователя без токена (если это разрешено)
            print("🔄 Попытка создания пользователя без токена...")
            create_response = requests.post(f"{api_url}/user/register", json=user_data)
            
            if create_response.status_code == 200:
                print("✅ Пользователь Pavel2 успешно создан!")
                print(f"📋 Детали: {create_response.json()}")
            else:
                print(f"❌ Ошибка при создании пользователя: {create_response.status_code}")
                print(f"📄 Ответ: {create_response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск создания пользователя Pavel2...")
    create_user()
