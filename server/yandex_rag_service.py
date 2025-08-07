import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, SessionLocal
from models_db import Content, Department, DocumentChunk, RAGSession
from yandex_ai_service import YandexAIService
import PyPDF2
import docx
from io import BytesIO
import re
import pandas as pd
from openpyxl import load_workbook

class YandexRAGService:
    def __init__(self):
        self.yandex_ai = YandexAIService()
        self.chunk_size = 1000  # Размер чанка в символах
        self.chunk_overlap = 200  # Перекрытие между чанками
        
    async def initialize_rag(self, department_id: int, force_reload: bool = False) -> Dict[str, Any]:
        """Инициализация RAG системы для отдела"""
        db = SessionLocal()
        try:
            # Проверяем существование отдела
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                return {
                    "success": False,
                    "message": f"Отдел с ID {department_id} не найден"
                }
            
            # Получаем или создаем RAG сессию
            rag_session = db.query(RAGSession).filter(RAGSession.department_id == department_id).first()
            if not rag_session:
                rag_session = RAGSession(department_id=department_id)
                db.add(rag_session)
                db.commit()
                db.refresh(rag_session)
            
            # Получаем все документы отдела
            documents = db.query(Content).filter(Content.department_id == department_id).all()
            
            if not documents:
                return {
                    "success": False,
                    "message": f"Нет документов для обработки в отделе {department.department_name}"
                }       
     
            # Если принудительная перезагрузка, удаляем существующие чанки
            if force_reload:
                db.query(DocumentChunk).filter(DocumentChunk.department_id == department_id).delete()
                db.commit()
            
            processed_docs = 0
            total_chunks = 0
            
            for document in documents:
                # Проверяем, есть ли уже чанки для этого документа
                existing_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.content_id == document.id
                ).count()
                
                if existing_chunks > 0 and not force_reload:
                    continue
                
                # Извлекаем текст из документа
                text_content = await self._extract_text_from_file(document.file_path)
                if not text_content:
                    continue
                
                # Разбиваем на чанки
                chunks = self._split_text_into_chunks(text_content)
                
                # Создаем эмбеддинги для каждого чанка
                for i, chunk_text in enumerate(chunks):
                    try:
                        # Получаем эмбеддинг от Yandex
                        embedding = await self.yandex_ai.get_embedding(chunk_text)
                        
                        # Сохраняем чанк в БД
                        chunk = DocumentChunk(
                            content_id=document.id,
                            department_id=department_id,
                            chunk_text=chunk_text,
                            chunk_index=i,
                            embedding_vector=embedding
                        )
                        db.add(chunk)
                        total_chunks += 1
                        
                    except Exception as e:
                        print(f"Ошибка создания эмбеддинга для чанка {i} документа {document.id}: {e}")
                        continue
                
                processed_docs += 1
                db.commit()
            
            # Обновляем статус RAG сессии
            rag_session.is_initialized = True
            rag_session.documents_count = len(documents)
            rag_session.chunks_count = total_chunks
            rag_session.last_updated = func.now()
            db.commit()
            
            return {
                "success": True,
                "message": f"RAG система инициализирована для отдела {department.department_name}",
                "documents_processed": processed_docs,
                "chunks_created": total_chunks
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Ошибка инициализации RAG: {str(e)}"
            }
        finally:
            db.close()  
  
    async def get_rag_status(self, department_id: int) -> Dict[str, Any]:
        """Получение статуса RAG системы для отдела"""
        db = SessionLocal()
        try:
            # Получаем информацию об отделе
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                raise Exception(f"Отдел с ID {department_id} не найден")
            
            # Получаем RAG сессию
            rag_session = db.query(RAGSession).filter(RAGSession.department_id == department_id).first()
            
            # Считаем документы в БД
            documents_in_db = db.query(Content).filter(Content.department_id == department_id).count()
            
            # Считаем чанки в векторной БД
            chunks_in_vector_store = db.query(DocumentChunk).filter(
                DocumentChunk.department_id == department_id
            ).count()
            
            is_initialized = rag_session.is_initialized if rag_session else False
            needs_reinitialization = False
            
            if rag_session and is_initialized:
                # Проверяем, нужна ли реинициализация
                needs_reinitialization = (
                    rag_session.documents_count != documents_in_db or
                    chunks_in_vector_store == 0
                )
            
            return {
                "department_id": department_id,
                "department_name": department.department_name,
                "is_initialized": is_initialized,
                "documents_in_db": documents_in_db,
                "documents_in_vector_store": chunks_in_vector_store,
                "needs_reinitialization": needs_reinitialization,
                "last_updated": rag_session.last_updated.isoformat() if rag_session and rag_session.last_updated else None
            }
            
        except Exception as e:
            raise Exception(f"Ошибка получения статуса RAG: {str(e)}")
        finally:
            db.close()
    
    async def reset_rag(self, department_id: int) -> Dict[str, Any]:
        """Сброс RAG системы для отдела"""
        db = SessionLocal()
        try:
            # Проверяем существование отдела
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                return {
                    "success": False,
                    "message": f"Отдел с ID {department_id} не найден"
                }
            
            # Удаляем все чанки отдела
            deleted_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.department_id == department_id
            ).delete()
            
            # Сбрасываем RAG сессию
            rag_session = db.query(RAGSession).filter(RAGSession.department_id == department_id).first()
            if rag_session:
                rag_session.is_initialized = False
                rag_session.documents_count = 0
                rag_session.chunks_count = 0
                rag_session.last_updated = func.now()
            
            db.commit()
            
            return {
                "success": True,
                "message": f"RAG система сброшена для отдела {department.department_name}. Удалено чанков: {deleted_chunks}"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Ошибка сброса RAG: {str(e)}"
            }
        finally:
            db.close()  
  
    async def query_rag(self, department_id: int, question: str) -> Dict[str, Any]:
        """Выполнение RAG запроса"""
        db = SessionLocal()
        try:
            # Проверяем, инициализирована ли RAG система
            rag_session = db.query(RAGSession).filter(RAGSession.department_id == department_id).first()
            if not rag_session or not rag_session.is_initialized:
                raise Exception("RAG система не инициализирована для данного отдела")
            
            # Получаем эмбеддинг для вопроса
            question_embedding = await self.yandex_ai.get_embedding(question)
            
            # Получаем все чанки отдела
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.department_id == department_id
            ).all()
            
            if not chunks:
                raise Exception("Нет данных в векторной базе для данного отдела")
            
            # Вычисляем сходство с каждым чанком
            similarities = []
            for chunk in chunks:
                if chunk.embedding_vector:
                    similarity = self._cosine_similarity(question_embedding, chunk.embedding_vector)
                    similarities.append((chunk, similarity))
            
            # Сортируем по убыванию сходства и берем топ-5
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunks = similarities[:5]
            
            # Формируем контекст из наиболее релевантных чанков
            context_parts = []
            sources = []
            
            for chunk, similarity in top_chunks:
                if similarity > 0.3:  # Порог релевантности
                    context_parts.append(chunk.chunk_text)
                    
                    # Получаем информацию о документе-источнике
                    content = db.query(Content).filter(Content.id == chunk.content_id).first()
                    if content:
                        sources.append({
                            "title": content.title,
                            "file_path": content.file_path,
                            "similarity": round(similarity, 3)
                        })
            
            if not context_parts:
                return {
                    "answer": "К сожалению, не найдено релевантной информации для ответа на ваш вопрос.",
                    "sources": [],
                    "context_used": 0
                }
            
            # Формируем промпт с контекстом
            context = "\n\n".join(context_parts)
            prompt = f"""На основе предоставленного контекста ответьте на вопрос пользователя.

Контекст:
{context}

Вопрос: {question}

Ответ должен быть основан только на предоставленном контексте. Если в контексте нет информации для ответа, скажите об этом."""
            
            # Получаем ответ от Yandex AI
            answer = await self.yandex_ai.generate_response(prompt)
            
            return {
                "answer": answer,
                "sources": sources,
                "context_used": len(context_parts)
            }
            
        except Exception as e:
            raise Exception(f"Ошибка RAG запроса: {str(e)}")
        finally:
            db.close()    

    async def _extract_text_from_file(self, file_path: str) -> str:
        """Извлечение текста из файла"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_text_from_docx(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                return self._extract_text_from_excel(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return ""
                
        except Exception as e:
            print(f"Ошибка извлечения текста из файла {file_path}: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF файла"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Ошибка извлечения текста из PDF {file_path}: {e}")
            return ""
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX файла"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Ошибка извлечения текста из DOCX {file_path}: {e}")
            return ""
    
    def _extract_text_from_excel(self, file_path: str) -> str:
        """Извлечение текста из Excel файла"""
        try:
            # Загружаем рабочую книгу
            workbook = load_workbook(file_path, data_only=True)
            
            text_content = f"=== Excel файл: {os.path.basename(file_path)} ===\n"
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                text_content += f"\n--- Лист: {sheet_name} ---\n"
                
                # Получаем размеры данных
                max_row = sheet.max_row
                max_col = sheet.max_column
                
                if max_row > 0 and max_col > 0:
                    # Читаем заголовки
                    headers = []
                    for col in range(1, max_col + 1):
                        cell_value = sheet.cell(row=1, column=col).value
                        headers.append(str(cell_value) if cell_value is not None else f"Столбец {col}")
                    
                    text_content += f"Заголовки: {' | '.join(headers)}\n"
                    
                    # Читаем данные (ограничиваем 100 строками для производительности)
                    for row in range(2, min(max_row + 1, 102)):  # 100 строк данных + заголовки
                        row_data = []
                        for col in range(1, max_col + 1):
                            cell_value = sheet.cell(row=row, column=col).value
                            row_data.append(str(cell_value) if cell_value is not None else "")
                        
                        text_content += f"Строка {row}: {' | '.join(row_data)}\n"
                    
                    if max_row > 101:
                        text_content += f"... и еще {max_row - 101} строк\n"
                
                text_content += "\n"
            
            return text_content
            
        except Exception as e:
            print(f"Ошибка извлечения текста из Excel {file_path}: {e}")
            return ""
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Разбиение текста на чанки"""
        # Очищаем текст от лишних пробелов и переносов
        text = re.sub(r'\s+', ' ', text.strip())
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Ищем ближайший разделитель предложения
            chunk_end = end
            for i in range(end, max(start + self.chunk_size - self.chunk_overlap, start), -1):
                if text[i] in '.!?':
                    chunk_end = i + 1
                    break
            
            chunks.append(text[start:chunk_end])
            start = chunk_end - self.chunk_overlap
            
            if start < 0:
                start = 0
        
        return chunks
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисление косинусного сходства между векторами"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

# Глобальный экземпляр сервиса
yandex_rag_service = YandexRAGService()