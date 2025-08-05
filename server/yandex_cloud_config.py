import os
from typing import Optional
from yandexcloud import SDK
import logging

logger = logging.getLogger(__name__)

class YandexCloudConfig:
    def __init__(self):
        self.sdk: Optional[SDK] = None
        self.folder_id: Optional[str] = None
        self.cloud_id: Optional[str] = None
        self.initialized: bool = False
        
    def initialize(self, 
                   service_account_key_path: Optional[str] = None,
                   folder_id: Optional[str] = None,
                   cloud_id: Optional[str] = None) -> bool:
        """
        Инициализация Yandex Cloud SDK
        
        Args:
            service_account_key_path: Путь к файлу ключа сервисного аккаунта
            folder_id: ID папки в Yandex Cloud
            cloud_id: ID облака в Yandex Cloud
            
        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            # Инициализация SDK
            if service_account_key_path and os.path.exists(service_account_key_path):
                self.sdk = SDK(service_account_key=service_account_key_path)
                logger.info(f"Yandex Cloud SDK инициализирован с ключом: {service_account_key_path}")
            else:
                # Использование переменных окружения
                self.sdk = SDK()
                logger.info("Yandex Cloud SDK инициализирован с переменными окружения")
            
            self.folder_id = folder_id or os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID')
            self.cloud_id = cloud_id or os.getenv('YC_CLOUD_ID')
            
            if not self.sdk:
                raise ValueError("Не удалось инициализировать Yandex Cloud SDK")
            
            self.initialized = True
            logger.info(f"Yandex Cloud SDK успешно инициализирован. Folder ID: {self.folder_id}, Cloud ID: {self.cloud_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Yandex Cloud SDK: {e}")
            self.initialized = False
            return False
    
    def get_sdk(self) -> Optional[SDK]:
        """Получить экземпляр SDK"""
        return self.sdk if self.initialized else None
    
    def get_folder_id(self) -> Optional[str]:
        """Получить ID папки"""
        return self.folder_id
    
    def get_cloud_id(self) -> Optional[str]:
        """Получить ID облака"""
        return self.cloud_id
    
    def is_initialized(self) -> bool:
        """Проверить, инициализирован ли SDK"""
        return self.initialized

# Глобальный экземпляр конфигурации
yandex_cloud_config = YandexCloudConfig() 