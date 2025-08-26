#!/usr/bin/env python3
"""
Тестовый скрипт для проверки аутентификации пользователя Pavel2
"""

import requests
import json

# Настройки
BASE_URL = "http://localhost:8000"
LOGIN = "Pavel2"
PASSWORD = "123123"

def test_auth():
    """Тестирует аутентификацию пользователя"""
    print("🔐 Тестирование аутентификации...")
    
    # 1. Попытка входа
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
            
            # 2. Тестируем доступ к контенту
            headers = {"Authorization": f"Bearer {token}"}
            
            # Получаем информацию о пользователе
            user_response = requests.get(f"{BASE_URL}/user/me", headers=headers)
            print(f"Статус получения информации о пользователе: {user_response.status_code}")
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                print(f"✅ Информация о пользователе получена:")
                print(f"   ID: {user_info.get('id')}")
                print(f"   Логин: {user_info.get('login')}")
                print(f"   Роль: {user_info.get('role_id')}")
                print(f"   Отдел: {user_info.get('department_id')}")
                print(f"   Уровень доступа: {user_info.get('access_id')}")
                
                # 3. Тестируем доступ к контенту
                content_response = requests.get(f"{BASE_URL}/user/{user_info['id']}/content/by-tags", headers=headers)
                print(f"Статус получения контента: {content_response.status_code}")
                
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    print(f"✅ Контент получен:")
                    print(f"   Тегов: {len(content_data.get('tags', []))}")
                    print(f"   Без категории: {len(content_data.get('untagged_content', []))}")
                    
                    # 4. Тестируем просмотр документа (если есть)
                    if content_data.get('untagged_content'):
                        first_doc = content_data['untagged_content'][0]
                        doc_id = first_doc.get('id')
                        print(f"Тестируем просмотр документа ID: {doc_id}")
                        
                        viewer_response = requests.get(f"{BASE_URL}/content/document-viewer/{doc_id}", headers=headers)
                        print(f"Статус просмотра документа: {viewer_response.status_code}")
                        
                        if viewer_response.status_code == 200:
                            print("✅ Просмотр документа работает!")
                        else:
                            print(f"❌ Ошибка просмотра документа: {viewer_response.text}")
                    
                else:
                    print(f"❌ Ошибка получения контента: {content_response.text}")
            else:
                print(f"❌ Ошибка получения информации о пользователе: {user_response.text}")
                
        else:
            print(f"❌ Ошибка входа: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

def test_direct_content_access():
    """Тестирует прямой доступ к контенту без аутентификации"""
    print("\n🔓 Тестирование прямого доступа к контенту...")
    
    try:
        # Пытаемся получить контент без токена
        response = requests.get(f"{BASE_URL}/content/document-viewer/1")
        print(f"Статус прямого доступа: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Правильно - требуется аутентификация")
        else:
            print(f"⚠️ Неожиданный статус: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск тестов аутентификации...")
    print(f"URL: {BASE_URL}")
    print(f"Логин: {LOGIN}")
    print(f"Пароль: {PASSWORD}")
    print("-" * 50)
    
    test_auth()
    test_direct_content_access()
    
    print("\n✅ Тестирование завершено!")
