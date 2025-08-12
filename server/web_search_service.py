import os
import logging
from typing import List, Dict, Any, Optional

from yandex_cloud_ml_sdk import AsyncYCloudML


logger = logging.getLogger(__name__)


class WebSearchService:
    """
    Сервис генеративного поиска через Yandex Cloud ML SDK.
    
    Использует search_api.generative для получения сгенерированных ИИ ответов
    на основе веб-поиска. Авторизация через отдельные ключи Search API.
    """

    def __init__(self) -> None:
        # Креды для Search API (отдельные от основного SDK)
        self.search_api_key = os.getenv('SEARCH_API_API_KEY')
        self.search_iam_token = os.getenv('SEARCH_API_IAM_TOKEN')
        self.folder_id = os.getenv('YC_FOLDER_ID') or os.getenv('YANDEX_FOLDER_ID')
        
        # SDK клиент
        self.ml_client: Optional[AsyncYCloudML] = None
        self._initialized = False
        
        # Инициализируем SDK
        self._initialize_sdk()

    def _initialize_sdk(self) -> None:
        """Инициализирует Yandex Cloud ML SDK для поиска"""
        auth_key = self.search_api_key or self.search_iam_token
        
        if auth_key and self.folder_id:
            try:
                self.ml_client = AsyncYCloudML(
                    folder_id=self.folder_id,
                    auth=auth_key
                )
                self._initialized = True
                logger.info("Yandex Cloud ML SDK для поиска инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации SDK: {e}")
                self.ml_client = None
                self._initialized = False
        else:
            logger.warning("SDK не инициализирован - отсутствуют параметры")
            self._initialized = False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._initialize_sdk()
        if not self.ml_client:
            raise RuntimeError("Yandex Cloud ML SDK не инициализирован")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Выполняет генеративный поиск через Yandex Cloud ML SDK search_api.generative
        и возвращает сгенерированный ИИ ответ на основе поиска.
        """
        self._ensure_initialized()
        
        try:
            search_obj = self.ml_client.search_api.generative(site="yandex.ru")
            search_result = await search_obj.run(query)
            
            # Извлекаем сгенерированный ответ
            if hasattr(search_result, 'text'):
                generated_text = search_result.text
            elif hasattr(search_result, 'content'):
                generated_text = search_result.content
            elif hasattr(search_result, 'response'):
                generated_text = search_result.response
            elif hasattr(search_result, 'answer'):
                generated_text = search_result.answer
            else:
                generated_text = str(search_result)
            
            # Создаем результат с сгенерированным ответом
            results = [{
                "title": f"Ответ на запрос: {query}",
                "url": "",
                "snippet": generated_text,
                "generated_response": True,
                "query": query
            }]

            return results

        except Exception as e:
            logger.error(f"Ошибка генеративного поиска: {e}")
            raise RuntimeError(f"Ошибка генеративного поиска: {e}")


# Singleton
web_search_service = WebSearchService()
