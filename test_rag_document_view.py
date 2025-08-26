#!/usr/bin/env python3
"""
Тестовый скрипт для проверки RAG функционала с просмотром документа
"""

import requests
import json

# Настройки
BASE_URL = "http://localhost:8000"
LOGIN = "Pavel2"
PASSWORD = "123123"

def test_rag_with_document_view():
    """Тестирует RAG запрос с возможностью просмотра документа"""
    print("🔍 Тестирование RAG с просмотром документа...")
    
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
            
            # 2. Получаем информацию о пользователе
            user_response = requests.get(f"{BASE_URL}/user/me", headers=headers)
            if user_response.status_code == 200:
                user_info = user_response.json()
                department_id = user_info.get('department_id')
                print(f"✅ Пользователь: {user_info.get('login')}, Отдел: {department_id}")
                
                # 3. Выполняем RAG запрос
                rag_data = {
                    "department_id": department_id,
                    "question": "Как загрузить документ в систему?"
                }
                
                print(f"🔍 RAG запрос: '{rag_data['question']}'")
                rag_response = requests.post(f"{BASE_URL}/api/yandex-rag/query", json=rag_data, headers=headers)
                print(f"Статус RAG запроса: {rag_response.status_code}")
                
                if rag_response.status_code == 200:
                    rag_result = rag_response.json()
                    print("✅ RAG ответ получен!")
                    print(f"   Ответ: {rag_result.get('answer', '')[:200]}...")
                    print(f"   Источников: {len(rag_result.get('sources', []))}")
                    
                    # 4. Проверяем источники
                    sources = rag_result.get('sources', [])
                    if sources:
                        print("\n📚 Источники:")
                        for i, source in enumerate(sources):
                            print(f"   {i+1}. {source.get('file_name', 'Без названия')}")
                            print(f"      ID документа: {source.get('content_id', 'Не указан')}")
                            print(f"      Релевантность: {source.get('similarity_score', 0)}")
                            print(f"      Отрывок: {source.get('chunk_content', '')[:100]}...")
                            
                            # 5. Тестируем просмотр документа
                            document_id = source.get('content_id')
                            if document_id:
                                print(f"   🔗 Тестируем просмотр документа ID: {document_id}")
                                
                                # Тестируем просмотр с выделением
                                viewer_url = f"{BASE_URL}/content/document-viewer-with-highlight/{document_id}"
                                viewer_response = requests.get(viewer_url, headers=headers)
                                print(f"      Статус просмотра с выделением: {viewer_response.status_code}")
                                
                                if viewer_response.status_code == 200:
                                    print("      ✅ Просмотр с выделением работает!")
                                else:
                                    print(f"      ❌ Ошибка просмотра с выделением: {viewer_response.text}")
                                
                                # Тестируем обычный просмотр
                                normal_viewer_url = f"{BASE_URL}/content/document-viewer/{document_id}"
                                normal_response = requests.get(normal_viewer_url, headers=headers)
                                print(f"      Статус обычного просмотра: {normal_response.status_code}")
                                
                                if normal_response.status_code == 200:
                                    print("      ✅ Обычный просмотр работает!")
                                else:
                                    print(f"      ❌ Ошибка обычного просмотра: {normal_response.text}")
                                
                                break  # Тестируем только первый источник
                    else:
                        print("⚠️ Источники не найдены")
                        
                else:
                    print(f"❌ Ошибка RAG запроса: {rag_response.text}")
            else:
                print(f"❌ Ошибка получения информации о пользователе: {user_response.text}")
                
        else:
            print(f"❌ Ошибка входа: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск теста RAG с просмотром документа...")
    print(f"URL: {BASE_URL}")
    print(f"Логин: {LOGIN}")
    print(f"Пароль: {PASSWORD}")
    print("-" * 50)
    
    test_rag_with_document_view()
    
    print("\n✅ Тестирование завершено!")
