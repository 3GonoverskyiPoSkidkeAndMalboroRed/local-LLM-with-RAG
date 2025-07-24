import asyncio
import logging
from datetime import datetime

class OllamaMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.success_count = 0
        self.failure_count = 0
        self.last_check = datetime.now()
    
    async def log_request(self, success: bool, duration: float, model: str):
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        success_rate = self.success_count / (self.success_count + self.failure_count) * 100
        self.logger.info(f"Request to {model}: {'SUCCESS' if success else 'FAILED'}, "
                        f"Duration: {duration:.2f}s, Success Rate: {success_rate:.1f}%")
    
    async def health_check(self):
        """Проверка здоровья Ollama сервиса"""
        try:
            # Проверка доступности API
            # Проверка загруженных моделей
            # Проверка использования памяти
            pass
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}") 