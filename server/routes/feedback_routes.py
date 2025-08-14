from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, status
import os
from sqlalchemy.orm import Session
from database import get_db
from models_db import Feedback, User
from pydantic import BaseModel
from fastapi.responses import FileResponse, Response
from typing import List, Optional
import base64
from io import BytesIO
# ✅ Добавляем импорт для аутентификации
from routes.user_routes import require_admin, get_current_user, is_admin

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    # ✅ Убираем user_id из модели - будет использоваться текущий пользователь
    text: str

@router.post("/create")
async def create_feedback(
    # ✅ Убираем user_id из параметров
    text: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию
    current_user: User = Depends(get_current_user)
):
    """
    Создает новое сообщение обратной связи с возможностью прикрепления фото
    """
    try:
        # ✅ Используем текущего пользователя вместо user_id из формы
        user = current_user
        
        # Обрабатываем фото, если оно предоставлено
        photo_data = None
        if photo:
            # ✅ Добавляем валидацию файла
            if photo.size and photo.size > 5 * 1024 * 1024:  # 5MB лимит
                raise HTTPException(status_code=400, detail="Размер файла превышает 5MB")
            
            # Проверяем тип файла
            allowed_types = ["image/jpeg", "image/png", "image/gif"]
            if photo.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла. Разрешены только JPEG, PNG, GIF")
            
            photo_data = await photo.read()
        
        # Создаем новую запись обратной связи
        new_feedback = Feedback(
            user_id=user.id,  # ✅ Используем ID текущего пользователя
            text=text,
            photo=photo_data
        )
        
        # Сохраняем в базу данных
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        
        return {"message": "Сообщение обратной связи успешно создано", "feedback_id": new_feedback.id}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании сообщения: {str(e)}")

@router.get("/list")
async def get_feedback_list(
    db: Session = Depends(get_db),
    # ✅ Уже есть проверка на админа
    current_user = Depends(require_admin),
):
    """
    Получает список всех сообщений обратной связи (доступно только для администраторов)
    """
    try:
        # Получаем все сообщения обратной связи
        feedback_list = db.query(Feedback).order_by(Feedback.created_at.desc()).all()
        
        # Формируем ответ
        result = []
        for feedback in feedback_list:
            # Получаем информацию о пользователе
            user = db.query(User).filter(User.id == feedback.user_id).first()
            user_info = {
                "id": user.id,
                "login": user.login,
                "full_name": user.full_name
            } if user else {"id": feedback.user_id, "login": "Неизвестно", "full_name": "Неизвестно"}
            
            # Добавляем информацию о сообщении
            result.append({
                "id": feedback.id,
                "text": feedback.text,
                "created_at": feedback.created_at,
                "has_photo": feedback.photo is not None,
                "user": user_info
            })
        
        return {"feedback_list": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка сообщений: {str(e)}")

@router.get("/photo/{feedback_id}")
async def get_feedback_photo(
    feedback_id: int, 
    db: Session = Depends(get_db),
    # ✅ Уже есть проверка на админа
    current_user = Depends(require_admin),
):
    """
    Получает фото для сообщения обратной связи по его ID (только для администраторов)
    """
    try:
        # Находим сообщение по ID
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")
        
        # Проверяем наличие фото
        if not feedback.photo:
            raise HTTPException(status_code=404, detail="Фото не найдено")
        
        # Возвращаем фото
        return Response(content=feedback.photo, media_type="image/jpeg")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении фото: {str(e)}")

@router.get("/detail/{feedback_id}")
async def get_feedback_detail(
    feedback_id: int, 
    db: Session = Depends(get_db),
    # ✅ Уже есть проверка на админа
    current_user = Depends(require_admin),
):
    """
    Получает детальную информацию о сообщении обратной связи по его ID (только для администраторов)
    """
    try:
        # Находим сообщение по ID
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")
        
        # Получаем информацию о пользователе
        user = db.query(User).filter(User.id == feedback.user_id).first()
        user_info = {
            "id": user.id,
            "login": user.login,
            "full_name": user.full_name,
            "department_id": user.department_id,
            "access_id": user.access_id
        } if user else {"id": feedback.user_id, "login": "Неизвестно", "full_name": "Неизвестно"}
        
        # Формируем ответ
        result = {
            "id": feedback.id,
            "text": feedback.text,
            "created_at": feedback.created_at,
            "has_photo": feedback.photo is not None,
            "user": user_info
        }
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации о сообщении: {str(e)}")

# ✅ Добавляем новый эндпоинт для получения собственных отзывов пользователя
@router.get("/my-feedback")
async def get_my_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получает список собственных сообщений обратной связи пользователя
    """
    try:
        # Получаем отзывы текущего пользователя
        feedback_list = db.query(Feedback).filter(
            Feedback.user_id == current_user.id
        ).order_by(Feedback.created_at.desc()).all()
        
        # Формируем ответ
        result = []
        for feedback in feedback_list:
            result.append({
                "id": feedback.id,
                "text": feedback.text,
                "created_at": feedback.created_at,
                "has_photo": feedback.photo is not None
            })
        
        return {"feedback_list": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка сообщений: {str(e)}")

# ✅ Добавляем эндпоинт для удаления собственного отзыва
@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удаляет сообщение обратной связи (пользователь может удалить только свои отзывы, админ - любые)
    """
    try:
        # Находим сообщение по ID
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")
        
        # ✅ Проверяем права: пользователь может удалить только свои отзывы или админ
        if not (is_admin(current_user) or feedback.user_id == current_user.id):
            raise HTTPException(status_code=403, detail="Недостаточно прав для удаления этого сообщения")
        
        # Удаляем сообщение
        db.delete(feedback)
        db.commit()
        
        return {"message": "Сообщение успешно удалено"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении сообщения: {str(e)}")
