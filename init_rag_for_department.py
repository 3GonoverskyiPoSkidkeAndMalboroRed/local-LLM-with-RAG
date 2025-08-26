#!/usr/bin/env python3
"""
Скрипт для инициализации RAG системы для отдела
"""

import requests
import json

# Настройки
BASE_URL = "http://localhost:8000"
LOGIN = "Pavel2"
PASSWORD = "123123"
DEPARTMENT_ID = 5  # Общий отдел

def init_rag_for_department():
    """Инициализирует RAG систему для отдела"""
    print("🚀 Инициализация RAG системы для отдела...")
    
    # 1. Вход в систему
    login_data = {
        "login": LOGIN,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/login", json=login_data)
        print(f"Статус входа: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ Вход успешен! Токен получен: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Инициализируем RAG для отдела
            init_data = {
                "department_id": DEPARTMENT_ID,
                "force_reload": True
            }
            
            print(f"🔧 Инициализация RAG для отдела {DEPARTMENT_ID}...")
            init_response = requests.post(f"{BASE_URL}/api/yandex-rag/initialize", json=init_data, headers=headers)
            print(f"Статус инициализации: {init_response.status_code}")
            
            if init_response.status_code == 200:
                init_result = init_response.json()
                print("✅ RAG система инициализирована!")
                print(f"   Результат: {init_result}")
            else:
                print(f"❌ Ошибка инициализации: {init_response.text}")
                
            # 3. Проверяем статус RAG
            print(f"📊 Проверка статуса RAG для отдела {DEPARTMENT_ID}...")
            status_response = requests.get(f"{BASE_URL}/api/yandex-rag/status/{DEPARTMENT_ID}", headers=headers)
            print(f"Статус проверки: {status_response.status_code}")
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                print("✅ Статус RAG получен!")
                print(f"   Статус: {status_result}")
            else:
                print(f"❌ Ошибка получения статуса: {status_response.text}")
                
        else:
            print(f"❌ Ошибка входа: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск инициализации RAG...")
    print(f"URL: {BASE_URL}")
    print(f"Логин: {LOGIN}")
    print(f"Пароль: {PASSWORD}")
    print(f"Отдел: {DEPARTMENT_ID}")
    print("-" * 50)
    
    init_rag_for_department()
    
    print("\n✅ Инициализация завершена!")
