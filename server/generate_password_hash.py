#!/usr/bin/env python3
"""
Скрипт для генерации хеша пароля
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "admin123"
hashed_password = pwd_context.hash(password)

print(f"Пароль: {password}")
print(f"Хеш: {hashed_password}")

# Проверяем, что хеш работает
is_valid = pwd_context.verify(password, hashed_password)
print(f"Проверка хеша: {is_valid}")
