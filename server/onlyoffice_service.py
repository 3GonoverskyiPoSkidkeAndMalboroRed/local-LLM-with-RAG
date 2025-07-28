import os
import jwt
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException
import hashlib
import uuid

class OnlyOfficeService:
    def __init__(self):
        self.jwt_secret = os.environ.get("ONLYOFFICE_JWT_SECRET", "your-secret-key-here")
        self.onlyoffice_url = os.environ.get("ONLYOFFICE_URL", "http://onlyoffice:80")
        self.api_url = os.environ.get("API_URL", "http://backend:8000")
        # URL для внешнего доступа (через nginx)
        self.external_url = os.environ.get("EXTERNAL_URL", "http://nginx:80")
        
    def generate_jwt_token(self, payload: Dict[str, Any]) -> str:
        """Генерирует JWT токен для OnlyOffice"""
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def create_document_config(self, 
                              file_path: str, 
                              file_name: str, 
                              file_id: str,
                              user_id: int,
                              user_name: str = "Пользователь",
                              mode: str = "view") -> Dict[str, Any]:
        """
        Создает конфигурацию документа для OnlyOffice
        
        Args:
            file_path: Путь к файлу на сервере
            file_name: Имя файла
            file_id: Уникальный ID файла
            user_id: ID пользователя
            user_name: Имя пользователя
            mode: Режим работы (view, edit, comment)
        """
        
        # Генерируем уникальный ключ для документа
        document_key = hashlib.md5(f"{file_id}_{user_id}".encode()).hexdigest()
        
        # Создаем URL для загрузки файла (используем публичный URL)
        download_url = f"http://localhost:8081/content/download-file/{file_id}"
        
        # Создаем URL для сохранения файла (используем публичный URL)
        save_url = f"http://localhost:8081/content/save-onlyoffice/{file_id}"
        
        config = {
            "document": {
                "fileType": self._get_file_type(file_name),
                "key": document_key,
                "title": file_name,
                "url": download_url,
                "permissions": {
                    "download": True,
                    "edit": mode in ["edit", "comment"],
                    "print": True,
                    "review": mode in ["edit", "comment"]
                }
            },
            "documentType": self._get_document_type(file_name),
            "editorConfig": {
                "mode": mode,
                "lang": "ru",
                "callbackUrl": save_url,
                "user": {
                    "id": str(user_id),
                    "name": user_name
                },
                "customization": {
                    "autosave": True,
                    "forcesave": True,
                    "chat": True,
                    "comments": True,
                    "compactHeader": False,
                    "feedback": False,
                    "help": True,
                    "integrationMode": "embed"
                }
            },
            "height": "100%",
            "width": "100%"
        }
        
        return config
    
    def _get_file_type(self, file_name: str) -> str:
        """Определяет тип файла по расширению"""
        ext = file_name.lower().split('.')[-1]
        file_types = {
            'doc': 'doc',
            'docx': 'docx',
            'odt': 'odt',
            'rtf': 'rtf',
            'txt': 'txt',
            'pdf': 'pdf',
            'xls': 'xls',
            'xlsx': 'xlsx',
            'ods': 'ods',
            'ppt': 'ppt',
            'pptx': 'pptx',
            'odp': 'odp'
        }
        return file_types.get(ext, 'docx')
    
    def _get_document_type(self, file_name: str) -> str:
        """Определяет тип документа по расширению"""
        ext = file_name.lower().split('.')[-1]
        if ext in ['doc', 'docx', 'odt', 'rtf', 'txt']:
            return 'text'
        elif ext in ['xls', 'xlsx', 'ods']:
            return 'spreadsheet'
        elif ext in ['ppt', 'pptx', 'odp']:
            return 'presentation'
        else:
            return 'text'
    
    def verify_callback(self, token: str, body: Dict[str, Any]) -> bool:
        """Проверяет подлинность callback от OnlyOffice"""
        try:
            # Декодируем JWT токен
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Проверяем статус
            if body.get('status') == 2:  # Статус 2 означает, что документ готов к сохранению
                return True
                
            return False
        except jwt.InvalidTokenError:
            return False
    
    def get_editor_url(self, config: Dict[str, Any]) -> str:
        """Возвращает URL для встраивания редактора"""
        config_json = json.dumps(config)
        return f"{self.onlyoffice_url}/web-apps/apps/api/documents/api.js"
    
    def create_editor_config(self, config: Dict[str, Any]) -> str:
        """Создает JavaScript конфигурацию для редактора"""
        config_json = json.dumps(config)
        return f"""
        new DocsAPI.DocEditor("placeholder", {config_json});
        """

# Создаем глобальный экземпляр сервиса
onlyoffice_service = OnlyOfficeService() 