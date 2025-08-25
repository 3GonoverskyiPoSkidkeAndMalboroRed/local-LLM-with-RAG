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
                        
                        # Определяем контекст изображения с улучшенным алгоритмом
                        context = self._find_image_context_improved(page, img_index, chunk_text)
                        
                        # Вычисляем релевантность изображения к тексту чанка
                        relevance_score = self._calculate_image_relevance(context, chunk_text)
                        
                        images.append({
                            "type": "pdf_image",
                            "page": page_num + 1,
                            "index": img_index,
                            "data": f"data:image/png;base64,{img_base64}",
                            "context": context,
                            "relevance_score": relevance_score,
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
                            context = self._find_docx_image_context_improved(zip_file, file_info.filename, chunk_text)
                            
                            # Вычисляем релевантность изображения к тексту чанка
                            relevance_score = self._calculate_image_relevance(context, chunk_text)
                            
                            images.append({
                                "type": "docx_image",
                                "filename": os.path.basename(file_info.filename),
                                "data": f"data:{mime_type};base64,{img_base64}",
                                "context": context,
                                "relevance_score": relevance_score,
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
            
            # Вычисляем релевантность изображения к тексту чанка
            relevance_score = self._calculate_image_relevance(chunk_text[:200], chunk_text)
            
            return [{
                "type": "single_image",
                "filename": os.path.basename(file_path),
                "data": f"data:{mime_type};base64,{img_base64}",
                "context": chunk_text[:200] if chunk_text else "",
                "relevance_score": relevance_score,
                "file_path": file_path
            }]
            
        except Exception as e:
            print(f"Ошибка при обработке изображения {file_path}: {e}")
            return []
    
    def _find_image_context_improved(self, page, img_index: int, chunk_text: str) -> str:
        """Улучшенный поиск контекста изображения на странице PDF"""
        try:
            # Получаем структуру страницы
            page_dict = page.get_text("dict")
            blocks = page_dict["blocks"]
            
            # Разделяем блоки на изображения и текст
            image_blocks = [block for block in blocks if block.get("type") == 1]  # type 1 = image
            text_blocks = [block for block in blocks if block.get("type") == 0]   # type 0 = text
            
            if img_index >= len(image_blocks):
                return chunk_text[:200] if chunk_text else ""
            
            img_block = image_blocks[img_index]
            img_bbox = img_block["bbox"]
            
            # Ищем текст рядом с изображением (улучшенный алгоритм)
            nearby_texts = []
            
            for text_block in text_blocks:
                text_bbox = text_block["bbox"]
                
                # Вычисляем расстояние между изображением и текстом
                distance = self._calculate_distance(img_bbox, text_bbox)
                
                # Если текст находится близко к изображению (в пределах 100 пикселей)
                if distance < 100:
                    for line in text_block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text and len(text) > 3:  # Игнорируем слишком короткий текст
                                nearby_texts.append({
                                    "text": text,
                                    "distance": distance,
                                    "bbox": text_bbox
                                })
            
            # Сортируем тексты по расстоянию и важности
            nearby_texts.sort(key=lambda x: (x["distance"], -len(x["text"])))
            
            # Берем наиболее релевантные тексты
            relevant_texts = []
            total_length = 0
            max_context_length = 300
            
            for text_info in nearby_texts:
                if total_length + len(text_info["text"]) <= max_context_length:
                    relevant_texts.append(text_info["text"])
                    total_length += len(text_info["text"])
                else:
                    break
            
            if relevant_texts:
                return " ".join(relevant_texts)
            
            # Если не нашли близкий текст, ищем текст на той же странице
            page_text = page.get_text()
            if page_text:
                # Ищем наиболее информативную часть текста страницы
                sentences = page_text.split('.')
                informative_sentences = []
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20 and len(sentence) < 150:
                        # Проверяем, содержит ли предложение важные слова
                        important_words = ['диаграмма', 'график', 'схема', 'рисунок', 'изображение', 
                                         'фото', 'иллюстрация', 'таблица', 'chart', 'diagram', 'figure']
                        
                        if any(word in sentence.lower() for word in important_words):
                            informative_sentences.append(sentence)
                
                if informative_sentences:
                    return ". ".join(informative_sentences[:2]) + "."
            
        except Exception as e:
            print(f"Ошибка при поиске контекста изображения: {e}")
        
        return chunk_text[:200] if chunk_text else ""
    
    def _find_docx_image_context_improved(self, zip_file, image_filename: str, chunk_text: str) -> str:
        """Улучшенный поиск контекста изображения в DOCX файле"""
        try:
            # Читаем document.xml для поиска связей с изображениями
            if 'word/document.xml' in zip_file.namelist():
                xml_content = zip_file.read('word/document.xml').decode('utf-8')
                
                # Ищем ссылки на изображения и связанный текст
                image_rid = None
                
                # Ищем rId для нашего изображения
                for match in re.finditer(r'<a:blip[^>]*r:embed="([^"]*)"', xml_content):
                    rid = match.group(1)
                    # Проверяем, соответствует ли этот rId нашему изображению
                    if self._check_rid_mapping(zip_file, rid, image_filename):
                        image_rid = rid
                        break
                
                if image_rid:
                    # Ищем текст вокруг изображения
                    context = self._find_text_around_image(xml_content, image_rid)
                    if context:
                        return context
                
        except Exception as e:
            print(f"Ошибка при поиске контекста изображения в DOCX: {e}")
        
        return chunk_text[:200] if chunk_text else ""
    
    def _check_rid_mapping(self, zip_file, rid: str, image_filename: str) -> bool:
        """Проверяет соответствие rId и имени файла изображения"""
        try:
            if 'word/_rels/document.xml.rels' in zip_file.namelist():
                rels_content = zip_file.read('word/_rels/document.xml.rels').decode('utf-8')
                
                # Ищем связь rId с файлом изображения
                pattern = f'Id="{rid}"[^>]*Target="[^"]*{image_filename}"'
                return bool(re.search(pattern, rels_content))
                
        except Exception as e:
            print(f"Ошибка при проверке rId mapping: {e}")
        
        return False
    
    def _find_text_around_image(self, xml_content: str, image_rid: str) -> str:
        """Ищет текст вокруг изображения в XML документе"""
        try:
            # Ищем параграфы, содержащие изображение
            paragraphs = re.findall(r'<w:p[^>]*>.*?</w:p>', xml_content, re.DOTALL)
            
            for paragraph in paragraphs:
                # Проверяем, содержит ли параграф наше изображение
                if f'r:embed="{image_rid}"' in paragraph:
                    # Извлекаем текст из параграфа
                    text_elements = re.findall(r'<w:t[^>]*>(.*?)</w:t>', paragraph, re.DOTALL)
                    if text_elements:
                        text = ' '.join(text_elements).strip()
                        if text and len(text) > 10:
                            return text
            
        except Exception as e:
            print(f"Ошибка при поиске текста вокруг изображения: {e}")
        
        return ""
    
    def _calculate_distance(self, bbox1, bbox2) -> float:
        """Вычисляет расстояние между двумя bounding box"""
        try:
            # Центры bounding box
            center1_x = (bbox1[0] + bbox1[2]) / 2
            center1_y = (bbox1[1] + bbox1[3]) / 2
            center2_x = (bbox2[0] + bbox2[2]) / 2
            center2_y = (bbox2[1] + bbox2[3]) / 2
            
            # Евклидово расстояние
            distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
            return distance
            
        except Exception:
            return float('inf')
    
    def _calculate_image_relevance(self, image_context: str, chunk_text: str) -> float:
        """Вычисляет релевантность изображения к тексту чанка"""
        if not image_context or not chunk_text:
            return 0.0
        
        try:
            # Приводим к нижнему регистру для сравнения
            context_lower = image_context.lower()
            chunk_lower = chunk_text.lower()
            
            # Разбиваем на слова
            context_words = set(re.findall(r'\b\w+\b', context_lower))
            chunk_words = set(re.findall(r'\b\w+\b', chunk_lower))
            
            # Удаляем стоп-слова
            stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'об', 'за', 'при', 'под', 'над', 'перед', 'после', 'между', 'через', 'без', 'про', 'со', 'во', 'не', 'ни', 'но', 'или', 'либо', 'что', 'как', 'где', 'когда', 'почему', 'зачем', 'какой', 'какая', 'какое', 'какие', 'чей', 'чья', 'чьё', 'чьи', 'это', 'тот', 'та', 'то', 'те', 'такой', 'такая', 'такое', 'такие', 'столько', 'сколько', 'который', 'которая', 'которое', 'которые', 'тот', 'та', 'то', 'те', 'этот', 'эта', 'это', 'эти', 'сам', 'сама', 'само', 'сами', 'весь', 'вся', 'всё', 'все', 'каждый', 'каждая', 'каждое', 'каждые', 'любой', 'любая', 'любое', 'любые', 'всякий', 'всякая', 'всякое', 'всякие', 'другой', 'другая', 'другое', 'другие', 'иной', 'иная', 'иное', 'иные', 'самый', 'самая', 'самое', 'самые', 'больше', 'больше', 'больше', 'больше', 'меньше', 'меньше', 'меньше', 'меньше', 'лучше', 'лучше', 'лучше', 'лучше', 'хуже', 'хуже', 'хуже', 'хуже', 'больший', 'большая', 'большее', 'большие', 'меньший', 'меньшая', 'меньшее', 'меньшие', 'лучший', 'лучшая', 'лучшее', 'лучшие', 'худший', 'худшая', 'худшее', 'худшие'}
            
            context_words = context_words - stop_words
            chunk_words = chunk_words - stop_words
            
            # Вычисляем пересечение слов
            common_words = context_words & chunk_words
            
            if not context_words or not chunk_words:
                return 0.0
            
            # Вычисляем Jaccard similarity
            jaccard_similarity = len(common_words) / len(context_words | chunk_words)
            
            # Дополнительные факторы
            # 1. Длина контекста (предпочитаем более длинный контекст)
            context_length_factor = min(len(image_context) / 200, 1.0)
            
            # 2. Наличие ключевых слов об изображениях
            image_keywords = {'диаграмма', 'график', 'схема', 'рисунок', 'изображение', 'фото', 'иллюстрация', 'таблица', 'chart', 'diagram', 'figure', 'image', 'picture'}
            keyword_bonus = 0.1 if any(word in context_lower for word in image_keywords) else 0.0
            
            # 3. Наличие цифр (часто указывает на графики/диаграммы)
            number_bonus = 0.05 if re.search(r'\d+', image_context) else 0.0
            
            # Итоговая релевантность
            relevance = jaccard_similarity * 0.6 + context_length_factor * 0.2 + keyword_bonus + number_bonus
            
            return min(relevance, 1.0)
            
        except Exception as e:
            print(f"Ошибка при вычислении релевантности изображения: {e}")
            return 0.0
    
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
        Получает изображения для конкретного чанка с фильтрацией по релевантности
        
        Args:
            content_id: ID контента
            department_id: ID отдела
            chunk_text: Текст чанка
            
        Returns:
            Список изображений, отсортированный по релевантности
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
            images = self.extract_images_from_file(file_path, chunk_text)
            
            # Фильтруем изображения по релевантности
            relevant_images = []
            for image in images:
                relevance_score = image.get('relevance_score', 0.0)
                # Показываем только изображения с релевантностью выше 0.1
                if relevance_score > 0.1:
                    relevant_images.append(image)
            
            # Сортируем по релевантности (убывание)
            relevant_images.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
            
            # Ограничиваем количество изображений (максимум 3 на чанк)
            return relevant_images[:3]
            
        except Exception as e:
            print(f"Ошибка при получении изображений для чанка: {e}")
            return []
        finally:
            db.close()
