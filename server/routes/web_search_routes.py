from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from web_search_service import web_search_service

router = APIRouter(prefix="/api/web-search", tags=["Web Search"])


class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    top_n: int = Field(3, ge=1, le=10, description="Количество результатов (1-10)")
    fetch_pages: bool = Field(True, description="Загружать и извлекать тексты страниц")
    compress: bool = Field(True, description="Сжимать извлеченные тексты (до ~1200 символов)")


class WebSearchItem(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    content_excerpt: Optional[str] = None
    content: Optional[str] = None


class WebSearchResponse(BaseModel):
    success: bool
    results: Optional[List[WebSearchItem]] = None
    error: Optional[str] = None


@router.post("/query", response_model=WebSearchResponse)
async def web_search_endpoint(req: WebSearchRequest):
    """
    Веб‑поиск по Яндекс Search API v2, при необходимости извлекает контент страниц и сжимает его.
    Требуются переменные окружения SEARCH_API_API_KEY (или SEARCH_API_IAM_TOKEN) и YC_FOLDER_ID.
    """
    try:
        results = await web_search_service.search_and_extract(
            query=req.query,
            top_n=req.top_n,
            fetch_pages=req.fetch_pages,
            compress=req.compress,
        )
        return WebSearchResponse(success=True, results=results)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка веб-поиска: {e}")
