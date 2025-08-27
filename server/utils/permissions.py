#!/usr/bin/env python3
"""
Модуль для проверки прав доступа пользователей
Реализует систему ролей: Админ, Пользователь, Глава отдела, Ответственный отдела
"""

from typing import Optional
from sqlalchemy.orm import Session
from models_db import User, Content, ContentProposal, Department

# Константы ролей
ROLE_ADMIN = 1
ROLE_USER = 2
ROLE_DEPARTMENT_HEAD = 3
ROLE_DEPARTMENT_RESPONSIBLE = 4

class PermissionChecker:
    """Класс для проверки прав доступа пользователей"""
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user.role_id == ROLE_ADMIN
    
    @staticmethod
    def is_department_head(user: User) -> bool:
        """Проверяет, является ли пользователь главой отдела"""
        return user.role_id == ROLE_DEPARTMENT_HEAD
    
    @staticmethod
    def is_department_responsible(user: User) -> bool:
        """Проверяет, является ли пользователь ответственным отдела"""
        return user.role_id == ROLE_DEPARTMENT_RESPONSIBLE
    
    @staticmethod
    def is_regular_user(user: User) -> bool:
        """Проверяет, является ли пользователь обычным пользователем"""
        return user.role_id == ROLE_USER
    
    @staticmethod
    def can_manage_users(user: User, target_user: Optional[User] = None) -> bool:
        """
        Проверяет, может ли пользователь управлять пользователями
        
        Админ: может управлять всеми пользователями
        Глава отдела: может создавать только пользователей с ролью "Пользователь" для своего отдела
        """
        if PermissionChecker.is_admin(user):
            return True
        
        if PermissionChecker.is_department_head(user):
            # Глава отдела может управлять только пользователями своего отдела
            if target_user and target_user.department_id != user.department_id:
                return False
            # Глава отдела может создавать только пользователей с ролью "Пользователь"
            if target_user and target_user.role_id != ROLE_USER:
                return False
            return True
        
        return False
    
    @staticmethod
    def can_manage_content(user: User, content: Optional[Content] = None) -> bool:
        """
        Проверяет, может ли пользователь управлять контентом
        
        Админ: может управлять всем контентом
        Глава отдела: может управлять контентом только своего отдела
        """
        if PermissionChecker.is_admin(user):
            return True
        
        if PermissionChecker.is_department_head(user):
            # Глава отдела может управлять только контентом своего отдела
            if content and content.department_id != user.department_id:
                return False
            return True
        
        return False
    
    @staticmethod
    def can_view_content(user: User, content: Content) -> bool:
        """
        Проверяет, может ли пользователь просматривать контент
        
        Админ: может просматривать весь контент
        Глава отдела: может просматривать контент своего отдела
        Пользователь/Ответственный: может просматривать контент своего отдела и уровня доступа
        """
        if PermissionChecker.is_admin(user):
            return True
        
        if PermissionChecker.is_department_head(user):
            # Глава отдела может просматривать контент своего отдела
            return content.department_id == user.department_id
        
        # Пользователь и ответственный отдела могут просматривать контент своего отдела и уровня доступа
        return (content.department_id == user.department_id and 
                content.access_level == user.access_id)
    
    @staticmethod
    def can_propose_content(user: User) -> bool:
        """
        Проверяет, может ли пользователь предлагать контент
        
        Админ: может предлагать контент
        Ответственный отдела: может предлагать контент
        """
        return PermissionChecker.is_admin(user) or PermissionChecker.is_department_responsible(user)
    
    @staticmethod
    def can_review_proposals(user: User, proposal: Optional[ContentProposal] = None) -> bool:
        """
        Проверяет, может ли пользователь рассматривать предложения контента
        
        Админ: может рассматривать все предложения
        Глава отдела: может рассматривать предложения только своего отдела
        """
        if PermissionChecker.is_admin(user):
            return True
        
        if PermissionChecker.is_department_head(user):
            # Глава отдела может рассматривать предложения только своего отдела
            if proposal and proposal.department_id != user.department_id:
                return False
            return True
        
        return False
    
    @staticmethod
    def can_manage_llm(user: User) -> bool:
        """
        Проверяет, может ли пользователь управлять LLM системой
        
        Только админ может управлять LLM
        """
        return PermissionChecker.is_admin(user)
    
    @staticmethod
    def can_view_feedback(user: User) -> bool:
        """
        Проверяет, может ли пользователь просматривать обратную связь
        
        Админ: может просматривать всю обратную связь
        """
        return PermissionChecker.is_admin(user)
    
    @staticmethod
    def can_send_feedback(user: User) -> bool:
        """
        Проверяет, может ли пользователь отправлять обратную связь
        
        Все авторизованные пользователи могут отправлять обратную связь
        """
        return True
    
    @staticmethod
    def can_take_quizzes(user: User) -> bool:
        """
        Проверяет, может ли пользователь проходить тесты и анкеты
        
        Все авторизованные пользователи могут проходить тесты и анкеты
        """
        return True
    
    @staticmethod
    def can_create_quizzes(user: User) -> bool:
        """
        Проверяет, может ли пользователь создавать тесты и анкеты
        
        Только админ может создавать тесты и анкеты
        """
        return PermissionChecker.is_admin(user)
    
    @staticmethod
    def get_user_role_name(user: User) -> str:
        """Возвращает название роли пользователя"""
        role_names = {
            ROLE_ADMIN: "Админ",
            ROLE_USER: "Пользователь", 
            ROLE_DEPARTMENT_HEAD: "Глава отдела",
            ROLE_DEPARTMENT_RESPONSIBLE: "Ответственный отдела"
        }
        return role_names.get(user.role_id, "Неизвестная роль")
    
    @staticmethod
    def get_user_permissions(user: User) -> dict:
        """Возвращает список разрешений пользователя"""
        return {
            "can_manage_users": PermissionChecker.can_manage_users(user),
            "can_manage_content": PermissionChecker.can_manage_content(user),
            "can_propose_content": PermissionChecker.can_propose_content(user),
            "can_review_proposals": PermissionChecker.can_review_proposals(user),
            "can_manage_llm": PermissionChecker.can_manage_llm(user),
            "can_view_feedback": PermissionChecker.can_view_feedback(user),
            "can_send_feedback": PermissionChecker.can_send_feedback(user),
            "can_take_quizzes": PermissionChecker.can_take_quizzes(user),
            "can_create_quizzes": PermissionChecker.can_create_quizzes(user),
            "role_name": PermissionChecker.get_user_role_name(user)
        }
