import os
import asyncio
import logging
from typing import List, Dict, Any, Optional

import httpx
from bs4 import BeautifulSoup
from yandex_cloud_ml_sdk import AsyncYCloudML


logger = logging.getLogger(__name__)


class WebSearchService:
    """
    Сервис веб-поиска через Yandex Cloud ML SDK с опциональным извлечением и сжатием контента страниц.

    Использует search_api.generative из Yandex Cloud ML SDK для поиска.
    Авторизация через те же переменные, что и для основного SDK.
    """

    def __init__(self) -> None:
        # Креды для Search API (отдельные от основного SDK)
        self.search_api_key = os.getenv('SEARCH_API_API_KEY')
        self.search_iam_token = os.getenv('SEARCH_API_IAM_TOKEN')
        self.folder_id = os.getenv('YC_FOLDER_ID') or os.getenv('YANDEX_FOLDER_ID')
        
        # SDK клиент
        self.ml_client: Optional[AsyncYCloudML] = None
        self._initialized = False

        # Параметры загрузки страниц
        self.timeout = float(os.getenv("WEB_FETCH_TIMEOUT", "8"))
        self.user_agent = (
            os.getenv("WEB_FETCH_UA")
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
        )

        self._client: Optional[httpx.AsyncClient] = None
        
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

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                trust_env=True,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._initialize_sdk()
        if not self.ml_client:
            raise RuntimeError("Yandex Cloud ML SDK не инициализирован")

    async def search(self, query: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Выполняет генеративный поиск через Yandex Cloud ML SDK search_api.generative
        и возвращает сгенерированный ИИ ответ на основе поиска.
        """
        self._ensure_initialized()
        
        try:
            # Создаем объект generative search
            # Используем yandex.ru как основной источник для поиска
            search_obj = self.ml_client.search_api.generative(
                site="yandex.ru"
            )
            
            # Выполняем генеративный поиск
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

    async def fetch_page_text(self, url: str) -> str:
        client = await self._get_client()
        try:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Не удалось загрузить {url}: {e}")
            return ""

        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(" ")
        text = " ".join(text.split())
        return text[:10000]

    def compress_text(self, text: str, max_chars: int = 1200) -> str:
        if not text:
            return ""
        parts = [p.strip() for p in text.replace("\r", " ").split("\n") if p.strip()]
        if not parts:
            parts = [text]
        out: List[str] = []
        total = 0
        for p in parts:
            if total + len(p) > max_chars:
                out.append(p[: max(0, max_chars - total)])
                break
            out.append(p)
            total += len(p)
            if total >= max_chars:
                break
        return "\n".join(out)

    async def search_and_extract(
        self,
        query: str,
        top_n: int = 3,
        fetch_pages: bool = True,
        compress: bool = True,
    ) -> List[Dict[str, Any]]:
        results = await self.search(query, top_n=top_n)
        
        # Для генеративного поиска не загружаем страницы
        if results and results[0].get("generated_response"):
            return results
            
        # Для обычного поиска
        if not fetch_pages:
            return results

        sem = asyncio.Semaphore(5)

        async def fetch_one(item: Dict[str, Any]) -> Dict[str, Any]:
            url = item.get("url")
            if not url:
                return item
            async with sem:
                text = await self.fetch_page_text(url)
            if compress:
                item["content_excerpt"] = self.compress_text(text)
            else:
                item["content"] = text
            return item

        return await asyncio.gather(*(fetch_one(it) for it in results))


# Singleton
web_search_service = WebSearchService()
