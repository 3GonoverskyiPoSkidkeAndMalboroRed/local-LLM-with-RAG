#!/usr/bin/env python3
"""
Утилиты для миграции и пересоздания эмбеддингов
Вспомогательные функции для работы с векторными базами данных
"""

import os
import sys
import json
import sqlite3
import hashlib
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Iterator
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

class EmbeddingMigrationUtils:
    """Утилиты для миграции эмбеддингов"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Получить схему базы данных"""
        cursor = self.connection.cursor()
        
        # Получить все таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [
                {
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default_value': row[4],
                    'primary_key': bool(row[5])
                }
                for row in cursor.fetchall()
            ]
            schema[table] = columns
        
        return schema
    
    def get_embedding_providers(self) -> List[str]:
        """Получить список провайдеров эмбеддингов в базе"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT provider FROM embeddings")
            providers = [row[0] for row in cursor.fetchall()]
            return providers
        except sqlite3.OperationalError:
            # Таблица embeddings не существует
            return []
    
    def get_documents_without_yandex_embeddings(self) -> List[Dict[str, Any]]:
        """Получить документы без Yandex Cloud эмбеддингов"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT d.id, d.content, d.metadata, d.source, d.created_at
        FROM documents d
        LEFT JOIN embeddings e ON d.id = e.document_id AND e.provider = 'yandex_cloud'
        WHERE e.document_id IS NULL
        ORDER BY d.id
        """
        
        cursor.execute(query)
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'id': row[0],
                'content': row[1],
                'metadata': json.loads(row[2]) if row[2] else {},
                'source': row[3],
                'created_at': row[4]
            })
        
        return documents
    
    def get_documents_with_old_embeddings(self, provider: str = None) -> List[Dict[str, Any]]:
        """Получить документы со старыми эмбеддингами"""
        cursor = self.connection.cursor()
        
        if provider:
            query = """
            SELECT d.id, d.content, d.metadata, d.source, d.created_at,
                   e.provider, e.model, e.created_at as embedding_created_at
            FROM documents d
            JOIN embeddings e ON d.id = e.document_id
            WHERE e.provider = ?
            ORDER BY d.id
            """
            cursor.execute(query, (provider,))
        else:
            query = """
            SELECT d.id, d.content, d.metadata, d.source, d.created_at,
                   e.provider, e.model, e.created_at as embedding_created_at
            FROM documents d
            JOIN embeddings e ON d.id = e.document_id
            WHERE e.provider != 'yandex_cloud'
            ORDER BY d.id
            """
            cursor.execute(query)
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'id': row[0],
                'content': row[1],
                'metadata': json.loads(row[2]) if row[2] else {},
                'source': row[3],
                'created_at': row[4],
                'old_provider': row[5],
                'old_model': row[6],
                'embedding_created_at': row[7]
            })
        
        return documents
    
    def compare_embeddings(self, doc_id: int) -> Dict[str, Any]:
        """Сравнить эмбеддинги для документа от разных провайдеров"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT provider, model, embedding, created_at
            FROM embeddings
            WHERE document_id = ?
            ORDER BY created_at DESC
        """, (doc_id,))
        
        embeddings = []
        for row in cursor.fetchall():
            try:
                embedding_data = json.loads(row[2])
                embeddings.append({
                    'provider': row[0],
                    'model': row[1],
                    'embedding': embedding_data,
                    'dimension': len(embedding_data),
                    'created_at': row[3]
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid embedding data for document {doc_id}, provider {row[0]}")
        
        return {
            'document_id': doc_id,
            'embeddings': embeddings,
            'provider_count': len(set(emb['provider'] for emb in embeddings))
        }
    
    def calculate_embedding_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Вычислить косинусное сходство между эмбеддингами"""
        import math
        
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def validate_embedding_consistency(self) -> Dict[str, Any]:
        """Проверить консистентность эмбеддингов"""
        cursor = self.connection.cursor()
        
        # Получить статистику по провайдерам
        cursor.execute("""
            SELECT provider, model, COUNT(*) as count,
                   MIN(created_at) as first_created,
                   MAX(created_at) as last_created
            FROM embeddings
            GROUP BY provider, model
            ORDER BY provider, model
        """)
        
        provider_stats = []
        for row in cursor.fetchall():
            provider_stats.append({
                'provider': row[0],
                'model': row[1],
                'count': row[2],
                'first_created': row[3],
                'last_created': row[4]
            })
        
        # Проверить размерности эмбеддингов
        cursor.execute("""
            SELECT provider, model, embedding
            FROM embeddings
            ORDER BY provider, model
            LIMIT 100
        """)
        
        dimension_stats = {}
        for row in cursor.fetchall():
            provider_model = f"{row[0]}:{row[1]}"
            try:
                embedding_data = json.loads(row[2])
                dimension = len(embedding_data)
                
                if provider_model not in dimension_stats:
                    dimension_stats[provider_model] = []
                dimension_stats[provider_model].append(dimension)
            except json.JSONDecodeError:
                continue
        
        # Анализ размерностей
        dimension_analysis = {}
        for provider_model, dimensions in dimension_stats.items():
            unique_dimensions = set(dimensions)
            dimension_analysis[provider_model] = {
                'unique_dimensions': list(unique_dimensions),
                'is_consistent': len(unique_dimensions) == 1,
                'sample_count': len(dimensions)
            }
        
        return {
            'provider_stats': provider_stats,
            'dimension_analysis': dimension_analysis,
            'total_embeddings': sum(stat['count'] for stat in provider_stats)
        }
    
    def create_embedding_index(self) -> bool:
        """Создать индексы для оптимизации запросов эмбеддингов"""
        cursor = self.connection.cursor()
        
        try:
            # Индекс по document_id и provider
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_doc_provider 
                ON embeddings(document_id, provider)
            """)
            
            # Индекс по provider и model
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_provider_model 
                ON embeddings(provider, model)
            """)
            
            # Индекс по created_at
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_created_at 
                ON embeddings(created_at)
            """)
            
            self.connection.commit()
            logger.info("Embedding indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False
    
    def cleanup_old_embeddings(self, provider: str, dry_run: bool = True) -> int:
        """Очистить старые эмбеддинги от указанного провайдера"""
        cursor = self.connection.cursor()
        
        # Подсчитать количество записей для удаления
        cursor.execute("SELECT COUNT(*) FROM embeddings WHERE provider = ?", (provider,))
        count_to_delete = cursor.fetchone()[0]
        
        if dry_run:
            logger.info(f"DRY RUN: Would delete {count_to_delete} embeddings from provider '{provider}'")
            return count_to_delete
        
        # Удалить записи
        cursor.execute("DELETE FROM embeddings WHERE provider = ?", (provider,))
        deleted_count = cursor.rowcount
        
        self.connection.commit()
        logger.info(f"Deleted {deleted_count} embeddings from provider '{provider}'")
        
        return deleted_count
    
    def export_embeddings(self, provider: str, output_file: str) -> bool:
        """Экспортировать эмбеддинги в файл"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT d.id, d.content, d.metadata, d.source,
                   e.embedding, e.model, e.created_at
            FROM documents d
            JOIN embeddings e ON d.id = e.document_id
            WHERE e.provider = ?
            ORDER BY d.id
        """, (provider,))
        
        export_data = {
            'provider': provider,
            'exported_at': datetime.now().isoformat(),
            'embeddings': []
        }
        
        for row in cursor.fetchall():
            try:
                embedding_data = json.loads(row[4])
                export_data['embeddings'].append({
                    'document_id': row[0],
                    'content': row[1],
                    'metadata': json.loads(row[2]) if row[2] else {},
                    'source': row[3],
                    'embedding': embedding_data,
                    'model': row[5],
                    'created_at': row[6]
                })
            except json.JSONDecodeError:
                logger.warning(f"Skipping invalid embedding for document {row[0]}")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(export_data['embeddings'])} embeddings to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export embeddings: {e}")
            return False
    
    def import_embeddings(self, input_file: str, overwrite: bool = False) -> int:
        """Импортировать эмбеддинги из файла"""
        try:
            with open(input_file, 'r') as f:
                import_data = json.load(f)
            
            cursor = self.connection.cursor()
            imported_count = 0
            
            for embedding_data in import_data['embeddings']:
                document_id = embedding_data['document_id']
                provider = import_data['provider']
                
                # Проверить, существует ли уже эмбеддинг
                if not overwrite:
                    cursor.execute("""
                        SELECT COUNT(*) FROM embeddings 
                        WHERE document_id = ? AND provider = ?
                    """, (document_id, provider))
                    
                    if cursor.fetchone()[0] > 0:
                        continue  # Пропустить существующий
                
                # Вставить или обновить эмбеддинг
                cursor.execute("""
                    INSERT OR REPLACE INTO embeddings 
                    (document_id, embedding, provider, model, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    document_id,
                    json.dumps(embedding_data['embedding']),
                    provider,
                    embedding_data['model'],
                    embedding_data['created_at']
                ))
                
                imported_count += 1
            
            self.connection.commit()
            logger.info(f"Imported {imported_count} embeddings from {input_file}")
            
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import embeddings: {e}")
            return 0

class EmbeddingBatchProcessor:
    """Batch процессор для создания эмбеддингов"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.yandex_embeddings = None
    
    async def initialize_yandex_embeddings(self):
        """Инициализировать Yandex эмбеддинги"""
        try:
            # Mock langchain_core
            import sys
            from unittest.mock import MagicMock
            
            class MockEmbeddings:
                pass
            
            sys.modules['langchain_core'] = MagicMock()
            sys.modules['langchain_core.embeddings'] = MagicMock()
            sys.modules['langchain_core.embeddings'].Embeddings = MockEmbeddings
            
            from yandex_embeddings import YandexEmbeddings
            
            self.yandex_embeddings = YandexEmbeddings(
                model="text-search-doc",
                cache_enabled=True
            )
            
            logger.info("Yandex embeddings initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Yandex embeddings: {e}")
            raise
    
    async def process_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработать batch документов"""
        if not self.yandex_embeddings:
            await self.initialize_yandex_embeddings()
        
        texts = [doc['content'] for doc in documents]
        
        try:
            # Создать эмбеддинги
            embeddings = self.yandex_embeddings.embed_documents(texts)
            
            # Объединить с документами
            results = []
            for doc, embedding in zip(documents, embeddings):
                results.append({
                    'document': doc,
                    'embedding': embedding,
                    'success': True,
                    'error': None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process batch: {e}")
            
            # Возвратить результаты с ошибками
            results = []
            for doc in documents:
                results.append({
                    'document': doc,
                    'embedding': None,
                    'success': False,
                    'error': str(e)
                })
            
            return results
    
    async def process_all_documents(self, documents: List[Dict[str, Any]]) -> Iterator[List[Dict[str, Any]]]:
        """Обработать все документы по батчам"""
        total_docs = len(documents)
        
        for i in range(0, total_docs, self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total_docs + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            results = await self.process_documents_batch(batch)
            yield results

def create_migration_summary(db_path: str) -> Dict[str, Any]:
    """Создать сводку по миграции"""
    with EmbeddingMigrationUtils(db_path) as utils:
        schema = utils.get_database_schema()
        providers = utils.get_embedding_providers()
        consistency = utils.validate_embedding_consistency()
        
        # Документы без Yandex эмбеддингов
        docs_without_yandex = utils.get_documents_without_yandex_embeddings()
        
        summary = {
            'database_path': db_path,
            'created_at': datetime.now().isoformat(),
            'schema': schema,
            'embedding_providers': providers,
            'consistency_check': consistency,
            'documents_without_yandex_embeddings': len(docs_without_yandex),
            'migration_needed': len(docs_without_yandex) > 0
        }
        
        return summary

if __name__ == "__main__":
    # Пример использования
    import argparse
    
    parser = argparse.ArgumentParser(description="Embedding migration utilities")
    parser.add_argument('--database', default='files/vector_db.sqlite', help='Database path')
    parser.add_argument('--action', choices=['summary', 'validate', 'export', 'cleanup'], 
                       required=True, help='Action to perform')
    parser.add_argument('--provider', help='Provider name for export/cleanup')
    parser.add_argument('--output', help='Output file for export')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    if args.action == 'summary':
        summary = create_migration_summary(args.database)
        print(json.dumps(summary, indent=2))
    
    elif args.action == 'validate':
        with EmbeddingMigrationUtils(args.database) as utils:
            consistency = utils.validate_embedding_consistency()
            print(json.dumps(consistency, indent=2))
    
    elif args.action == 'export' and args.provider and args.output:
        with EmbeddingMigrationUtils(args.database) as utils:
            utils.export_embeddings(args.provider, args.output)
    
    elif args.action == 'cleanup' and args.provider:
        with EmbeddingMigrationUtils(args.database) as utils:
            utils.cleanup_old_embeddings(args.provider, dry_run=args.dry_run)