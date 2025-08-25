"""
Утилита для извлечения изображений из документов
"""

import os
import re
import json
import base64
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import fitz  # PyMuPDF
from docx import Document
import zipfile
import xml.etree.ElementTree as ET

class ImageExtractor:
    """Класс для извлечения изображений из различных типов документов"""
    
    def __init__(self, base_path: str = "ContentForDepartment"):
        self.base_path = base_path
        self.supported_image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    def extract_images_from_file(self, file_path: str, chunk_text: str = "") -> List[Dict[str, Any]]:
        """
        Извлекает изображения из файла
        
        Args:
            file_path: Путь к файлу
            chunk_text: Текст чанка для контекста
            
        Returns:
            Список словарей с информацией об изображениях
        """
        if not os.path.exists(file_path):
            return []
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path, chunk_text)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path, chunk_text)
            elif file_extension in self.supported_image_extensions:
                return self._extract_single_image(file_path, chunk_text)
            else:
                return []
        except Exception as e:
            print(f"Ошибка при извлечении изображений из {file_path}: {e}")
            return []
    
    def _extract_from_pdf(self, file_path: str, chunk_text: str) -> List[Dict[str, Any]]:
        """Извлекает изображения из PDF файла"""
        images = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Получаем изображение
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                        else:  # CMYK: convert to RGB first
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix1.tobytes("png")
                            pix1 = None
                        
                        # Кодируем в base64
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        
                        # Определяем контекст изображения
                        context = self._find_image_context(page, img_index, chunk_text)
                        
                        images.append({
                            "type": "pdf_image",
                            "page": page_num + 1,
                            "index": img_index,
                            "data": f"data:image/png;base64,{img_base64}",
                            "context": context,
                            "file_path": file_path
                        })
                        
                        pix = None
                        
                    except Exception as e:
                        print(f"Ошибка при обработке изображения {img_index} на странице {page_num}: {e}")
                        continue
            
            doc.close()
            
        except Exception as e:
            print(f"Ошибка при открытии PDF {file_path}: {e}")
        
        return images
    
    def _extract_from_docx(self, file_path: str, chunk_text: str) -> List[Dict[str, Any]]:
        """Извлекает изображения из DOCX файла"""
        images = []
        
        try:
            # Открываем DOCX как ZIP архив
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Ищем изображения в папке word/media
                for file_info in zip_file.filelist:
                    if file_info.filename.startswith('word/media/'):
                        try:
                            # Читаем изображение
                            img_data = zip_file.read(file_info.filename)
                            
                            # Определяем тип изображения
                            file_ext = os.path.splitext(file_info.filename)[1].lower()
                            mime_type = self._get_mime_type(file_ext)
                            
                            # Кодируем в base64
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            
                            # Определяем контекст изображения
                            context = self._find_docx_image_context(zip_file, file_info.filename, chunk_text)
                            
                            images.append({
                                "type": "docx_image",
                                "filename": os.path.basename(file_info.filename),
                                "data": f"data:{mime_type};base64,{img_base64}",
                                "context": context,
                                "file_path": file_path
                            })
                            
                        except Exception as e:
                            print(f"Ошибка при обработке изображения {file_info.filename}: {e}")
                            continue
                            
        except Exception as e:
            print(f"Ошибка при открытии DOCX {file_path}: {e}")
        
        return images
    
    def _extract_single_image(self, file_path: str, chunk_text: str) -> List[Dict[str, Any]]:
        """Обрабатывает одиночное изображение"""
        try:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            
            # Определяем тип изображения
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_type = self._get_mime_type(file_ext)
            
            # Кодируем в base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            return [{
                "type": "single_image",
                "filename": os.path.basename(file_path),
                "data": f"data:{mime_type};base64,{img_base64}",
                "context": chunk_text[:200] if chunk_text else "",
                "file_path": file_path
            }]
            
        except Exception as e:
            print(f"Ошибка при обработке изображения {file_path}: {e}")
            return []
    
    def _find_image_context(self, page, img_index: int, chunk_text: str) -> str:
        """Находит контекст изображения на странице PDF"""
        try:
            # Получаем текст вокруг изображения
            text_blocks = page.get_text("dict")["blocks"]
            
            # Ищем блоки текста рядом с изображениями
            image_blocks = [block for block in text_blocks if block.get("type") == 1]  # type 1 = image
            text_blocks = [block for block in text_blocks if block.get("type") == 0]   # type 0 = text
            
            if img_index < len(image_blocks):
                img_block = image_blocks[img_index]
                img_bbox = img_block["bbox"]
                
                # Ищем текст рядом с изображением
                nearby_text = []
                for text_block in text_blocks:
                    text_bbox = text_block["bbox"]
                    
                    # Проверяем, находится ли текст рядом с изображением
                    if (abs(text_bbox[1] - img_bbox[3]) < 50 or  # Текст выше изображения
                        abs(text_bbox[3] - img_bbox[1]) < 50):   # Текст ниже изображения
                        
                        for line in text_block.get("lines", []):
                            for span in line.get("spans", []):
                                nearby_text.append(span.get("text", ""))
                
                return " ".join(nearby_text) if nearby_text else chunk_text[:200]
            
        except Exception as e:
            print(f"Ошибка при поиске контекста изображения: {e}")
        
        return chunk_text[:200] if chunk_text else ""
    
    def _find_docx_image_context(self, zip_file, image_filename: str, chunk_text: str) -> str:
        """Находит контекст изображения в DOCX файле"""
        try:
            # Читаем document.xml для поиска связей с изображениями
            if 'word/document.xml' in zip_file.namelist():
                xml_content = zip_file.read('word/document.xml').decode('utf-8')
                
                # Ищем ссылки на изображения
                image_rid = None
                for match in re.finditer(r'<a:blip[^>]*r:embed="([^"]*)"', xml_content):
                    # Здесь можно добавить логику для поиска контекста
                    pass
                
        except Exception as e:
            print(f"Ошибка при поиске контекста изображения в DOCX: {e}")
        
        return chunk_text[:200] if chunk_text else ""
    
    def _get_mime_type(self, file_ext: str) -> str:
        """Определяет MIME тип по расширению файла"""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        return mime_types.get(file_ext.lower(), 'image/png')
    
    def get_images_for_chunk(self, content_id: int, department_id: int, chunk_text: str) -> List[Dict[str, Any]]:
        """
        Получает изображения для конкретного чанка
        
        Args:
            content_id: ID контента
            department_id: ID отдела
            chunk_text: Текст чанка
            
        Returns:
            Список изображений
        """
        from models_db import Content
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            # Получаем информацию о файле
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                return []
            
            # Формируем полный путь к файлу
            file_path = os.path.join(self.base_path, "AllTypesOfFiles", str(department_id), content.file_path)
            
            # Извлекаем изображения
            return self.extract_images_from_file(file_path, chunk_text)
            
        except Exception as e:
            print(f"Ошибка при получении изображений для чанка: {e}")
            return []
        finally:
            db.close()
