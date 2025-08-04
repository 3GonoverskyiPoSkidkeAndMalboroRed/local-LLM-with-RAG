#!/usr/bin/env python3
"""
Система валидации целостности данных после миграции
Проверяет корректность миграции и целостность векторной базы данных
"""

import os
import sys
import json
import sqlite3
import hashlib
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging
import statistics

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Base exception for validation errors"""
    pass

class DataIntegrityValidator:
    """Валидатор целостности данных после миграции"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.validation_results = {}
        self.errors = []
        self.warnings = []
    
    def validate_database_structure(self) -> bool:
        """Проверить структуру базы данных"""
        logger.info("Validating database structure...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверить существование основных таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['documents', 'embeddings']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                self.errors.append(f"Missing required tables: {missing_tables}")
                return False
            
            # Проверить структуру таблицы documents
            cursor.execute("PRAGMA table_info(documents)")
            doc_columns = [row[1] for row in cursor.fetchall()]
            
            required_doc_columns = ['id', 'content', 'metadata', 'source']
            missing_doc_columns = [col for col in required_doc_columns if col not in doc_columns]
            
            if missing_doc_columns:
                self.errors.append(f"Missing columns in documents table: {missing_doc_columns}")
                return False
            
            # Проверить структуру таблицы embeddings
            cursor.execute("PRAGMA table_info(embeddings)")
            emb_columns = [row[1] for row in cursor.fetchall()]
            
            required_emb_columns = ['document_id', 'embedding', 'provider', 'model']
            missing_emb_columns = [col for col in required_emb_columns if col not in emb_columns]
            
            if missing_emb_columns:
                self.errors.append(f"Missing columns in embeddings table: {missing_emb_columns}")
                return False
            
            conn.close()
            
            self.validation_results['database_structure'] = {
                'valid': True,
                'tables': tables,
                'document_columns': doc_columns,
                'embedding_columns': emb_columns
            }
            
            logger.info("✅ Database structure validation passed")
            return True
            
        except Exception as e:
            self.errors.append(f"Database structure validation failed: {e}")
            logger.error(f"❌ Database structure validation failed: {e}")
            return False
    
    def validate_data_consistency(self) -> bool:
        """Проверить консистентность данных"""
        logger.info("Validating data consistency...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверить, что все документы имеют контент
            cursor.execute("SELECT COUNT(*) FROM documents WHERE content IS NULL OR content = ''")
            empty_content_count = cursor.fetchone()[0]
            
            if empty_content_count > 0:
                self.warnings.append(f"Found {empty_content_count} documents with empty content")
            
            # Проверить, что все эмбеддинги ссылаются на существующие документы
            cursor.execute("""
                SELECT COUNT(*) FROM embeddings e
                LEFT JOIN documents d ON e.document_id = d.id
                WHERE d.id IS NULL
            """)
            orphaned_embeddings = cursor.fetchone()[0]
            
            if orphaned_embeddings > 0:
                self.errors.append(f"Found {orphaned_embeddings} orphaned embeddings")
                return False
            
            # Проверить, что все эмбеддинги имеют валидные JSON данные
            cursor.execute("SELECT document_id, embedding FROM embeddings")
            invalid_embeddings = []
            
            for row in cursor.fetchall():
                doc_id, embedding_data = row
                try:
                    embedding = json.loads(embedding_data)
                    if not isinstance(embedding, list) or len(embedding) == 0:
                        invalid_embeddings.append(doc_id)
                except json.JSONDecodeError:
                    invalid_embeddings.append(doc_id)
            
            if invalid_embeddings:
                self.errors.append(f"Found {len(invalid_embeddings)} invalid embeddings for documents: {invalid_embeddings[:10]}")
                return False
            
            conn.close()
            
            self.validation_results['data_consistency'] = {
                'valid': True,
                'empty_content_documents': empty_content_count,
                'orphaned_embeddings': orphaned_embeddings,
                'invalid_embeddings': len(invalid_embeddings)
            }
            
            logger.info("✅ Data consistency validation passed")
            return True
            
        except Exception as e:
            self.errors.append(f"Data consistency validation failed: {e}")
            logger.error(f"❌ Data consistency validation failed: {e}")
            return False
    
    def validate_yandex_embeddings(self) -> bool:
        """Проверить Yandex Cloud эмбеддинги"""
        logger.info("Validating Yandex Cloud embeddings...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Подсчитать общее количество документов
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_documents = cursor.fetchone()[0]
            
            # Подсчитать документы с Yandex эмбеддингами
            cursor.execute("""
                SELECT COUNT(DISTINCT e.document_id) 
                FROM embeddings e 
                WHERE e.provider = 'yandex_cloud'
            """)
            yandex_embedded_docs = cursor.fetchone()[0]
            
            # Вычислить покрытие
            coverage_percentage = (yandex_embedded_docs / total_documents * 100) if total_documents > 0 else 0
            
            # Проверить размерности эмбеддингов
            cursor.execute("""
                SELECT embedding FROM embeddings 
                WHERE provider = 'yandex_cloud' 
                LIMIT 100
            """)
            
            dimensions = []
            for row in cursor.fetchall():
                try:
                    embedding = json.loads(row[0])
                    dimensions.append(len(embedding))
                except json.JSONDecodeError:
                    continue
            
            # Анализ размерностей
            unique_dimensions = set(dimensions)
            dimension_consistency = len(unique_dimensions) <= 1
            
            if not dimension_consistency:
                self.errors.append(f"Inconsistent embedding dimensions: {unique_dimensions}")
                return False
            
            # Проверить минимальное покрытие (95%)
            min_coverage = 95.0
            if coverage_percentage < min_coverage:
                self.errors.append(f"Low Yandex embedding coverage: {coverage_percentage:.1f}% < {min_coverage}%")
                return False
            
            # Проверить качество эмбеддингов (не все нули)
            cursor.execute("""
                SELECT embedding FROM embeddings 
                WHERE provider = 'yandex_cloud' 
                LIMIT 10
            """)
            
            zero_embeddings = 0
            for row in cursor.fetchall():
                try:
                    embedding = json.loads(row[0])
                    if all(x == 0 for x in embedding):
                        zero_embeddings += 1
                except json.JSONDecodeError:
                    continue
            
            if zero_embeddings > 0:
                self.warnings.append(f"Found {zero_embeddings} zero embeddings")
            
            conn.close()
            
            self.validation_results['yandex_embeddings'] = {
                'valid': True,
                'total_documents': total_documents,
                'yandex_embedded_documents': yandex_embedded_docs,
                'coverage_percentage': coverage_percentage,
                'embedding_dimensions': list(unique_dimensions),
                'dimension_consistency': dimension_consistency,
                'zero_embeddings': zero_embeddings
            }
            
            logger.info(f"✅ Yandex embeddings validation passed")
            logger.info(f"   Coverage: {coverage_percentage:.1f}%")
            logger.info(f"   Dimensions: {list(unique_dimensions)}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Yandex embeddings validation failed: {e}")
            logger.error(f"❌ Yandex embeddings validation failed: {e}")
            return False
    
    def validate_embedding_quality(self) -> bool:
        """Проверить качество эмбеддингов"""
        logger.info("Validating embedding quality...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получить выборку эмбеддингов для анализа
            cursor.execute("""
                SELECT d.content, e.embedding 
                FROM documents d
                JOIN embeddings e ON d.id = e.document_id
                WHERE e.provider = 'yandex_cloud'
                ORDER BY RANDOM()
                LIMIT 50
            """)
            
            samples = cursor.fetchall()
            
            if len(samples) == 0:
                self.warnings.append("No Yandex embeddings found for quality validation")
                return True
            
            quality_metrics = {
                'sample_count': len(samples),
                'dimension_stats': {},
                'magnitude_stats': {},
                'similarity_stats': {}
            }
            
            embeddings_data = []
            magnitudes = []
            
            for content, embedding_json in samples:
                try:
                    embedding = json.loads(embedding_json)
                    embeddings_data.append((content, embedding))
                    
                    # Вычислить магнитуду
                    magnitude = sum(x * x for x in embedding) ** 0.5
                    magnitudes.append(magnitude)
                    
                except json.JSONDecodeError:
                    continue
            
            if not magnitudes:
                self.errors.append("No valid embeddings found for quality analysis")
                return False
            
            # Статистика размерностей
            dimensions = [len(emb[1]) for emb in embeddings_data]
            quality_metrics['dimension_stats'] = {
                'min': min(dimensions),
                'max': max(dimensions),
                'mean': statistics.mean(dimensions),
                'unique_count': len(set(dimensions))
            }
            
            # Статистика магнитуд
            quality_metrics['magnitude_stats'] = {
                'min': min(magnitudes),
                'max': max(magnitudes),
                'mean': statistics.mean(magnitudes),
                'median': statistics.median(magnitudes),
                'std_dev': statistics.stdev(magnitudes) if len(magnitudes) > 1 else 0
            }
            
            # Проверить на аномальные значения
            mean_magnitude = quality_metrics['magnitude_stats']['mean']
            std_magnitude = quality_metrics['magnitude_stats']['std_dev']
            
            # Эмбеддинги с очень низкой или высокой магнитудой могут быть проблематичными
            anomalous_count = 0
            for mag in magnitudes:
                if abs(mag - mean_magnitude) > 3 * std_magnitude:
                    anomalous_count += 1
            
            if anomalous_count > len(magnitudes) * 0.1:  # Более 10% аномальных
                self.warnings.append(f"High number of anomalous embeddings: {anomalous_count}/{len(magnitudes)}")
            
            # Проверить на нулевые эмбеддинги
            zero_magnitude_count = sum(1 for mag in magnitudes if mag < 1e-10)
            if zero_magnitude_count > 0:
                self.warnings.append(f"Found {zero_magnitude_count} near-zero magnitude embeddings")
            
            conn.close()
            
            self.validation_results['embedding_quality'] = {
                'valid': True,
                'metrics': quality_metrics,
                'anomalous_embeddings': anomalous_count,
                'zero_magnitude_embeddings': zero_magnitude_count
            }
            
            logger.info("✅ Embedding quality validation passed")
            logger.info(f"   Sample size: {len(samples)}")
            logger.info(f"   Mean magnitude: {mean_magnitude:.4f}")
            logger.info(f"   Anomalous embeddings: {anomalous_count}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Embedding quality validation failed: {e}")
            logger.error(f"❌ Embedding quality validation failed: {e}")
            return False
    
    def validate_migration_completeness(self) -> bool:
        """Проверить полноту миграции"""
        logger.info("Validating migration completeness...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверить, что все документы имеют хотя бы один эмбеддинг
            cursor.execute("""
                SELECT COUNT(*) FROM documents d
                LEFT JOIN embeddings e ON d.id = e.document_id
                WHERE e.document_id IS NULL
            """)
            documents_without_embeddings = cursor.fetchone()[0]
            
            # Проверить, что все документы имеют Yandex эмбеддинг
            cursor.execute("""
                SELECT COUNT(*) FROM documents d
                LEFT JOIN embeddings e ON d.id = e.document_id AND e.provider = 'yandex_cloud'
                WHERE e.document_id IS NULL
            """)
            documents_without_yandex = cursor.fetchone()[0]
            
            # Проверить дублирующиеся эмбеддинги
            cursor.execute("""
                SELECT document_id, provider, model, COUNT(*) as count
                FROM embeddings
                GROUP BY document_id, provider, model
                HAVING COUNT(*) > 1
            """)
            duplicate_embeddings = cursor.fetchall()
            
            # Проверить старые провайдеры
            cursor.execute("""
                SELECT DISTINCT provider FROM embeddings
                WHERE provider != 'yandex_cloud'
            """)
            old_providers = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Оценка полноты миграции
            migration_complete = (
                documents_without_yandex == 0 and
                len(duplicate_embeddings) == 0
            )
            
            if documents_without_embeddings > 0:
                self.warnings.append(f"Found {documents_without_embeddings} documents without any embeddings")
            
            if documents_without_yandex > 0:
                self.errors.append(f"Found {documents_without_yandex} documents without Yandex embeddings")
            
            if duplicate_embeddings:
                self.warnings.append(f"Found {len(duplicate_embeddings)} duplicate embedding entries")
            
            if old_providers:
                self.warnings.append(f"Old embedding providers still present: {old_providers}")
            
            self.validation_results['migration_completeness'] = {
                'valid': migration_complete,
                'documents_without_embeddings': documents_without_embeddings,
                'documents_without_yandex': documents_without_yandex,
                'duplicate_embeddings': len(duplicate_embeddings),
                'old_providers': old_providers,
                'migration_complete': migration_complete
            }
            
            if migration_complete:
                logger.info("✅ Migration completeness validation passed")
            else:
                logger.warning("⚠️  Migration completeness validation has issues")
            
            return migration_complete
            
        except Exception as e:
            self.errors.append(f"Migration completeness validation failed: {e}")
            logger.error(f"❌ Migration completeness validation failed: {e}")
            return False
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Запустить полную валидацию"""
        logger.info("Starting full validation...")
        
        validation_start = datetime.now()
        
        # Запустить все проверки
        validations = [
            ('database_structure', self.validate_database_structure),
            ('data_consistency', self.validate_data_consistency),
            ('yandex_embeddings', self.validate_yandex_embeddings),
            ('embedding_quality', self.validate_embedding_quality),
            ('migration_completeness', self.validate_migration_completeness)
        ]
        
        passed_validations = 0
        total_validations = len(validations)
        
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                if result:
                    passed_validations += 1
                    logger.info(f"✅ {validation_name} validation passed")
                else:
                    logger.error(f"❌ {validation_name} validation failed")
            except Exception as e:
                logger.error(f"❌ {validation_name} validation error: {e}")
                self.errors.append(f"{validation_name} validation error: {e}")
        
        validation_end = datetime.now()
        
        # Создать итоговый отчет
        validation_report = {
            'validation_id': validation_start.strftime("%Y%m%d_%H%M%S"),
            'database_path': self.db_path,
            'validation_start': validation_start.isoformat(),
            'validation_end': validation_end.isoformat(),
            'duration_seconds': (validation_end - validation_start).total_seconds(),
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'failed_validations': total_validations - passed_validations,
            'success_rate': (passed_validations / total_validations) * 100,
            'overall_valid': passed_validations == total_validations,
            'validation_results': self.validation_results,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        # Логирование итогов
        logger.info(f"\n{'='*60}")
        logger.info("VALIDATION SUMMARY")
        logger.info('='*60)
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Duration: {validation_report['duration_seconds']:.2f}s")
        logger.info(f"Validations: {passed_validations}/{total_validations} passed")
        logger.info(f"Success rate: {validation_report['success_rate']:.1f}%")
        
        if validation_report['overall_valid']:
            logger.info("🎉 ALL VALIDATIONS PASSED!")
        else:
            logger.error("⚠️  SOME VALIDATIONS FAILED")
        
        if self.errors:
            logger.error(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        if self.warnings:
            logger.warning(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")
        
        return validation_report
    
    def save_validation_report(self, report: Dict[str, Any], output_file: str = None) -> str:
        """Сохранить отчет валидации"""
        if output_file is None:
            output_file = f"validation_report_{report['validation_id']}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Validation report saved: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
            return None

def main():
    """Main validation script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate database migration")
    parser.add_argument(
        '--database',
        default='files/vector_db.sqlite',
        help='Path to the database file'
    )
    parser.add_argument(
        '--output',
        help='Output file for validation report'
    )
    parser.add_argument(
        '--validation',
        choices=['structure', 'consistency', 'yandex', 'quality', 'completeness', 'all'],
        default='all',
        help='Specific validation to run'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    validator = DataIntegrityValidator(args.database)
    
    try:
        if args.validation == 'all':
            report = validator.run_full_validation()
        else:
            # Run specific validation
            validation_methods = {
                'structure': validator.validate_database_structure,
                'consistency': validator.validate_data_consistency,
                'yandex': validator.validate_yandex_embeddings,
                'quality': validator.validate_embedding_quality,
                'completeness': validator.validate_migration_completeness
            }
            
            method = validation_methods[args.validation]
            result = method()
            
            report = {
                'validation_type': args.validation,
                'result': result,
                'validation_results': validator.validation_results,
                'errors': validator.errors,
                'warnings': validator.warnings
            }
        
        # Save report
        if args.output:
            validator.save_validation_report(report, args.output)
        else:
            validator.save_validation_report(report)
        
        # Return appropriate exit code
        if report.get('overall_valid', result if 'result' in report else False):
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())