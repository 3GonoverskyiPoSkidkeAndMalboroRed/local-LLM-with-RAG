#!/usr/bin/env python3
"""
Маршруты для работы с предложениями контента
Реализует систему предложения-одобрения контента
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
import os
import shutil

from database import get_db
from models_db import User, ContentProposal, Content, Department, Access, Tag
from routes.user_routes import get_current_user, oauth2_scheme
from utils.permissions import PermissionChecker

router = APIRouter(prefix="/proposals", tags=["proposals"])
limiter = Limiter(key_func=get_remote_address)

# Pydantic модели для запросов и ответов
class ProposalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    access_level: int
    department_id: int
    tag_id: Optional[int] = None

class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    access_level: Optional[int] = None
    department_id: Optional[int] = None
    tag_id: Optional[int] = None

class ProposalReview(BaseModel):
    status: str  # 'approved' или 'rejected'
    review_comment: Optional[str] = None

from datetime import datetime

class ProposalResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    access_level: int
    department_id: int
    tag_id: Optional[int]
    proposed_by: int
    status: str
    reviewed_by: Optional[int]
    review_comment: Optional[str]
    created_at: str
    updated_at: Optional[str]
    file_path: Optional[str] = None  # Добавляем путь к файлу
    
    # Дополнительная информация
    proposer_name: Optional[str] = None
    reviewer_name: Optional[str] = None
    department_name: Optional[str] = None
    access_name: Optional[str] = None
    tag_name: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Преобразуем datetime в строку
        data = {
            'id': obj.id,
            'title': obj.title,
            'description': obj.description,
            'access_level': obj.access_level,
            'department_id': obj.department_id,
            'tag_id': obj.tag_id,
            'proposed_by': obj.proposed_by,
            'status': obj.status,
            'reviewed_by': obj.reviewed_by,
            'review_comment': obj.review_comment,
            'created_at': obj.created_at.isoformat() if obj.created_at else None,
            'updated_at': obj.updated_at.isoformat() if obj.updated_at else None,
            'file_path': getattr(obj, 'file_path', None),  # Добавляем путь к файлу
        }
        return cls(**data)

@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_proposal(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    access_level: int = Form(...),
    department_id: int = Form(...),
    tag_id: Optional[int] = Form(None),
    file: UploadFile = File(...),  # Добавляем загрузку файла
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание предложения контента с файлом"""
    
    # Проверяем права на создание предложений
    if not PermissionChecker.can_propose_content(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания предложений контента"
        )
    
    # Проверяем, что отдел существует
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отдел не найден"
        )
    
    # Проверяем, что уровень доступа существует
    access = db.query(Access).filter(Access.id == access_level).first()
    if not access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уровень доступа не найден"
        )
    
    # Проверяем тег, если указан
    if tag_id:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тег не найден"
            )
    
    # Создаем директорию для предложений
    proposals_dir = "/app/files/proposals"
    os.makedirs(proposals_dir, exist_ok=True)
    
    # Сохраняем файл во временную директорию предложений
    file_path = os.path.join(proposals_dir, f"proposal_{current_user.id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении файла: {str(e)}"
        )
    
    # Создаем предложение
    proposal = ContentProposal(
        title=title,
        description=description,
        access_level=access_level,
        department_id=department_id,
        tag_id=tag_id,
        proposed_by=current_user.id,
        status='pending',
        file_path=file_path  # Сохраняем путь к файлу
    )
    
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    # Создаем ответ с дополнительной информацией
    proposer = db.query(User).filter(User.id == proposal.proposed_by).first()
    department = db.query(Department).filter(Department.id == proposal.department_id).first()
    access = db.query(Access).filter(Access.id == proposal.access_level).first()
    
    response_data = {
        'id': proposal.id,
        'title': proposal.title,
        'description': proposal.description,
        'access_level': proposal.access_level,
        'department_id': proposal.department_id,
        'tag_id': proposal.tag_id,
        'proposed_by': proposal.proposed_by,
        'status': proposal.status,
        'reviewed_by': proposal.reviewed_by,
        'review_comment': proposal.review_comment,
        'created_at': proposal.created_at.isoformat() if proposal.created_at else None,
        'updated_at': proposal.updated_at.isoformat() if proposal.updated_at else None,
        'file_path': proposal.file_path,
        'proposer_name': proposer.full_name if proposer else None,
        'department_name': department.department_name if department else None,
        'access_name': access.access_name if access else None,
    }
    
    return response_data

@router.get("/")
@limiter.limit("30/minute")
async def get_proposals(
    request: Request,
    status_filter: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка предложений контента"""
    
    # Базовый запрос
    query = db.query(ContentProposal)
    
    # Фильтруем по правам доступа
    if not PermissionChecker.is_admin(current_user):
        if PermissionChecker.is_department_head(current_user):
            # Глава отдела видит предложения только своего отдела
            query = query.filter(ContentProposal.department_id == current_user.department_id)
        else:
            # Обычные пользователи видят только свои предложения
            query = query.filter(ContentProposal.proposed_by == current_user.id)
    
    # Применяем фильтры
    if status_filter:
        query = query.filter(ContentProposal.status == status_filter)
    
    if department_id:
        query = query.filter(ContentProposal.department_id == department_id)
    
    proposals = query.all()
    
    # Формируем ответ с дополнительной информацией
    result = []
    for proposal in proposals:
        proposer = db.query(User).filter(User.id == proposal.proposed_by).first()
        reviewer = None
        if proposal.reviewed_by:
            reviewer = db.query(User).filter(User.id == proposal.reviewed_by).first()
        
        department = db.query(Department).filter(Department.id == proposal.department_id).first()
        access = db.query(Access).filter(Access.id == proposal.access_level).first()
        tag = None
        if proposal.tag_id:
            tag = db.query(Tag).filter(Tag.id == proposal.tag_id).first()
        
        result.append(ProposalResponse(
            id=proposal.id,
            title=proposal.title,
            description=proposal.description,
            access_level=proposal.access_level,
            department_id=proposal.department_id,
            tag_id=proposal.tag_id,
            proposed_by=proposal.proposed_by,
            status=proposal.status,
            reviewed_by=proposal.reviewed_by,
            review_comment=proposal.review_comment,
            created_at=proposal.created_at.isoformat() if proposal.created_at else None,
            updated_at=proposal.updated_at.isoformat() if proposal.updated_at else None,
            file_path=proposal.file_path,
            proposer_name=proposer.full_name if proposer else None,
            reviewer_name=reviewer.full_name if reviewer else None,
            department_name=department.department_name if department else None,
            access_name=access.access_name if access else None,
            tag_name=tag.tag_name if tag else None
        ))
    
    return result

@router.get("/{proposal_id}")
@limiter.limit("30/minute")
async def get_proposal(
    request: Request,
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение конкретного предложения контента"""
    
    proposal = db.query(ContentProposal).filter(ContentProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предложение не найдено"
        )
    
    # Проверяем права доступа
    if not PermissionChecker.is_admin(current_user):
        if PermissionChecker.is_department_head(current_user):
            if proposal.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для просмотра этого предложения"
                )
        else:
            if proposal.proposed_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для просмотра этого предложения"
                )
    
    # Получаем дополнительную информацию
    proposer = db.query(User).filter(User.id == proposal.proposed_by).first()
    reviewer = None
    if proposal.reviewed_by:
        reviewer = db.query(User).filter(User.id == proposal.reviewed_by).first()
    
    department = db.query(Department).filter(Department.id == proposal.department_id).first()
    access = db.query(Access).filter(Access.id == proposal.access_level).first()
    tag = None
    if proposal.tag_id:
        tag = db.query(Tag).filter(Tag.id == proposal.tag_id).first()
    
    return ProposalResponse(
        id=proposal.id,
        title=proposal.title,
        description=proposal.description,
        access_level=proposal.access_level,
        department_id=proposal.department_id,
        tag_id=proposal.tag_id,
        proposed_by=proposal.proposed_by,
        status=proposal.status,
        reviewed_by=proposal.reviewed_by,
        review_comment=proposal.review_comment,
        created_at=proposal.created_at,
        updated_at=proposal.updated_at,
        file_path=proposal.file_path,
        proposer_name=proposer.full_name if proposer else None,
        reviewer_name=reviewer.full_name if reviewer else None,
        department_name=department.department_name if department else None,
        access_name=access.access_name if access else None,
        tag_name=tag.tag_name if tag else None
    )

@router.put("/{proposal_id}/review")
@limiter.limit("10/minute")
async def review_proposal(
    request: Request,
    proposal_id: int,
    review_data: ProposalReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Рассмотрение предложения контента"""
    
    proposal = db.query(ContentProposal).filter(ContentProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предложение не найдено"
        )
    
    # Проверяем права на рассмотрение
    if not PermissionChecker.can_review_proposals(current_user, proposal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для рассмотрения этого предложения"
        )
    
    # Проверяем статус предложения
    if proposal.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Предложение уже рассмотрено"
        )
    
    # Обновляем статус предложения
    proposal.status = review_data.status
    proposal.reviewed_by = current_user.id
    proposal.review_comment = review_data.review_comment
    
    db.commit()
    db.refresh(proposal)
    
    # Если предложение одобрено, создаем контент и перемещаем файл
    if review_data.status == 'approved':
        # Создаем директорию для контента отдела
        content_dir = f"/app/files/ContentForDepartment/{proposal.department_id}"
        os.makedirs(content_dir, exist_ok=True)
        
        # Перемещаем файл из временной директории предложений в постоянную
        if proposal.file_path and os.path.exists(proposal.file_path):
            filename = os.path.basename(proposal.file_path)
            new_file_path = os.path.join(content_dir, filename)
            
            try:
                shutil.move(proposal.file_path, new_file_path)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка при перемещении файла: {str(e)}"
                )
        else:
            new_file_path = ""
        
        content = Content(
            title=proposal.title,
            description=proposal.description,
            file_path=new_file_path,
            access_level=proposal.access_level,
            department_id=proposal.department_id,
            tag_id=proposal.tag_id,
            creator_id=proposal.proposed_by,
            status='active'
        )
        db.add(content)
        db.commit()
    
    return proposal

@router.delete("/{proposal_id}")
@limiter.limit("5/minute")
async def delete_proposal(
    request: Request,
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление предложения контента"""
    
    proposal = db.query(ContentProposal).filter(ContentProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предложение не найдено"
        )
    
    # Проверяем права на удаление
    if not PermissionChecker.is_admin(current_user) and proposal.proposed_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого предложения"
        )
    
    # Удаляем файл, если он существует
    if proposal.file_path and os.path.exists(proposal.file_path):
        try:
            os.remove(proposal.file_path)
        except Exception as e:
            print(f"Ошибка при удалении файла: {str(e)}")
    
    db.delete(proposal)
    db.commit()
    
    return {"message": "Предложение успешно удалено"}

@router.get("/{proposal_id}/download")
@limiter.limit("30/minute")
async def download_proposal_file(
    request: Request,
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Скачивание файла предложения"""
    
    proposal = db.query(ContentProposal).filter(ContentProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Предложение не найдено"
        )
    
    # Проверяем права доступа
    if not PermissionChecker.is_admin(current_user):
        if PermissionChecker.is_department_head(current_user):
            if proposal.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для скачивания этого файла"
                )
        else:
            if proposal.proposed_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для скачивания этого файла"
                )
    
    if not proposal.file_path or not os.path.exists(proposal.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=proposal.file_path,
        filename=os.path.basename(proposal.file_path),
        media_type='application/octet-stream'
    )
