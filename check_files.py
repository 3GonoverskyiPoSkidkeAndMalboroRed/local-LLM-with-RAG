#!/usr/bin/env python3
"""
Скрипт для проверки содержимого Docker volume с файлами
"""

import os
import subprocess
import sys

def check_docker_volume():
    """Проверяет содержимое Docker volume"""
    print("🔍 Проверка содержимого Docker volume...")
    
    # Проверяем, что Docker доступен
    try:
        result = subprocess.run(['docker', 'volume', 'ls'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker недоступен или не запущен")
            return False
    except FileNotFoundError:
        print("❌ Docker не установлен или не доступен в PATH")
        return False
    
    # Ищем volume с файлами
    volume_name = None
    for line in result.stdout.split('\n'):
        if 'files_storage' in line:
            volume_name = line.split()[-1]
            break
    
    if not volume_name:
        print("❌ Volume с файлами не найден")
        return False
    
    print(f"✅ Найден volume: {volume_name}")
    
    # Проверяем содержимое volume
    try:
        cmd = f'docker run --rm -v {volume_name}:/files alpine ls -la /files'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📁 Содержимое volume:")
            print(result.stdout)
        else:
            print("❌ Ошибка при чтении volume:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Ошибка при проверке volume: {e}")
        return False
    
    return True

def check_container_files():
    """Проверяет файлы внутри контейнера"""
    print("\n🔍 Проверка файлов внутри контейнера...")
    
    try:
        # Проверяем базовую директорию
        cmd = 'docker exec local-llm-with-rag-backend-1 ls -la /app/files/'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📁 Содержимое /app/files/:")
            print(result.stdout)
        else:
            print("❌ Ошибка при чтении /app/files/:")
            print(result.stderr)
        
        # Проверяем директорию отдела
        cmd = 'docker exec local-llm-with-rag-backend-1 ls -la /app/files/ContentForDepartment/5/'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📁 Содержимое /app/files/ContentForDepartment/5/:")
            print(result.stdout)
        else:
            print("❌ Ошибка при чтении /app/files/ContentForDepartment/5/:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Ошибка при проверке контейнера: {e}")

def main():
    print("🚀 Проверка системы файлов")
    print("=" * 50)
    
    # Проверяем Docker volume
    if check_docker_volume():
        print("\n✅ Docker volume работает корректно")
    else:
        print("\n❌ Проблемы с Docker volume")
    
    # Проверяем файлы в контейнере
    check_container_files()
    
    print("\n" + "=" * 50)
    print("📋 Резюме:")
    print("- Файлы сохраняются в Docker volume, а не в локальной файловой системе")
    print("- Путь /app/files/ существует только внутри контейнера")
    print("- Для доступа к файлам используйте Docker команды или API")

if __name__ == "__main__":
    main() 