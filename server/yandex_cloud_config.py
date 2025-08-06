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
        self.api_key: Optional[str] = None
        self.initialized: bool = False
        
    def initialize(self, 
                   service_account_key_path: Optional[str] = None,
                   folder_id: Optional[str] = None,
                   cloud_id: Optional[str] = None,
                   api_key: Optional[str] = None) -> bool:
        """
        Инициализация Yandex Cloud SDK
        
        Args:
            service_account_key_path: Путь к файлу ключа сервисного аккаунта
            folder_id: ID папки в Yandex Cloud
            cloud_id: ID облака в Yandex Cloud
            api_key: API ключ для аутентификации
            
        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            # Получаем переменные окружения
            self.api_key = api_key or os.getenv('YANDEX_API_KEY') or os.getenv('YC_API_KEY')
            self.folder_id = folder_id or os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID')
            self.cloud_id = cloud_id or os.getenv('YC_CLOUD_ID')
            
            # Проверяем наличие необходимых переменных
            if not self.api_key:
                logger.warning("API ключ не найден. Проверьте переменные YANDEX_API_KEY или YC_API_KEY")
                return False
                
            if not self.folder_id:
                logger.warning("Folder ID не найден. Проверьте переменные YANDEX_FOLDER_ID или YC_FOLDER_ID")
                return False
            
            # Инициализация SDK
            if service_account_key_path and os.path.exists(service_account_key_path):
                self.sdk = SDK(service_account_key=service_account_key_path)
                logger.info(f"Yandex Cloud SDK инициализирован с ключом: {service_account_key_path}")
            else:
                # Использование переменных окружения
                self.sdk = SDK()
                logger.info("Yandex Cloud SDK инициализирован с переменными окружения")
            
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
    
    def get_api_key(self) -> Optional[str]:
        """Получить API ключ"""
        return self.api_key
    
    def is_initialized(self) -> bool:
        """Проверить, инициализирован ли SDK"""
        return self.initialized

# Глобальный экземпляр конфигурации
yandex_cloud_config = YandexCloudConfig() 