from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os

# Настройки подключения к базе данных
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:123123@localhost:3307/db_main")

# Создание движка базы данных
engine = create_engine(DATABASE_URL)

# Создание базового класса для моделей
Base = declarative_base()

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Проверка подключения к базе данных
def check_connection():
    try:
        with engine.connect() as connection:
            print("Подключение к базе данных успешно!")
    except SQLAlchemyError as e:
        print(f"Ошибка подключения: {e}")
