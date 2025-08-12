from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from web_search_service import web_search_service

router = APIRouter(prefix="/api/web-search", tags=["Web Search"])


class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")


class WebSearchItem(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    generated_response: Optional[bool] = None
    query: Optional[str] = None


class WebSearchResponse(BaseModel):
    success: bool
    results: Optional[List[WebSearchItem]] = None
    error: Optional[str] = None


@router.post("/query", response_model=WebSearchResponse)
async def web_search_endpoint(req: WebSearchRequest):
    """
    Генеративный поиск через Yandex Cloud ML SDK.
    Возвращает сгенерированный ИИ ответ на основе веб-поиска.
    Требуются переменные окружения SEARCH_API_API_KEY (или SEARCH_API_IAM_TOKEN) и YC_FOLDER_ID.
    """
    try:
        results = await web_search_service.search(query=req.query)
        return WebSearchResponse(success=True, results=results)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генеративного поиска: {e}")
