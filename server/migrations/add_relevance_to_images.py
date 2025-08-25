"""
Миграция для добавления поля релевантности к изображениям
"""

import os
import sys
import json
from sqlalchemy import create_engine, text

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_URL

def add_relevance_to_images():
    """Добавляет поле релевантности к существующим изображениям"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Получаем все чанки с изображениями
            result = conn.execute(text("""
                SELECT id, images 
                FROM document_chunks 
                WHERE images IS NOT NULL AND images != 'null' AND images != ''
            """))
            
            updated_count = 0
            
            for row in result:
                chunk_id = row[0]
                images_data = row[1]
                
                try:
                    # Парсим JSON изображений
                    if isinstance(images_data, str):
                        images = json.loads(images_data)
                    else:
                        images = images_data
                    
                    if not isinstance(images, list):
                        continue
                    
                    # Обновляем каждое изображение, добавляя поле релевантности
                    updated_images = []
                    for image in images:
                        if isinstance(image, dict):
                            # Если поле релевантности отсутствует, добавляем его
                            if 'relevance_score' not in image:
                                image['relevance_score'] = 0.5  # Значение по умолчанию
                            updated_images.append(image)
                        else:
                            # Если изображение не является словарем, пропускаем
                            continue
                    
                    # Обновляем данные в базе
                    if updated_images:
                        updated_images_json = json.dumps(updated_images, ensure_ascii=False)
                        conn.execute(text("""
                            UPDATE document_chunks 
                            SET images = :images 
                            WHERE id = :chunk_id
                        """), {
                            'images': updated_images_json,
                            'chunk_id': chunk_id
                        })
                        updated_count += 1
                        print(f"Обновлен чанк {chunk_id}: добавлено поле релевантности к {len(updated_images)} изображениям")
                
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON для чанка {chunk_id}: {e}")
                    continue
                except Exception as e:
                    print(f"Ошибка обработки чанка {chunk_id}: {e}")
                    continue
            
            conn.commit()
            print(f"Миграция завершена. Обновлено чанков: {updated_count}")
            
    except Exception as e:
        print(f"Ошибка миграции: {e}")
        raise

if __name__ == "__main__":
    print("Запуск миграции для добавления поля релевантности к изображениям...")
    add_relevance_to_images()
    print("Миграция завершена успешно!")
