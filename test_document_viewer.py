#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала просмотра документа
"""

import requests
import json

# Настройки
BASE_URL = "http://localhost:8000"
LOGIN = "Pavel2"
PASSWORD = "123123"

def test_document_viewer():
    """Тестирует функционал просмотра документа"""
    print("📄 Тестирование просмотра документа...")
    
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
            
            # 2. Получаем список документов
            print("📋 Получение списка документов...")
            content_response = requests.get(f"{BASE_URL}/user/2/content/by-tags", headers=headers)
            print(f"Статус получения контента: {content_response.status_code}")
            
            if content_response.status_code == 200:
                content_data = content_response.json()
                print("✅ Контент получен!")
                
                # Ищем документы
                all_documents = []
                
                # Документы без категории
                if content_data.get('untagged_content'):
                    all_documents.extend(content_data['untagged_content'])
                
                # Документы по тегам
                if content_data.get('tags'):
                    for tag in content_data['tags']:
                        if tag.get('content'):
                            all_documents.extend(tag['content'])
                
                print(f"📄 Найдено документов: {len(all_documents)}")
                
                if all_documents:
                    # Берем первый документ для тестирования
                    test_doc = all_documents[0]
                    doc_id = test_doc.get('id')
                    doc_title = test_doc.get('title', 'Без названия')
                    doc_path = test_doc.get('file_path', '')
                    
                    print(f"\n🔍 Тестируем документ:")
                    print(f"   ID: {doc_id}")
                    print(f"   Название: {doc_title}")
                    print(f"   Путь: {doc_path}")
                    
                    if doc_id:
                        # 3. Тестируем обычный просмотр документа
                        print(f"\n📖 Тестирование обычного просмотра документа...")
                        normal_viewer_url = f"{BASE_URL}/content/document-viewer/{doc_id}"
                        normal_response = requests.get(normal_viewer_url, headers=headers)
                        print(f"Статус обычного просмотра: {normal_response.status_code}")
                        
                        if normal_response.status_code == 200:
                            print("✅ Обычный просмотр работает!")
                            print(f"   Размер ответа: {len(normal_response.text)} символов")
                        else:
                            print(f"❌ Ошибка обычного просмотра: {normal_response.text}")
                        
                        # 4. Тестируем просмотр с выделением
                        print(f"\n🔍 Тестирование просмотра с выделением...")
                        highlight_viewer_url = f"{BASE_URL}/content/document-viewer-with-highlight/{doc_id}"
                        highlight_response = requests.get(highlight_viewer_url, headers=headers)
                        print(f"Статус просмотра с выделением: {highlight_response.status_code}")
                        
                        if highlight_response.status_code == 200:
                            print("✅ Просмотр с выделением работает!")
                            print(f"   Размер ответа: {len(highlight_response.text)} символов")
                        else:
                            print(f"❌ Ошибка просмотра с выделением: {highlight_response.text}")
                        
                        # 5. Тестируем просмотр с поисковым запросом
                        print(f"\n🔍 Тестирование просмотра с поисковым запросом...")
                        search_query = "документ"
                        search_viewer_url = f"{BASE_URL}/content/document-viewer-with-highlight/{doc_id}?search_query={search_query}"
                        search_response = requests.get(search_viewer_url, headers=headers)
                        print(f"Статус просмотра с поиском: {search_response.status_code}")
                        
                        if search_response.status_code == 200:
                            print("✅ Просмотр с поиском работает!")
                            print(f"   Размер ответа: {len(search_response.text)} символов")
                            
                            # Проверяем, есть ли выделение в ответе
                            if '<mark>' in search_response.text:
                                print("✅ Выделение найдено в ответе!")
                            else:
                                print("⚠️ Выделение не найдено в ответе")
                        else:
                            print(f"❌ Ошибка просмотра с поиском: {search_response.text}")
                        
                    else:
                        print("❌ ID документа не найден")
                else:
                    print("⚠️ Документы не найдены")
                    
            else:
                print(f"❌ Ошибка получения контента: {content_response.text}")
                
        else:
            print(f"❌ Ошибка входа: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск теста просмотра документа...")
    print(f"URL: {BASE_URL}")
    print(f"Логин: {LOGIN}")
    print(f"Пароль: {PASSWORD}")
    print("-" * 50)
    
    test_document_viewer()
    
    print("\n✅ Тестирование завершено!")
