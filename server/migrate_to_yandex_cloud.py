#!/usr/bin/env python3
"""
Система миграции данных для перехода на Yandex Cloud эмбеддинги
Обеспечивает безопасную миграцию существующих векторных баз данных
"""

import os
import sys
import json
import sqlite3
import hashlib
import asyncio
import argparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """Base exception for migration errors"""
    pass

class MigrationValidationError(MigrationError):
    """Exception for validation errors during migration"""
    pass

class MigrationRollbackError(MigrationError):
    """Exception for rollback errors"""
    pass

class DatabaseMigrator:
    """Main class for database migration to Yandex Cloud embeddings"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('database_path', 'files/vector_db.sqlite')
        self.backup_path = config.get('backup_path', 'files/migration_backup')
        self.batch_size = config.get('batch_size', 100)
        self.dry_run = config.get('dry_run', False)
        
        # Migration state
        self.migration_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.migration_log = []
        self.rollback_data = {}
        
        # Statistics
        self.stats = {
            'total_documents': 0,
            'migrated_documents': 0,
            'failed_documents': 0,
            'total_embeddings': 0,
            'migrated_embeddings': 0,
            'failed_embeddings': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"Migration initialized with ID: {self.migration_id}")
    
    def validate_environment(self) -> bool:
        """Validate that environment is ready for migration"""
        logger.info("Validating migration environment...")
        
        required_vars = ['YANDEX_API_KEY', 'YANDEX_FOLDER_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        # Check if database exists
        if not Path(self.db_path).exists():
            logger.error(f"Database not found: {self.db_path}")
            return False
        
        # Check if Yandex Cloud components are available
        try:
            from yandex_embeddings import YandexEmbeddings
            from yandex_cloud_adapter import YandexCloudAdapter, YandexCloudConfig
            logger.info("Yandex Cloud components available")
        except ImportError as e:
            logger.error(f"Yandex Cloud components not available: {e}")
            return False
        
        # Test Yandex Cloud connection
        try:
            config = YandexCloudConfig.from_env()
            adapter = YandexCloudAdapter(config)
            logger.info("Yandex Cloud connection validated")
        except Exception as e:
            logger.error(f"Failed to connect to Yandex Cloud: {e}")
            return False
        
        logger.info("Environment validation completed successfully")
        return True
    
    def create_backup(self) -> str:
        """Create backup of current database"""
        logger.info("Creating database backup...")
        
        backup_dir = Path(self.backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"vector_db_backup_{self.migration_id}.sqlite"
        
        try:
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            # Create backup metadata
            metadata = {
                'migration_id': self.migration_id,
                'original_db_path': str(self.db_path),
                'backup_created_at': datetime.now().isoformat(),
                'backup_size_bytes': backup_file.stat().st_size
            }
            
            metadata_file = backup_dir / f"backup_metadata_{self.migration_id}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise MigrationError(f"Backup creation failed: {e}")
    
    def analyze_existing_data(self) -> Dict[str, Any]:
        """Analyze existing database structure and data"""
        logger.info("Analyzing existing database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            analysis = {
                'tables': tables,
                'document_count': 0,
                'embedding_count': 0,
                'embedding_dimensions': None,
                'sample_documents': []
            }
            
            # Analyze documents table if exists
            if 'documents' in tables:
                cursor.execute("SELECT COUNT(*) FROM documents")
                analysis['document_count'] = cursor.fetchone()[0]
                
                # Get sample documents
                cursor.execute("SELECT id, content, metadata FROM documents LIMIT 5")
                analysis['sample_documents'] = [
                    {'id': row[0], 'content': row[1][:100] + '...', 'metadata': row[2]}
                    for row in cursor.fetchall()
                ]
            
            # Analyze embeddings table if exists
            if 'embeddings' in tables:
                cursor.execute("SELECT COUNT(*) FROM embeddings")
                analysis['embedding_count'] = cursor.fetchone()[0]
                
                # Get embedding dimensions
                cursor.execute("SELECT embedding FROM embeddings LIMIT 1")
                sample_embedding = cursor.fetchone()
                if sample_embedding:
                    try:
                        embedding_data = json.loads(sample_embedding[0])
                        analysis['embedding_dimensions'] = len(embedding_data)
                    except:
                        pass
            
            conn.close()
            
            self.stats['total_documents'] = analysis['document_count']
            self.stats['total_embeddings'] = analysis['embedding_count']
            
            logger.info(f"Database analysis completed:")
            logger.info(f"  Tables: {analysis['tables']}")
            logger.info(f"  Documents: {analysis['document_count']}")
            logger.info(f"  Embeddings: {analysis['embedding_count']}")
            logger.info(f"  Embedding dimensions: {analysis['embedding_dimensions']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze database: {e}")
            raise MigrationError(f"Database analysis failed: {e}")
    
    async def migrate_embeddings(self) -> bool:
        """Migrate embeddings to Yandex Cloud format"""
        logger.info("Starting embeddings migration...")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
        
        try:
            # Mock langchain_core for embeddings
            import sys
            from unittest.mock import MagicMock
            
            class MockEmbeddings:
                pass
            
            sys.modules['langchain_core'] = MagicMock()
            sys.modules['langchain_core.embeddings'] = MagicMock()
            sys.modules['langchain_core.embeddings'].Embeddings = MockEmbeddings
            
            from yandex_embeddings import YandexEmbeddings
            
            # Initialize Yandex embeddings
            yandex_embeddings = YandexEmbeddings(
                model="text-search-doc",
                cache_enabled=True
            )
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all documents that need new embeddings
            cursor.execute("""
                SELECT id, content, metadata 
                FROM documents 
                WHERE id NOT IN (
                    SELECT document_id FROM embeddings 
                    WHERE provider = 'yandex_cloud'
                )
                ORDER BY id
            """)
            
            documents_to_migrate = cursor.fetchall()
            total_docs = len(documents_to_migrate)
            
            logger.info(f"Found {total_docs} documents to migrate")
            
            if total_docs == 0:
                logger.info("No documents need migration")
                return True
            
            # Process documents in batches
            migrated_count = 0
            failed_count = 0
            
            for i in range(0, total_docs, self.batch_size):
                batch = documents_to_migrate[i:i + self.batch_size]
                batch_texts = [doc[1] for doc in batch]  # content
                batch_ids = [doc[0] for doc in batch]    # ids
                
                logger.info(f"Processing batch {i//self.batch_size + 1}/{(total_docs + self.batch_size - 1)//self.batch_size}")
                
                try:
                    # Create embeddings for batch
                    if not self.dry_run:
                        batch_embeddings = yandex_embeddings.embed_documents(batch_texts)
                        
                        # Store new embeddings
                        for doc_id, embedding in zip(batch_ids, batch_embeddings):
                            cursor.execute("""
                                INSERT OR REPLACE INTO embeddings 
                                (document_id, embedding, provider, model, created_at)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                doc_id,
                                json.dumps(embedding),
                                'yandex_cloud',
                                'text-search-doc',
                                datetime.now().isoformat()
                            ))
                        
                        conn.commit()
                    
                    migrated_count += len(batch)
                    self.stats['migrated_embeddings'] += len(batch)
                    
                    logger.info(f"Migrated batch: {len(batch)} documents")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate batch: {e}")
                    failed_count += len(batch)
                    self.stats['failed_embeddings'] += len(batch)
                    
                    # Continue with next batch
                    continue
            
            conn.close()
            
            logger.info(f"Embeddings migration completed:")
            logger.info(f"  Migrated: {migrated_count}")
            logger.info(f"  Failed: {failed_count}")
            
            self.stats['migrated_documents'] = migrated_count
            self.stats['failed_documents'] = failed_count
            
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Embeddings migration failed: {e}")
            raise MigrationError(f"Embeddings migration failed: {e}")
    
    def validate_migration(self) -> bool:
        """Validate migration results"""
        logger.info("Validating migration results...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if all documents have Yandex Cloud embeddings
            cursor.execute("""
                SELECT COUNT(*) FROM documents d
                LEFT JOIN embeddings e ON d.id = e.document_id 
                WHERE e.provider = 'yandex_cloud'
            """)
            yandex_embeddings_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_documents = cursor.fetchone()[0]
            
            # Check embedding dimensions consistency
            cursor.execute("""
                SELECT embedding FROM embeddings 
                WHERE provider = 'yandex_cloud' 
                LIMIT 10
            """)
            
            embedding_samples = cursor.fetchall()
            dimensions = set()
            
            for sample in embedding_samples:
                try:
                    embedding_data = json.loads(sample[0])
                    dimensions.add(len(embedding_data))
                except:
                    pass
            
            conn.close()
            
            # Validation checks
            validation_results = {
                'total_documents': total_documents,
                'yandex_embeddings': yandex_embeddings_count,
                'coverage_percentage': (yandex_embeddings_count / total_documents * 100) if total_documents > 0 else 0,
                'embedding_dimensions': list(dimensions),
                'dimension_consistency': len(dimensions) <= 1
            }
            
            logger.info(f"Validation results:")
            logger.info(f"  Total documents: {validation_results['total_documents']}")
            logger.info(f"  Yandex embeddings: {validation_results['yandex_embeddings']}")
            logger.info(f"  Coverage: {validation_results['coverage_percentage']:.1f}%")
            logger.info(f"  Embedding dimensions: {validation_results['embedding_dimensions']}")
            
            # Determine if migration is valid
            is_valid = (
                validation_results['coverage_percentage'] >= 95.0 and  # At least 95% coverage
                validation_results['dimension_consistency']  # Consistent dimensions
            )
            
            if is_valid:
                logger.info("✅ Migration validation passed")
            else:
                logger.error("❌ Migration validation failed")
                if validation_results['coverage_percentage'] < 95.0:
                    logger.error(f"  Low coverage: {validation_results['coverage_percentage']:.1f}% < 95%")
                if not validation_results['dimension_consistency']:
                    logger.error(f"  Inconsistent dimensions: {validation_results['embedding_dimensions']}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            raise MigrationValidationError(f"Validation failed: {e}")
    
    def create_rollback_point(self) -> str:
        """Create rollback point before migration"""
        logger.info("Creating rollback point...")
        
        rollback_file = f"rollback_data_{self.migration_id}.json"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current embeddings state
            cursor.execute("""
                SELECT document_id, embedding, provider, model, created_at
                FROM embeddings
                WHERE provider = 'yandex_cloud'
            """)
            
            current_yandex_embeddings = [
                {
                    'document_id': row[0],
                    'embedding': row[1],
                    'provider': row[2],
                    'model': row[3],
                    'created_at': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            rollback_data = {
                'migration_id': self.migration_id,
                'created_at': datetime.now().isoformat(),
                'yandex_embeddings_before_migration': current_yandex_embeddings,
                'database_path': self.db_path
            }
            
            with open(rollback_file, 'w') as f:
                json.dump(rollback_data, f, indent=2)
            
            conn.close()
            
            logger.info(f"Rollback point created: {rollback_file}")
            return rollback_file
            
        except Exception as e:
            logger.error(f"Failed to create rollback point: {e}")
            raise MigrationError(f"Rollback point creation failed: {e}")
    
    def rollback_migration(self, rollback_file: str) -> bool:
        """Rollback migration to previous state"""
        logger.info(f"Rolling back migration using: {rollback_file}")
        
        try:
            # Load rollback data
            with open(rollback_file, 'r') as f:
                rollback_data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove all Yandex Cloud embeddings created during migration
            cursor.execute("DELETE FROM embeddings WHERE provider = 'yandex_cloud'")
            
            # Restore previous Yandex Cloud embeddings if any
            for embedding_data in rollback_data['yandex_embeddings_before_migration']:
                cursor.execute("""
                    INSERT INTO embeddings 
                    (document_id, embedding, provider, model, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    embedding_data['document_id'],
                    embedding_data['embedding'],
                    embedding_data['provider'],
                    embedding_data['model'],
                    embedding_data['created_at']
                ))
            
            conn.commit()
            conn.close()
            
            logger.info("Migration rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise MigrationRollbackError(f"Rollback failed: {e}")
    
    def generate_migration_report(self) -> str:
        """Generate detailed migration report"""
        report_file = f"migration_report_{self.migration_id}.json"
        
        report = {
            'migration_id': self.migration_id,
            'migration_completed_at': datetime.now().isoformat(),
            'configuration': self.config,
            'statistics': self.stats,
            'migration_log': self.migration_log,
            'validation_passed': self.validate_migration() if not self.dry_run else None
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Migration report generated: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return None
    
    async def run_migration(self) -> bool:
        """Run complete migration process"""
        logger.info(f"Starting migration process (ID: {self.migration_id})")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Step 1: Validate environment
            if not self.validate_environment():
                raise MigrationError("Environment validation failed")
            
            # Step 2: Analyze existing data
            analysis = self.analyze_existing_data()
            
            # Step 3: Create backup
            backup_file = self.create_backup()
            
            # Step 4: Create rollback point
            rollback_file = self.create_rollback_point()
            
            # Step 5: Migrate embeddings
            migration_success = await self.migrate_embeddings()
            
            # Step 6: Validate migration
            if not self.dry_run:
                validation_success = self.validate_migration()
                if not validation_success:
                    logger.error("Migration validation failed, rolling back...")
                    self.rollback_migration(rollback_file)
                    raise MigrationValidationError("Migration validation failed")
            
            self.stats['end_time'] = datetime.now()
            
            # Step 7: Generate report
            report_file = self.generate_migration_report()
            
            logger.info("Migration completed successfully!")
            logger.info(f"  Duration: {self.stats['end_time'] - self.stats['start_time']}")
            logger.info(f"  Migrated documents: {self.stats['migrated_documents']}")
            logger.info(f"  Failed documents: {self.stats['failed_documents']}")
            logger.info(f"  Backup: {backup_file}")
            logger.info(f"  Report: {report_file}")
            
            return True
            
        except Exception as e:
            self.stats['end_time'] = datetime.now()
            logger.error(f"Migration failed: {e}")
            
            # Generate failure report
            self.generate_migration_report()
            
            return False

def main():
    """Main migration script"""
    parser = argparse.ArgumentParser(description="Migrate vector database to Yandex Cloud embeddings")
    
    parser.add_argument(
        '--database-path',
        default='files/vector_db.sqlite',
        help='Path to the vector database file'
    )
    
    parser.add_argument(
        '--backup-path',
        default='files/migration_backup',
        help='Path for backup files'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing documents'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run migration in dry-run mode (no actual changes)'
    )
    
    parser.add_argument(
        '--rollback',
        help='Rollback migration using specified rollback file'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing migration'
    )
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        'database_path': args.database_path,
        'backup_path': args.backup_path,
        'batch_size': args.batch_size,
        'dry_run': args.dry_run
    }
    
    migrator = DatabaseMigrator(config)
    
    try:
        if args.rollback:
            # Rollback mode
            logger.info("Running in rollback mode")
            success = migrator.rollback_migration(args.rollback)
            
        elif args.validate_only:
            # Validation only mode
            logger.info("Running validation only")
            success = migrator.validate_migration()
            
        else:
            # Normal migration mode
            logger.info("Running migration")
            success = asyncio.run(migrator.run_migration())
        
        if success:
            logger.info("✅ Operation completed successfully")
            return 0
        else:
            logger.error("❌ Operation failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())