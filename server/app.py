# УРЕЗАННАЯ ВЕРСИЯ БЕЗ OLLAMA
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query, APIRouter
from pydantic import BaseModel
import uvicorn
import os

from sqlalchemy import create_engine, text, inspect, or_
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import secrets
from typing import List
from fastapi.responses import FileResponse

from models_db import User, Department, Access, Content, Tag
import argparse
import sys
from database import get_db

from quiz import router as quiz_router
from routes.directory_routes import router as directory_router
from routes.content_routes import router as content_router
from routes.user_routes import router as user_router
from routes.feedback_routes import router as feedback_router

# Инициализация глобальных переменных
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Добавляем маршрутизаторы (исключаем llm_router)
app.include_router(quiz_router)
app.include_router(directory_router)
app.include_router(content_router)
app.include_router(user_router)
app.include_router(feedback_router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки подключения к базе данных
DATABASE_URL = "mysql+mysqlconnector://root:123123@77.222.42.53:3306/db_test"

# Создание движка и сессии
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Классы для запросов (заглушки для совместимости)
class GenerateRequest(BaseModel):
    messages: str
    model: str = "disabled"

class GenerateResponse(BaseModel):
    text: str
    model: str = "disabled"

# Эндпоинт для парсинга аргументов
@app.get("/parse-args")
async def parse_args():
    args = parse_arguments()
    return {
        "port": args.port,
        "message": "LLM functionality disabled"
    }

@app.get("/check_db_connection")
async def check_db_connection():
    try:
        # Создаем сессию
        db = SessionLocal()
        # Выполняем простой запрос для проверки подключения
        db.execute(text("SELECT 1"))
        return {"message": "Подключение к базе данных успешно!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к базе данных: {str(e)}")
    finally:
        db.close()

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run document viewer without LLM.")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the web server.",
    )
    return parser.parse_args()



@app.get("/api/departments")
async def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return [{"id": dept.id, "department_name": dept.department_name} for dept in departments]

@app.get("/api/access_levels")
async def get_access_levels(db: Session = Depends(get_db)):
    access_levels = db.query(Access).all()
    return [{"id": access_level.id, "access_name": access_level.access_name} for access_level in access_levels]

@app.get("/departments")
async def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return [{"id": dept.id, "name": dept.department_name} for dept in departments]

@app.get("/access-levels")
async def get_access_level(db: Session = Depends(get_db)):
    access_levels = db.query(Access).all()
    return [{"id": access.id, "access_name": access.access_name} for access in access_levels]

@app.get("/tables")
async def get_tables(db: Session = Depends(get_db)):
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении таблиц: {str(e)}")

@app.get("/tables/{table_name}")
async def get_table_info(table_name: str, db: Session = Depends(get_db)):
    try:
        inspector = inspect(db.bind)
        columns = inspector.get_columns(table_name)
        return {"table": table_name, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации о таблице {table_name}: {str(e)}")

class TagCreate(BaseModel):
    tag_name: str

@app.post("/tags")
async def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    try:
        new_tag = Tag(tag_name=tag.tag_name)
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        return {"message": "Тег успешно добавлен", "tag": new_tag}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении тега: {str(e)}")

@app.get("/tags")
async def get_tags(db: Session = Depends(get_db)):
    try:
        tags = db.query(Tag).all()  # Получаем все теги из базы данных
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении тегов: {str(e)}")

@app.get("/user/{user_id}/content/by-tags")
async def get_user_content_by_tags(user_id: int, db: Session = Depends(get_db)):
    try:
        # Получаем пользователя по user_id
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Получаем все теги
        tags = db.query(Tag).all()
        
        # Создаем словарь для результата
        result = {
            "tags": [],
            "untagged_content": []
        }
        
        # Добавляем информацию о тегах и связанном контенте
        for tag in tags:
            # Получаем контент для данного тега с учетом прав доступа пользователя
            tag_content = db.query(Content).filter(
                Content.tag_id == tag.id,
                Content.access_level == user.access_id,
                Content.department_id == user.department_id
            ).all()
            
            # Если есть контент для этого тега, добавляем его в результат
            if tag_content:
                tag_info = {
                    "id": tag.id,
                    "tag_name": tag.tag_name,
                    "content": []
                }
                
                for content in tag_content:
                    tag_info["content"].append({
                        "id": content.id,
                        "title": content.title,
                        "description": content.description,
                        "file_path": content.file_path
                    })
                
                result["tags"].append(tag_info)
        
        # Получаем контент без тега
        untagged_content = db.query(Content).filter(
            Content.tag_id == None,
            Content.access_level == user.access_id,
            Content.department_id == user.department_id
        ).all()
        
        # Добавляем контент без тега в результат
        for content in untagged_content:
            result["untagged_content"].append({
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении контента: {str(e)}")


@app.get("/initialized-departments")
async def get_initialized_departments():
    """
    Возвращает сообщение о том, что LLM функционал отключен.
    """
    return {"message": "LLM functionality disabled"}

@app.get("/search-documents")
async def search_documents(
    user_id: int,
    search_query: str = Query(None, description="Поисковый запрос для названия, описания или имени файла"),
    db: Session = Depends(get_db)
):
    try:
        # Получаем пользователя по user_id для проверки прав доступа
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Базовый запрос с учетом прав доступа пользователя
        query = db.query(Content).filter(
            Content.access_level == user.access_id,
            Content.department_id == user.department_id
        )
        
        # Если указан поисковый запрос, добавляем условия поиска
        if search_query:
            # Получаем имя файла из пути
            query = query.filter(
                or_(
                    Content.title.ilike(f"%{search_query}%"),  # Поиск по названию
                    Content.description.ilike(f"%{search_query}%"),  # Поиск по описанию
                    Content.file_path.ilike(f"%{search_query}%")  # Поиск по пути файла (включая имя файла)
                )
            )
        
        # Выполняем запрос
        contents = query.all()
        
        # Если контент не найден, возвращаем пустой список
        if not contents:
            return {"documents": []}
        
        # Формируем результат
        result = []
        for content in contents:
            # Получаем имя файла из пути
            file_name = os.path.basename(content.file_path) if content.file_path else "Имя файла недоступно"
            
            # Получаем название отдела
            department = db.query(Department).filter(Department.id == content.department_id).first()
            department_name = department.department_name if department else "Неизвестный отдел"
            
            # Получаем название уровня доступа
            access = db.query(Access).filter(Access.id == content.access_level).first()
            access_name = access.access_name if access else "Неизвестный уровень"
            
            # Получаем название тега, если он есть
            tag_name = None
            if content.tag_id:
                tag = db.query(Tag).filter(Tag.id == content.tag_id).first()
                tag_name = tag.tag_name if tag else None
            
            result.append({
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path,
                "file_name": file_name,
                "department_id": content.department_id,
                "department_name": department_name,
                "access_level": content.access_level,
                "access_name": access_name,
                "tag_id": content.tag_id,
                "tag_name": tag_name
            })
        
        return {"documents": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске документов: {str(e)}")

if __name__ == "__main__":
    args = parse_arguments()
    # main(args.model, args.embedding_model, args.path, args.department, args.web, args.port) # Удален вызов main
    uvicorn.run(app, host="0.0.0.0", port=args.port, access_log=True)
