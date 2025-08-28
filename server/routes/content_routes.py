from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Request, status, Query
import os
from sqlalchemy.orm import Session
from database import get_db
from models_db import Access, Content, User, Tag
from routes.user_routes import get_current_user, require_admin, is_admin
from utils.permissions import PermissionChecker
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from typing import List, Optional
import re
import requests
import shutil
import mimetypes
import urllib.parse
# ✅ Добавляем импорт для rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/content", tags=["content"])

# ✅ Добавляем rate limiter
limiter = Limiter(key_func=get_remote_address)

# Модель для пакетной загрузки контента
class BatchContentItem(BaseModel):
    title: Optional[str] = None  # Если не указано, будет использовано имя файла
    description: Optional[str] = None
    tag_id: Optional[int] = None

# Модель для пакетной загрузки
class BatchUploadRequest(BaseModel):
    access_id: int
    department_id: int
    items: List[BatchContentItem] = []  # Опционально для указания названий/описаний
    use_filename_as_title: bool = True  # Использовать имя файла как название по умолчанию

@router.get("/document-viewer/{content_id}")
@limiter.limit("100/minute")  # ✅ Высокий лимит для просмотра документов
async def get_document_viewer_page(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает HTML страницу для просмотра документа через Google Docs Viewer
    """
    try:
        # Получаем контент из базы данных
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Проверяем доступ пользователя к документу
        if not PermissionChecker.can_view_content(current_user, content):
            # Логируем для отладки
            print(f"Access denied for user {current_user.id} to content {content_id}")
            print(f"User access_id: {current_user.access_id}, content access_level: {content.access_level}")
            print(f"User department_id: {current_user.department_id}, content department_id: {content.department_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра документа")

        # Получаем расширение файла
        file_extension = content.file_path.lower().split('.')[-1] if '.' in content.file_path else ''
        
        # Определяем URL для скачивания файла - используем полный URL
        base_url = str(request.base_url).rstrip('/')
        download_url = f"{base_url}/content/download-file/{content_id}"
        
        # Поддерживаемые форматы для Google Docs Viewer
        supported_formats = ['doc', 'docx', 'pdf', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'rtf']
        
        if file_extension in supported_formats:
            # Используем Google Docs Viewer для поддерживаемых форматов
            google_docs_url = f"https://docs.google.com/viewer?url={download_url}&embedded=true"
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.title} - Просмотр документа</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: Arial, sans-serif;
                        background-color: #f5f5f5;
                    }}
                    .header {{
                        background: #f8f9fa;
                        padding: 15px 20px;
                        border-bottom: 1px solid #dee2e6;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 18px;
                        color: #333;
                    }}
                    .header .controls {{
                        display: flex;
                        gap: 10px;
                    }}
                    .btn {{
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 14px;
                    }}
                    .btn-primary {{
                        background: #007bff;
                        color: white;
                    }}
                    .btn-secondary {{
                        background: #6c757d;
                        color: white;
                    }}
                    .google-docs-info {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        color: #856404;
                        padding: 10px;
                        border-radius: 4px;
                        margin: 10px 20px;
                    }}
                    #viewer {{
                        width: 100%;
                        height: calc(100vh - 80px);
                        border: none;
                    }}
                    .fallback-content {{
                        padding: 20px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{content.title}</h1>
                    <div class="controls">
                        <a href="{download_url}" class="btn btn-primary">Скачать</a>
                        <a href="javascript:history.back()" class="btn btn-secondary">Назад</a>
                    </div>
                </div>
                <div class="google-docs-info">
                    <strong>Внимание:</strong> Google Docs Viewer может не работать с файлами на localhost. 
                    Для корректной работы убедитесь, что файл доступен по публичному URL.
                </div>
                <iframe id="viewer" src="{google_docs_url}" onerror="showFallback()"></iframe>
                <div id="fallback" class="fallback-content" style="display: none;">
                    <h3>Google Docs Viewer недоступен</h3>
                    <p>Попробуйте скачать файл для просмотра в соответствующем приложении.</p>
                    <a href="{download_url}" class="btn btn-primary">Скачать файл</a>
                </div>
                <script>
                    function showFallback() {{
                        document.getElementById('viewer').style.display = 'none';
                        document.getElementById('fallback').style.display = 'block';
                    }}
                    
                    // Проверяем загрузку iframe
                    setTimeout(function() {{
                        const iframe = document.getElementById('viewer');
                        if (iframe.contentDocument && iframe.contentDocument.body.innerHTML.includes('error')) {{
                            showFallback();
                        }}
                    }}, 5000);
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        else:
            # Для неподдерживаемых форматов показываем сообщение
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.title} - Неподдерживаемый формат</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .btn {{
                        padding: 10px 20px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 14px;
                        margin: 10px;
                    }}
                    .btn-primary {{
                        background: #007bff;
                        color: white;
                    }}
                    .btn-secondary {{
                        background: #6c757d;
                        color: white;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Неподдерживаемый формат файла</h1>
                    <p>Формат файла <strong>.{file_extension}</strong> не поддерживается для просмотра в браузере.</p>
                    <p>Вы можете скачать файл для просмотра в соответствующем приложении.</p>
                    <div>
                        <a href="{download_url}" class="btn btn-primary">Скачать файл</a>
                        <a href="javascript:history.back()" class="btn btn-secondary">Назад</a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
            
    except Exception as e:
        print(f"Error in document viewer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании страницы просмотра: {str(e)}")

@router.get("/document-viewer-with-highlight/{content_id}")
@limiter.limit("100/minute")
async def get_document_viewer_with_highlight(
    request: Request,
    content_id: int,
    search_query: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает HTML страницу для просмотра документа с выделением найденных отрывков
    """
    try:
        # Получаем контент из базы данных
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Проверяем доступ пользователя к документу
        if not (is_admin(current_user) or (
            current_user.access_id == content.access_level and current_user.department_id == content.department_id
        )):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра документа")

        # Получаем расширение файла
        file_extension = content.file_path.lower().split('.')[-1] if '.' in content.file_path else ''
        
        # Определяем URL для скачивания файла
        base_url = str(request.base_url).rstrip('/')
        download_url = f"{base_url}/content/download-file/{content_id}"
        
        # Поддерживаемые форматы для просмотра с выделением
        supported_formats = ['txt', 'md', 'html']
        
        if file_extension in supported_formats:
            # Читаем содержимое файла
            try:
                file_path = os.path.join("documents", content.file_path)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                else:
                    file_content = f"Файл {content.file_path} не найден на сервере."
            except Exception as e:
                file_content = f"Ошибка при чтении файла: {str(e)}"
            
            # Выделяем найденные отрывки, если есть поисковый запрос
            if search_query:
                import re
                pattern = re.compile(f'({re.escape(search_query)})', re.IGNORECASE)
                file_content = pattern.sub(r'<mark>\1</mark>', file_content)
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.title} - Просмотр документа</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #f8f9fa;
                    }}
                    .header {{
                        background: #ffffff;
                        padding: 15px 20px;
                        border-bottom: 1px solid #dee2e6;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 20px;
                        color: #333;
                        font-weight: 600;
                    }}
                    .header .controls {{
                        display: flex;
                        gap: 10px;
                    }}
                    .btn {{
                        padding: 8px 16px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 14px;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }}
                    .btn-primary {{
                        background: #007bff;
                        color: white;
                    }}
                    .btn-primary:hover {{
                        background: #0056b3;
                    }}
                    .btn-secondary {{
                        background: #6c757d;
                        color: white;
                    }}
                    .btn-secondary:hover {{
                        background: #545b62;
                    }}
                    .document-container {{
                        max-width: 800px;
                        margin: 20px auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .document-content {{
                        padding: 30px;
                        line-height: 1.8;
                        font-size: 16px;
                        color: #333;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                    .document-content mark {{
                        background-color: #fff3cd;
                        color: #856404;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-weight: 600;
                    }}
                    .search-info {{
                        background: #e7f3ff;
                        border: 1px solid #b3d9ff;
                        color: #0066cc;
                        padding: 10px 20px;
                        margin: 0;
                        font-size: 14px;
                    }}
                    .document-meta {{
                        background: #f8f9fa;
                        padding: 15px 30px;
                        border-bottom: 1px solid #dee2e6;
                        color: #6c757d;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{content.title}</h1>
                    <div class="controls">
                        <a href="{download_url}" class="btn btn-primary">Скачать</a>
                        <a href="javascript:history.back()" class="btn btn-secondary">Назад</a>
                    </div>
                </div>
                <div class="document-container">
                    <div class="document-meta">
                        <strong>Формат:</strong> {file_extension.upper()} | 
                        <strong>Размер:</strong> {len(file_content)} символов
                        {f' | <strong>Поиск:</strong> "{search_query}"' if search_query else ''}
                    </div>
                    {f'<div class="search-info">Найдено выделений для запроса: <strong>"{search_query}"</strong></div>' if search_query else ''}
                    <div class="document-content">{file_content}</div>
                </div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        else:
            # Для неподдерживаемых форматов перенаправляем на обычный просмотр
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Перенаправление</title>
            </head>
            <body>
                <script>
                    window.location.href = '{base_url}/content/document-viewer/{content_id}';
                </script>
                <p>Перенаправление на просмотр документа...</p>
            </body>
            </html>
            """)
            
    except Exception as e:
        print(f"Error in document viewer with highlight: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании страницы просмотра: {str(e)}")

@router.post("/upload-content")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для загрузки контента
async def upload_content(
    request: Request,
    files: List[UploadFile] = File(...),
    access_id: int = Form(...),
    department_id: int = Form(...),
    tag_id: Optional[int] = Form(None),
    user_id: Optional[int] = Form(None),
    use_filename_as_title: bool = Form(True),
    titles: Optional[str] = Form(None),  # JSON строка с названиями
    descriptions: Optional[str] = Form(None),  # JSON строка с описаниями
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Пакетная загрузка контента с поддержкой множественных файлов.
    Названия документов могут быть указаны в параметре titles (JSON массив),
    или будут взяты из имен файлов, если use_filename_as_title=True
    """
    import json
    
    # Проверки прав: user_id (если передан) должен совпадать с текущим пользователем, иначе только админ
    if user_id is not None and user_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для загрузки от имени другого пользователя")

    # Админ может грузить в любой отдел; не-админ только в свой отдел
    if not is_admin(current_user) and department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для загрузки в другой отдел")

    # Проверка существования уровня доступа
    access = db.query(Access).filter(Access.id == access_id).first()
    if access is None:
        raise HTTPException(status_code=400, detail="Уровень доступа не найден")

    # Создаем базовую директорию /app/files/, если она не существует
    os.makedirs("/app/files/", exist_ok=True)
    
    # Автоматически формируем путь на основе ID отдела с новой структурой
    department_directory = f"ContentForDepartment/AllTypesOfFiles/{department_id}"
    target_dir = f"/app/files/{department_directory}"
    
    # Создаем директорию для отдела, если она не существует
    os.makedirs(target_dir, exist_ok=True)
    
    # Парсим названия и описания из JSON строк
    titles_list = []
    descriptions_list = []
    
    if titles:
        try:
            titles_list = json.loads(titles)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Неверный формат JSON для названий")
    
    if descriptions:
        try:
            descriptions_list = json.loads(descriptions)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Неверный формат JSON для описаний")
    
    # Список для хранения информации о загруженных файлах
    uploaded_files_info = []
    
    for i, file in enumerate(files):
        # Определяем название документа
        if i < len(titles_list) and titles_list[i]:
            title = titles_list[i]
        elif use_filename_as_title:
            # Убираем расширение файла для более красивого названия
            title = os.path.splitext(file.filename)[0]
        else:
            title = file.filename
        
        # Определяем описание документа
        if i < len(descriptions_list) and descriptions_list[i]:
            description = descriptions_list[i]
        else:
            description = f"Загруженный файл: {file.filename}"
        
        # Формируем полный путь к файлу
        file_location = f"{target_dir}/{file.filename}"
        
        try:
            with open(file_location, "wb") as f:
                f.write(await file.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла {file.filename}: {str(e)}")

        # Создание записи в базе данных
        new_content = Content(
            title=title,
            description=description,
            file_path=file_location,
            access_level=access_id,
            department_id=department_id,
            tag_id=tag_id  # Указываем тег, если он есть
        )
        db.add(new_content)
        db.commit()
        db.refresh(new_content)

        uploaded_files_info.append({
            "id": new_content.id,
            "filename": file.filename,
            "title": title,
            "description": description,
            "file_path": file_location
        })

    return {
        "message": f"Контент успешно загружен в {target_dir}",
        "uploaded_count": len(uploaded_files_info),
        "files": uploaded_files_info
    }

@router.post("/upload-content-batch")
@limiter.limit("15/minute")  # ✅ Умеренный лимит для пакетной загрузки
async def upload_content_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    batch_data: BatchUploadRequest = Form(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Пакетная загрузка контента с использованием структурированных данных.
    Поддерживает указание названий и описаний для каждого файла через batch_data.items
    """
    # Проверки прав: user_id (если передан) должен совпадать с текущим пользователем, иначе только админ
    if user_id is not None and user_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для загрузки от имени другого пользователя")

    # Админ может грузить в любой отдел; не-админ только в свой отдел
    if not is_admin(current_user) and batch_data.department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для загрузки в другой отдел")

    # Проверка существования уровня доступа
    access = db.query(Access).filter(Access.id == batch_data.access_id).first()
    if access is None:
        raise HTTPException(status_code=400, detail="Уровень доступа не найден")

    # Создаем базовую директорию /app/files/, если она не существует
    os.makedirs("/app/files/", exist_ok=True)
    
    # Автоматически формируем путь на основе ID отдела с новой структурой
    department_directory = f"ContentForDepartment/AllTypesOfFiles/{batch_data.department_id}"
    target_dir = f"/app/files/{department_directory}"
    
    # Создаем директорию для отдела, если она не существует
    os.makedirs(target_dir, exist_ok=True)
    
    # Список для хранения информации о загруженных файлах
    uploaded_files_info = []
    
    for i, file in enumerate(files):
        # Получаем данные для текущего файла
        item_data = batch_data.items[i] if i < len(batch_data.items) else BatchContentItem()
        
        # Определяем название документа
        if item_data.title:
            title = item_data.title
        elif batch_data.use_filename_as_title:
            # Убираем расширение файла для более красивого названия
            title = os.path.splitext(file.filename)[0]
        else:
            title = file.filename
        
        # Определяем описание документа
        if item_data.description:
            description = item_data.description
        else:
            description = f"Загруженный файл: {file.filename}"
        
        # Формируем полный путь к файлу
        file_location = f"{target_dir}/{file.filename}"
        
        try:
            with open(file_location, "wb") as f:
                f.write(await file.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла {file.filename}: {str(e)}")

        # Создание записи в базе данных
        new_content = Content(
            title=title,
            description=description,
            file_path=file_location,
            access_level=batch_data.access_id,
            department_id=batch_data.department_id,
            tag_id=item_data.tag_id
        )
        db.add(new_content)
        db.commit()
        db.refresh(new_content)

        uploaded_files_info.append({
            "id": new_content.id,
            "filename": file.filename,
            "title": title,
            "description": description,
            "file_path": file_location,
            "tag_id": item_data.tag_id
        })

    return {
        "message": f"Контент успешно загружен в {target_dir}",
        "uploaded_count": len(uploaded_files_info),
        "files": uploaded_files_info
    }

@router.post("/upload-files")
@limiter.limit("10/minute")  # ✅ Строгий лимит для массовой загрузки
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    access_level: int = 1,
    department_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверки прав на массовую загрузку
    if not is_admin(current_user) and department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для загрузки в другой отдел")
    # Базовая директория для всех файлов
    base_dir = "/app/files"
    print(f"DEBUG: Создаем базовую директорию: {base_dir}")
    os.makedirs(base_dir, exist_ok=True)
    print(f"DEBUG: Базовая директория создана/существует: {os.path.exists(base_dir)}")
    
    # Автоматически формируем путь на основе ID отдела
    department_directory = f"ContentForDepartment/{department_id}"
    target_dir = os.path.join(base_dir, department_directory)
    print(f"DEBUG: Целевая директория: {target_dir}")
    
    # Создаем директорию для отдела, если она не существует
    os.makedirs(target_dir, exist_ok=True)
    print(f"DEBUG: Директория отдела создана/существует: {os.path.exists(target_dir)}")
    
    # Список для хранения информации о загруженных файлах
    uploaded_files_info = []

    for file in files:
        # Сохранение файла в указанной директории
        file_location = os.path.join(target_dir, file.filename)
        
        try:
            with open(file_location, "wb") as f:
                f.write(await file.read())
            
            # Сохраняем относительный путь в БД (относительно /app/files/)
            relative_path = os.path.relpath(file_location, base_dir)
            db_file_path = os.path.join(base_dir, relative_path)
            
            # Добавление информации о файле в базу данных
            new_content = Content(
                title=file.filename,
                description="Загруженный файл",
                file_path=db_file_path,  # Сохраняем полный путь
                access_level=access_level,
                department_id=department_id,
                tag_id=None
            )
            db.add(new_content)
            db.commit()
            db.refresh(new_content)

            uploaded_files_info.append({
                "filename": file.filename,
                "file_path": db_file_path
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла {file.filename}: {str(e)}")

    return {"message": f"Файлы успешно загружены в {target_dir}", "files": uploaded_files_info}

# Модель для обновления контента
class ContentUpdate(BaseModel):
    title: str = None
    description: str = None
    access_id: int = None
    department_id: int = None
    tag_id: int = None

@router.put("/{content_id}")
@limiter.limit("30/minute")  # ✅ Умеренный лимит для обновления контента
async def update_content(
    request: Request,
    content_id: int,
    content_data: ContentUpdate,
    db: Session = Depends(get_db)
):
    # Отладочный вывод входных параметров
    print(f"Получены параметры: content_id={content_id}, data={content_data}")
    
    # Получаем контент из базы данных по ID
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Контент не найден")

    # Обновляем поля, если они были переданы
    if content_data.title is not None:
        content.title = content_data.title
    if content_data.description is not None:
        content.description = content_data.description
    if content_data.access_id is not None:
        # Проверка существования уровня доступа
        access = db.query(Access).filter(Access.id == content_data.access_id).first()
        if access is None:
            raise HTTPException(status_code=400, detail="Уровень доступа не найден")
        content.access_level = content_data.access_id
    if content_data.department_id is not None:
        content.department_id = content_data.department_id
    if content_data.tag_id is not None:
        content.tag_id = content_data.tag_id

    db.commit()
    db.refresh(content)

    return {"message": "Контент успешно обновлен", "content": content}

class ContentBase(BaseModel):
    id: int
    title: str
    description: str
    file_path: str

    class Config:
        from_attributes = True

@router.get("/content/filter")
@limiter.limit("120/minute")  # ✅ Высокий лимит для фильтрации
async def get_content_by_access_and_department(
    request: Request,
    access_level: int,
    department_id: int,
    tag_id: int = None,  # Новый параметр для фильтрации по тегу
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Content).filter(
            Content.access_level == access_level,
            Content.department_id == department_id
        )
        
        if tag_id is not None:
            query = query.filter(Content.tag_id == tag_id)  # Фильтрация по тегу

        contents = query.all()

        if not contents:
            raise HTTPException(status_code=404, detail="Контент не найден")

        return [
            {
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path,
                "access_level": content.access_level,
                "department_id": content.department_id,
                "tag_id": content.tag_id  # Возвращаем ID тега
            } for content in contents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении контента: {str(e)}")
    
    
@router.get("/content/{content_id}")
@limiter.limit("100/minute")  # ✅ Высокий лимит для получения контента
async def get_content_by_id(
    request: Request,
    content_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        if content is None:
            raise HTTPException(status_code=404, detail="Контент не найден")
        
        # Проверяем права доступа: админ или пользователь имеет доступ к контенту
        if not (is_admin(current_user) or (
            current_user.access_id == content.access_level and current_user.department_id == content.department_id
        )):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для доступа к контенту")
        
        return {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "file_path": content.file_path,
            "access_level": content.access_level,
            "department_id": content.department_id,
            "tag_id": content.tag_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении контента: {str(e)}")

@router.delete("/content/{content_id}")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для удаления
async def delete_content(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Получаем контент по ID
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Контент не найден")
        
        # Проверяем права: админ или владеет по департаменту/уровню
        if not (is_admin(current_user) or (
            current_user.access_id == content.access_level and current_user.department_id == content.department_id
        )):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для удаления контента")

        # Сохраняем путь к файлу
        file_path = content.file_path
        
        # Удаляем контент из базы данных
        db.delete(content)
        db.commit()
        
        # Удаляем файл с сервера, если он существует
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Ошибка при удалении файла {file_path}: {e}")
        
        return {"message": "Контент успешно удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении контента: {str(e)}")


@router.get("/all")
@limiter.limit("30/minute")  # ✅ Умеренный лимит для получения всего контента
async def get_all_content(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        contents = db.query(Content).all()
        return [
            {
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path,
                "access_level": content.access_level,
                "department_id": content.department_id,
                "tag_id": content.tag_id
            } for content in contents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении контента: {str(e)}")
    
    
def get_mime_type(file_path):
    """Определяет MIME-тип файла по расширению"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

@router.options("/download-file/{content_id}")
async def download_file_options(content_id: int):
    """Обработчик OPTIONS запросов для CORS"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.get("/download-file/{content_id}")
@limiter.limit("50/minute")  # ✅ Умеренный лимит для скачивания
async def download_file(
    request: Request,
    content_id: int,
    user_id: Optional[int] = Query(None, description="ID пользователя (опционально)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Получаем контент из базы данных по ID
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Контент не найден")

    # Определяем пользователя для проверки прав доступа
    user_to_check = current_user
    if user_id is not None:
        # Если передан user_id, получаем пользователя из базы
        user_to_check = db.query(User).filter(User.id == user_id).first()
        if not user_to_check:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем права доступа пользователя
    if not (is_admin(user_to_check) or (
        user_to_check.access_id == content.access_level and user_to_check.department_id == content.department_id
    )):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для скачивания файла")

    # Проверяем, существует ли файл
    file_path = content.file_path
    if not os.path.exists(file_path):
        # Если файл не найден по абсолютному пути, проверяем, может быть это старый путь
        # и нужно добавить префикс /app/files/
        if not file_path.startswith('/app/files/'):
            new_path = f"/app/files/{os.path.basename(file_path)}"
            if os.path.exists(new_path):
                file_path = new_path
            else:
                raise HTTPException(status_code=404, detail="Файл не найден")
        else:
            raise HTTPException(status_code=404, detail="Файл не найден")

    # Определяем MIME-тип файла
    mime_type = get_mime_type(file_path)
    
    # Получаем имя файла и кодируем его для заголовка
    filename = os.path.basename(file_path)
    try:
        # Пытаемся закодировать имя файла в latin-1
        filename_encoded = filename.encode('latin-1').decode('latin-1')
    except UnicodeEncodeError:
        # Если не получается, используем URL-кодирование
        filename_encoded = urllib.parse.quote(filename)
    
    # Определяем, нужно ли открывать файл в браузере или скачивать
    file_extension = file_path.lower().split('.')[-1] if '.' in file_path else ''
    is_pdf = file_extension == 'pdf'
    
    # Для PDF файлов используем inline, для остальных - attachment
    disposition = "inline" if is_pdf else "attachment"
    
    # Возвращаем файл как ответ с правильным MIME-типом
    return FileResponse(
        file_path, 
        media_type=mime_type, 
        filename=filename_encoded,
        headers={
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{urllib.parse.quote(filename)}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@router.get("/public-download/{content_id}")
@limiter.limit("30/minute")  # ✅ Умеренный лимит для публичного скачивания
async def public_download_file(
    request: Request,
    content_id: int,
    token: str = Query(..., description="Временный токен для скачивания"),
    db: Session = Depends(get_db),
):
    """
    Публичный эндпоинт для скачивания файлов с временным токеном.
    Используется для скачивания через window.location.href
    """
    try:
        # Декодируем токен (простая реализация - в продакшене нужно использовать JWT)
        import base64
        import json
        from datetime import datetime, timedelta
        
        try:
            # Декодируем токен
            decoded_token = base64.b64decode(token).decode('utf-8')
            token_data = json.loads(decoded_token)
            
            # Проверяем срок действия токена (1 час)
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if datetime.now() - token_time > timedelta(hours=1):
                raise HTTPException(status_code=401, detail="Токен истек")
                
            user_id = token_data['user_id']
            content_id_from_token = token_data['content_id']
            
            # Проверяем соответствие content_id
            if content_id_from_token != content_id:
                raise HTTPException(status_code=401, detail="Неверный токен")
                
        except Exception as e:
            raise HTTPException(status_code=401, detail="Неверный токен")
        
        # Получаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        
        # Получаем контент из базы данных по ID
        content = db.query(Content).filter(Content.id == content_id).first()
        if content is None:
            raise HTTPException(status_code=404, detail="Контент не найден")

        # Проверяем права доступа текущего пользователя
        if not (is_admin(user) or (
            user.access_id == content.access_level and user.department_id == content.department_id
        )):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для скачивания файла")

        # Проверяем, существует ли файл
        file_path = content.file_path
        if not os.path.exists(file_path):
            # Если файл не найден по абсолютному пути, проверяем, может быть это старый путь
            # и нужно добавить префикс /app/files/
            if not file_path.startswith('/app/files/'):
                new_path = f"/app/files/{os.path.basename(file_path)}"
                if os.path.exists(new_path):
                    file_path = new_path
                else:
                    raise HTTPException(status_code=404, detail="Файл не найден")
            else:
                raise HTTPException(status_code=404, detail="Файл не найден")

        # Получаем имя файла и кодируем его для заголовка
        filename = os.path.basename(file_path)
        try:
            # Пытаемся закодировать имя файла в latin-1
            filename_encoded = filename.encode('latin-1').decode('latin-1')
        except UnicodeEncodeError:
            # Если не получается, используем URL-кодирование
            filename_encoded = urllib.parse.quote(filename)
        
        # Определяем MIME-тип файла
        mime_type = get_mime_type(file_path)
        
        # Определяем, нужно ли открывать файл в браузере или скачивать
        file_extension = file_path.lower().split('.')[-1] if '.' in file_path else ''
        is_pdf = file_extension == 'pdf'
        
        # Для PDF файлов используем inline, для остальных - attachment
        disposition = "inline" if is_pdf else "attachment"
        
        # Возвращаем файл как ответ с правильным MIME-типом
        return FileResponse(
            file_path, 
            media_type=mime_type, 
            filename=filename_encoded,
            headers={
                "Content-Disposition": f"{disposition}; filename*=UTF-8''{urllib.parse.quote(filename)}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при скачивании файла: {str(e)}")


@router.get("/download-token/{content_id}")
@limiter.limit("50/minute")  # ✅ Умеренный лимит для получения токенов
async def get_download_token(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Генерирует временный токен для скачивания файла
    """
    # Получаем контент из базы данных по ID
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Контент не найден")

    # Проверяем права доступа текущего пользователя
    if not (is_admin(current_user) or (
        current_user.access_id == content.access_level and current_user.department_id == content.department_id
    )):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для скачивания файла")

    # Генерируем временный токен
    import base64
    import json
    from datetime import datetime
    
    token_data = {
        'user_id': current_user.id,
        'content_id': content_id,
        'timestamp': datetime.now().isoformat()
    }
    
    token = base64.b64encode(json.dumps(token_data).encode('utf-8')).decode('utf-8')
    
    return {"download_token": token}



@router.get("/user/{user_id}/content/by-tags/{tag_id}")
@limiter.limit("100/minute")  # ✅ Высокий лимит для получения контента по тегам
async def get_user_content_by_tags_and_tag_id(request: Request, user_id: int, tag_id: int, db: Session = Depends(get_db)):
    try:
        # Получаем пользователя по user_id
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Получаем контент для данного тега с учетом прав доступа пользователя
        tag_content = db.query(Content).filter(
            Content.tag_id == tag_id,
            Content.access_level == user.access_id,
            Content.department_id == user.department_id
        ).all()
        
        if not tag_content:
            raise HTTPException(status_code=404, detail="Контент не найден")

        return [
            {
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path
            }
            for content in tag_content
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении контента: {str(e)}")

@router.get("/search-documents")
@limiter.limit("80/minute")  # ✅ Высокий лимит для поиска
async def search_documents(
    request: Request,
    user_id: int,
    search_query: str = None,
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
            from sqlalchemy import or_
            # Поиск по названию, описанию или пути файла
            query = query.filter(
                or_(
                    Content.title.ilike(f"%{search_query}%"),  # Поиск по названию
                    Content.description.ilike(f"%{search_query}%"),  # Поиск по описанию
                    Content.file_path.ilike(f"%{search_query}%")  # Поиск по пути файла (включая имя файла)
                )
            )
        
        # Выполняем запрос
        contents = query.all()
        
        # Формируем результат
        documents = [
            {
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path,
                "tag_id": content.tag_id
            }
            for content in contents
        ]
        
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске документов: {str(e)}")

@router.post("/create-tag")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для создания тегов
async def create_tag(
    request: Request,
    tag_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        new_tag = Tag(tag_name=tag_name)
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        return {"message": "Тег успешно создан", "tag": new_tag}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании тега: {str(e)}")

@router.put("/update-tag/{tag_id}")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для обновления тегов
async def update_tag(
    request: Request,
    tag_id: int,
    tag_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if tag is None:
            raise HTTPException(status_code=404, detail="Тег не найден")
        tag.tag_name = tag_name
        db.commit()
        db.refresh(tag)
        return {"message": "Тег успешно обновлен", "tag": tag}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении тега: {str(e)}")

@router.delete("/delete-tag/{tag_id}")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для удаления тегов
async def delete_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Удаляет тег по ID.
    """
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if tag is None:
            raise HTTPException(status_code=404, detail="Тег не найден")
        
        db.delete(tag)
        db.commit()
        return {"message": "Тег успешно удален"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении тега: {str(e)}")

@router.get("/list-files/{department_id}")
@limiter.limit("60/minute")  # ✅ Умеренный лимит для списка файлов
async def list_department_files(request: Request, department_id: int):
    """
    Возвращает список файлов в директории отдела.
    """
    try:
        # Формируем путь к директории отдела
        department_path = f"/app/files/ContentForDepartment/{department_id}"
        
        if not os.path.exists(department_path):
            return {
                "department_id": department_id,
                "path": department_path,
                "exists": False,
                "files": [],
                "message": f"Директория для отдела {department_id} не существует"
            }
        
        # Получаем список файлов
        files = []
        for filename in os.listdir(department_path):
            file_path = os.path.join(department_path, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                # Форматируем размер файла
                if file_size < 1024:
                    size_formatted = f"{file_size} Б"
                elif file_size < 1024 * 1024:
                    size_formatted = f"{file_size / 1024:.1f} КБ"
                elif file_size < 1024 * 1024 * 1024:
                    size_formatted = f"{file_size / (1024 * 1024):.1f} МБ"
                else:
                    size_formatted = f"{file_size / (1024 * 1024 * 1024):.1f} ГБ"
                
                files.append({
                    "name": filename,
                    "size": file_size,
                    "size_formatted": size_formatted
                })
        
        return {
            "department_id": department_id,
            "path": department_path,
            "exists": True,
            "files": files,
            "total_files": len(files),
            "message": f"Найдено {len(files)} файлов в директории отдела {department_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка файлов: {str(e)}")

@router.delete("/delete-file/{department_id}/{filename}")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для удаления файлов
async def delete_department_file(request: Request, department_id: int, filename: str):
    """
    Удаляет конкретный файл из директории отдела.
    """
    try:
        # Формируем путь к файлу
        department_path = f"/app/files/ContentForDepartment/{department_id}"
        file_path = os.path.join(department_path, filename)
        
        # Проверяем, существует ли директория
        if not os.path.exists(department_path):
            raise HTTPException(status_code=404, detail=f"Директория для отдела {department_id} не существует")
        
        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Файл {filename} не найден в директории отдела {department_id}")
        
        # Удаляем файл
        os.remove(file_path)
        
        # Также удаляем запись из базы данных, если она существует
        from database import get_db
        from sqlalchemy.orm import Session
        db = next(get_db())
        try:
            content = db.query(Content).filter(
                Content.department_id == department_id,
                Content.file_path.like(f"%{filename}")
            ).first()
            
            if content:
                db.delete(content)
                db.commit()
        except Exception as db_error:
            print(f"Ошибка при удалении записи из БД: {db_error}")
        finally:
            db.close()
        
        return {"message": f"Файл {filename} успешно удален из директории отдела {department_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")

@router.delete("/delete-all-files/{department_id}")
@limiter.limit("5/minute")  # ✅ Строгий лимит для массового удаления
async def delete_all_department_files(request: Request, department_id: int):
    """
    Удаляет все файлы из директории отдела.
    """
    try:
        # Формируем путь к директории отдела
        department_path = f"/app/files/ContentForDepartment/{department_id}"
        
        # Проверяем, существует ли директория
        if not os.path.exists(department_path):
            raise HTTPException(status_code=404, detail=f"Директория для отдела {department_id} не существует")
        
        # Получаем список файлов
        files_to_delete = []
        for filename in os.listdir(department_path):
            file_path = os.path.join(department_path, filename)
            if os.path.isfile(file_path):
                files_to_delete.append((filename, file_path))
        
        if not files_to_delete:
            return {"message": f"В директории отдела {department_id} нет файлов для удаления"}
        
        # Удаляем все файлы
        deleted_count = 0
        for filename, file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Ошибка при удалении файла {filename}: {e}")
        
        # Также удаляем записи из базы данных
        from database import get_db
        from sqlalchemy.orm import Session
        db = next(get_db())
        try:
            contents = db.query(Content).filter(Content.department_id == department_id).all()
            for content in contents:
                db.delete(content)
            db.commit()
        except Exception as db_error:
            print(f"Ошибка при удалении записей из БД: {db_error}")
        finally:
            db.close()
        
        return {"message": f"Удалено {deleted_count} файлов из директории отдела {department_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файлов: {str(e)}")

@router.get("/list-all-departments")
@limiter.limit("30/minute")  # ✅ Умеренный лимит для списка отделов
async def list_all_departments(request: Request, ):
    """
    Возвращает список всех отделов с файлами.
    """
    try:
        base_path = "/app/files/ContentForDepartment"
        
        if not os.path.exists(base_path):
            return {
                "base_path": base_path,
                "exists": False,
                "departments": [],
                "message": "Базовая директория не существует"
            }
        
        departments = []
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                # Подсчитываем файлы в директории
                file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                departments.append({
                    "department_id": item,
                    "file_count": file_count,
                    "path": item_path
                })
        
        return {
            "base_path": base_path,
            "exists": True,
            "departments": departments,
            "total_departments": len(departments),
            "message": f"Найдено {len(departments)} отделов"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка отделов: {str(e)}") 

@router.get("/view-token/{content_id}")
@limiter.limit("50/minute")  # ✅ Умеренный лимит для получения токенов
async def get_view_token(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Генерирует временный токен для просмотра документа
    """
    # Получаем контент из базы данных по ID
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Контент не найден")

    # Проверяем права доступа текущего пользователя
    if not (is_admin(current_user) or (
        current_user.access_id == content.access_level and current_user.department_id == content.department_id
    )):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра документа")

    # Генерируем временный токен
    import base64
    import json
    from datetime import datetime
    
    token_data = {
        'user_id': current_user.id,
        'content_id': content_id,
        'timestamp': datetime.now().isoformat()
    }
    
    token = base64.b64encode(json.dumps(token_data).encode('utf-8')).decode('utf-8')
    
    return {"view_token": token}


@router.get("/public-view/{content_id}")
@limiter.limit("100/minute")  # ✅ Высокий лимит для просмотра документов
async def public_view_document(
    request: Request,
    content_id: int,
    token: str = Query(..., description="Временный токен для просмотра"),
    search_query: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Публичный эндпоинт для просмотра документов с временным токеном.
    Используется для просмотра через window.open
    """
    try:
        # Декодируем токен
        import base64
        import json
        from datetime import datetime, timedelta
        
        try:
            # Декодируем токен
            decoded_token = base64.b64decode(token).decode('utf-8')
            token_data = json.loads(decoded_token)
            
            # Проверяем срок действия токена (1 час)
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if datetime.now() - token_time > timedelta(hours=1):
                raise HTTPException(status_code=401, detail="Токен истек")
                
            user_id = token_data['user_id']
            content_id_from_token = token_data['content_id']
            
            # Проверяем соответствие content_id
            if content_id_from_token != content_id:
                raise HTTPException(status_code=401, detail="Неверный токен")
                
        except Exception as e:
            raise HTTPException(status_code=401, detail="Неверный токен")
        
        # Получаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        
        # Получаем контент из базы данных
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Проверяем доступ пользователя к документу
        if not (is_admin(user) or (
            user.access_id == content.access_level and user.department_id == content.department_id
        )):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра документа")

        # Получаем расширение файла
        file_extension = content.file_path.lower().split('.')[-1] if '.' in content.file_path else ''
        
        # Определяем URL для скачивания файла
        base_url = str(request.base_url).rstrip('/')
        download_url = f"{base_url}/content/public-download/{content_id}?token={token}"
        
        # Поддерживаемые форматы для просмотра с выделением
        text_formats = ['txt', 'md', 'html']
        
        # Поддерживаемые форматы для Google Docs Viewer
        supported_formats = ['doc', 'docx', 'pdf', 'ppt', 'pptx', 'xls', 'xlsx', 'rtf']
        
        if file_extension in text_formats:
            # Для текстовых файлов используем просмотр с выделением
            try:
                file_path = os.path.join("documents", content.file_path)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                else:
                    file_content = f"Файл {content.file_path} не найден на сервере."
            except Exception as e:
                file_content = f"Ошибка при чтении файла: {str(e)}"
            
            # Выделяем найденные отрывки, если есть поисковый запрос
            if search_query:
                import re
                pattern = re.compile(f'({re.escape(search_query)})', re.IGNORECASE)
                file_content = pattern.sub(r'<mark>\1</mark>', file_content)
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.title} - Просмотр документа</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #f8f9fa;
                    }}
                    .header {{
                        background: #ffffff;
                        padding: 15px 20px;
                        border-bottom: 1px solid #dee2e6;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 20px;
                        color: #333;
                        font-weight: 600;
                    }}
                    .header .controls {{
                        display: flex;
                        gap: 10px;
                    }}
                    .btn {{
                        padding: 8px 16px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 14px;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }}
                    .btn-primary {{
                        background: #007bff;
                        color: white;
                    }}
                    .btn-primary:hover {{
                        background: #0056b3;
                    }}
                    .btn-secondary {{
                        background: #6c757d;
                        color: white;
                    }}
                    .btn-secondary:hover {{
                        background: #545b62;
                    }}
                    .content-info {{
                        background: #e7f3ff;
                        border: 1px solid #b3d9ff;
                        color: #004085;
                        padding: 12px 20px;
                        border-radius: 6px;
                        margin: 15px 20px;
                        font-size: 14px;
                    }}
                    .document-content {{
                        background: white;
                        margin: 15px 20px;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        line-height: 1.6;
                        font-size: 16px;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        max-height: calc(100vh - 200px);
                        overflow-y: auto;
                    }}
                    mark {{
                        background-color: #ffeb3b;
                        color: #000;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-weight: bold;
                    }}
                    .search-info {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        color: #856404;
                        padding: 10px 20px;
                        border-radius: 6px;
                        margin: 15px 20px;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{content.title}</h1>
                    <div class="controls">
                        <a href="{download_url}" class="btn btn-primary" download>Скачать</a>
                        <button onclick="window.close()" class="btn btn-secondary">Закрыть</button>
                    </div>
                </div>
                <div class="content-info">
                    <strong>Формат файла:</strong> {file_extension.upper()}
                    <br><strong>Размер:</strong> {len(file_content)} символов
                    {f'<br><strong>Поисковый запрос:</strong> {search_query}' if search_query else ''}
                </div>
                {f'<div class="search-info"><strong>Найдено выделений:</strong> {file_content.count("<mark>")} совпадений</div>' if search_query else ''}
                <div class="document-content">{file_content}</div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        elif file_extension in supported_formats:
            # Используем Google Docs Viewer для поддерживаемых форматов
            google_docs_url = f"https://docs.google.com/viewer?url={download_url}&embedded=true"
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.title} - Просмотр документа</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: Arial, sans-serif;
                        background-color: #f5f5f5;
                    }}
                    .header {{
                        background: #f8f9fa;
                        padding: 15px 20px;
                        border-bottom: 1px solid #dee2e6;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 18px;
                        color: #333;
                    }}
                    .header .controls {{
                        display: flex;
                        gap: 10px;
                    }}
                    .btn {{
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 14px;
                    }}
                    .btn-primary {{
                        background: #007bff;
                        color: white;
                    }}
                    .btn-secondary {{
                        background: #6c757d;
                        color: white;
                    }}
                    .google-docs-info {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        color: #856404;
                        padding: 10px;
                        border-radius: 4px;
                        margin: 10px 20px;
                    }}
                    #viewer {{
                        width: 100%;
                        height: calc(100vh - 80px);
                        border: none;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{content.title}</h1>
                    <div class="controls">
                        <a href="{download_url}" class="btn btn-primary" download>Скачать</a>
                        <button onclick="window.close()" class="btn btn-secondary">Закрыть</button>
                    </div>
                </div>
                <div class="google-docs-info">
                    <strong>Информация:</strong> Документ отображается через Google Docs Viewer. 
                    Если документ не загружается, попробуйте скачать его.
                </div>
                <iframe id="viewer" src="{google_docs_url}"></iframe>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        else:
            # Для неподдерживаемых форматов предлагаем скачать
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.title} - Скачать документ</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        max-width: 500px;
                        margin: 0 auto;
                    }}
                    .btn {{
                        padding: 12px 24px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 16px;
                        margin: 10px;
                    }}
                    .btn-primary {{
                        background: #007bff;
                        color: white;
                    }}
                    .btn-secondary {{
                        background: #6c757d;
                        color: white;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>{content.title}</h2>
                    <p>Формат файла (.{file_extension}) не поддерживается для просмотра в браузере.</p>
                    <p>Пожалуйста, скачайте файл для просмотра.</p>
                    <div>
                        <a href="{download_url}" class="btn btn-primary" download>Скачать документ</a>
                        <button onclick="window.close()" class="btn btn-secondary">Закрыть</button>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании страницы просмотра: {str(e)}") 