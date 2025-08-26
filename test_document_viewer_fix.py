#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправленного эндпоинта просмотра документов
"""

import requests
import json

# Настройки
BASE_URL = "http://localhost:8000"
LOGIN = "Pavel2"
PASSWORD = "123123"

def test_document_viewer_fix():
    """Тестирует исправленный эндпоинт просмотра документов"""
    print("🔧 Тестирование исправленного эндпоинта просмотра документов...")
    
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
            
            # 2. Получаем список контента пользователя
            headers = {"Authorization": f"Bearer {token}"}
            
            # Получаем информацию о пользователе
            user_response = requests.get(f"{BASE_URL}/user/me", headers=headers)
            print(f"Статус получения информации о пользователе: {user_response.status_code}")
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_id = user_data.get("id")
                print(f"✅ Информация о пользователе получена: ID={user_id}")
                
                # 3. Получаем контент пользователя
                content_response = requests.get(f"{BASE_URL}/content/user/{user_id}/content", headers=headers)
                print(f"Статус получения контента: {content_response.status_code}")
                
                if content_response.status_code == 200:
                    content_list = content_response.json()
                    print(f"✅ Контент получен: {len(content_list)} документов")
                    
                    if content_list:
                        # Берем первый документ для тестирования
                        test_doc = content_list[0]
                        doc_id = test_doc.get("id")
                        doc_title = test_doc.get("title")
                        print(f"📄 Тестируем документ: {doc_title} (ID: {doc_id})")
                        
                        # 4. Тестируем получение токена для просмотра
                        view_token_response = requests.get(f"{BASE_URL}/content/view-token/{doc_id}", headers=headers)
                        print(f"Статус получения токена просмотра: {view_token_response.status_code}")
                        
                        if view_token_response.status_code == 200:
                            token_data = view_token_response.json()
                            view_token = token_data.get("view_token")
                            print(f"✅ Токен просмотра получен: {view_token[:20]}...")
                            
                            # 5. Тестируем публичный эндпоинт просмотра
                            public_view_url = f"{BASE_URL}/content/public-view/{doc_id}?token={view_token}"
                            print(f"🔗 URL публичного просмотра: {public_view_url}")
                            
                            public_view_response = requests.get(public_view_url)
                            print(f"Статус публичного просмотра: {public_view_response.status_code}")
                            
                            if public_view_response.status_code == 200:
                                print("✅ Публичный просмотр работает!")
                                print(f"📄 Тип контента: {public_view_response.headers.get('content-type', 'unknown')}")
                                
                                # Проверяем, что это HTML
                                if 'text/html' in public_view_response.headers.get('content-type', ''):
                                    print("✅ Получен HTML для просмотра документа")
                                else:
                                    print("⚠️ Получен не HTML контент")
                            else:
                                print(f"❌ Ошибка публичного просмотра: {public_view_response.text}")
                        else:
                            print(f"❌ Ошибка получения токена просмотра: {view_token_response.text}")
                    else:
                        print("⚠️ Нет документов для тестирования")
                else:
                    print(f"❌ Ошибка получения контента: {content_response.text}")
            else:
                print(f"❌ Ошибка получения информации о пользователе: {user_response.text}")
        else:
            print(f"❌ Ошибка входа: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")

if __name__ == "__main__":
    test_document_viewer_fix()
