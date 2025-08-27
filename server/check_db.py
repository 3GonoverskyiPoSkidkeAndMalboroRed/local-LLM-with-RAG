#!/usr/bin/env python3
"""
Скрипт для проверки базы данных
"""

from database import get_db
from models_db import User, Department
from sqlalchemy.orm import Session
from sqlalchemy import text

def check_database():
    """Проверяем базу данных"""
    print("🔍 Проверяем базу данных...")
    
    db = next(get_db())
    
    try:
        # Проверяем роли (прямой запрос к БД)
        print("\n📋 Роли в системе:")
        result = db.execute(text("SELECT id, role_name FROM role"))
        roles = result.fetchall()
        for role in roles:
            print(f"  {role[0]}: {role[1]}")
        
        # Проверяем отделы
        print("\n🏢 Отделы в системе:")
        departments = db.query(Department).all()
        for dept in departments:
            print(f"  {dept.id}: {dept.department_name}")
        
        # Проверяем пользователей
        print("\n👥 Пользователи в системе:")
        users = db.query(User).all()
        for user in users:
            # Получаем роль и отдел через прямые запросы
            role_result = db.execute(text(f"SELECT role_name FROM role WHERE id = {user.role_id}"))
            role_row = role_result.fetchone()
            role_name = role_row[0] if role_row else "Нет роли"
            
            dept_result = db.execute(text(f"SELECT department_name FROM department WHERE id = {user.department_id}"))
            dept_row = dept_result.fetchone()
            dept_name = dept_row[0] if dept_row else "Нет отдела"
            
            print(f"  {user.id}: {user.login} - {user.full_name} ({role_name}, {dept_name})")
        
        # Проверяем хеш пароля админа
        admin = db.query(User).filter(User.login == "admin").first()
        if admin:
            role_result = db.execute(text(f"SELECT role_name FROM role WHERE id = {admin.role_id}"))
            role_row = role_result.fetchone()
            role_name = role_row[0] if role_row else "Нет роли"
            
            print(f"\n🔐 Админ найден:")
            print(f"  Логин: {admin.login}")
            print(f"  Хеш пароля: {admin.password[:20]}...")
            print(f"  Роль: {role_name}")
        else:
            print("\n❌ Админ не найден!")
        
        # Проверяем ответственного отдела
        resp = db.query(User).filter(User.login == "resp_it").first()
        if resp:
            role_result = db.execute(text(f"SELECT role_name FROM role WHERE id = {resp.role_id}"))
            role_row = role_result.fetchone()
            role_name = role_row[0] if role_row else "Нет роли"
            
            print(f"\n👤 Ответственный найден:")
            print(f"  Логин: {resp.login}")
            print(f"  Хеш пароля: {resp.password[:20]}...")
            print(f"  Роль: {role_name}")
        else:
            print("\n❌ Ответственный не найден!")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
