#!/usr/bin/env python3
"""
Быстрый тест Yandex GPT эндпоинтов
"""

import requests
import json
import os
from typing import Optional

def quick_test():
    """Быстрый тест основных эндпоинтов"""
    base_url = "http://localhost:8000/api/yandex"
    
    print("Быстрый тест Yandex GPT эндпоинтов")
    print("=" * 40)
    
    # 1. Проверка конфигурации
    print("1. Проверка конфигурации...")
    try:
        response = requests.get(f"{base_url}/config")
        if response.status_code == 200:
            config = response.json()
            print(f"   Настроено: {config.get('is_configured', False)}")
            if config.get('folder_id'):
                print(f"   Folder ID: {config['folder_id']}")
        else:
            print(f"   Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 2. Проверка здоровья
    print("\n2. Проверка здоровья API...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   Статус: {health.get('status', 'unknown')}")
        else:
            print(f"   Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 3. Тест генерации
    print("\n3. Тест генерации текста...")
    try:
        data = {
            "prompt": "Привет! Как дела?",
            "model": "yandexgpt",
            "temperature": 0.1,
            "max_tokens": 50
        }
        response = requests.post(f"{base_url}/generate", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"   Ответ: {result.get('text', '')[:100]}...")
            print(f"   Время: {result.get('response_time', 0):.2f}с")
        else:
            print(f"   Ошибка: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    print("\n" + "=" * 40)
    print("Тест завершен!")

if __name__ == "__main__":
    quick_test() 