import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Тест авторизации админа"""
    print("🔐 Тестируем авторизацию админа...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/user/login", json=login_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Авторизация успешна")
        print(f"Токен: {data.get('access_token', 'Нет токена')[:50]}...")
        return data.get('access_token')
    else:
        print(f"❌ Ошибка авторизации: {response.text}")
        return None

def test_user_info(token):
    """Тест получения информации о пользователе"""
    print("\n👤 Тестируем получение информации о пользователе...")
    
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

def test_permissions(token):
    """Тест получения разрешений"""
    print("\n🔑 Тестируем получение разрешений...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/permissions", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Разрешения получены")
        print(f"Разрешения: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_users_list(token):
    """Тест получения списка пользователей"""
    print("\n👥 Тестируем получение списка пользователей...")
    
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

def test_create_proposal(token):
    """Тест создания предложения контента"""
    print("\n📝 Тестируем создание предложения контента...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    proposal_data = {
        "title": "Тестовый документ",
        "description": "Описание тестового документа",
        "access_level": 1,
        "department_id": 1,
        "tag_id": 1
    }
    
    response = requests.post(f"{BASE_URL}/proposals/", json=proposal_data, headers=headers)
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

def test_proposals_list(token):
    """Тест получения списка предложений"""
    print("\n📋 Тестируем получение списка предложений...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/proposals/", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Список предложений получен")
        print(f"Количество предложений: {len(data)}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def main():
    print("🚀 Начинаем тестирование системы ролей...")
    
    # Тест авторизации
    token = test_login()
    if not token:
        print("❌ Не удалось получить токен. Прерываем тестирование.")
        return
    
    # Тест информации о пользователе
    user_info = test_user_info(token)
    
    # Тест разрешений
    permissions = test_permissions(token)
    
    # Тест списка пользователей
    users = test_users_list(token)
    
    # Тест создания предложения
    proposal = test_create_proposal(token)
    
    # Тест списка предложений
    proposals = test_proposals_list(token)
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    main()
