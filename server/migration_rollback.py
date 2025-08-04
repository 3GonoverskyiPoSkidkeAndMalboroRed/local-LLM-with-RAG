#!/usr/bin/env python3
"""
Система rollback для возврата к предыдущему состоянию после миграции
Обеспечивает безопасный откат изменений в случае проблем
"""

import os
import sys
import json
import sqlite3
import shutil
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

class RollbackError(Exception):
    """Base exception for rollback errors"""
    pass

class MigrationRollback:
    """Система rollback для миграции"""
    
    def __init__(self, db_path: str, backup_dir: str = "files/migration_backup"):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.rollback_log = []
        
        logger.info(f"Rollback system initialized for database: {db_path}")
    
    def list_available_backups(self) -> List[Dict[str, Any]]:
        """Получить список доступных бэкапов"""
        logger.info("Scanning for available backups...")
        
        if not self.backup_dir.exists():
            logger.warning(f"Backup directory does not exist: {self.backup_dir}")
            return []
        
        backups = []
        
        # Найти все файлы бэкапов
        for backup_file in self.backup_dir.glob("vector_db_backup_*.sqlite"):
            migration_id = backup_file.stem.replace("vector_db_backup_", "")
            
            # Найти соответствующий файл метаданных
            metadata_file = self.backup_dir / f"backup_metadata_{migration_id}.json"
            
            backup_info = {
                'migration_id': migration_id,
                'backup_file': str(backup_file),
                'backup_size': backup_file.stat().st_size,
                'backup_created': datetime.fromtimestamp(backup_file.stat().st_mtime),
                'metadata_file': str(metadata_file) if metadata_file.exists() else None,
                'metadata': None
            }
            
            # Загрузить метаданные если доступны
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        backup_info['metadata'] = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {migration_id}: {e}")
            
            backups.append(backup_info)
        
        # Сортировать по времени создания (новые первыми)
        backups.sort(key=lambda x: x['backup_created'], reverse=True)
        
        logger.info(f"Found {len(backups)} available backups")
        return backups
    
    def list_rollback_points(self) -> List[Dict[str, Any]]:
        """Получить список точек отката"""
        logger.info("Scanning for rollback points...")
        
        rollback_points = []
        
        # Найти все файлы rollback данных
        for rollback_file in Path('.').glob("rollback_data_*.json"):
            migration_id = rollback_file.stem.replace("rollback_data_", "")
            
            try:
                with open(rollback_file, 'r') as f:
                    rollback_data = json.load(f)
                
                rollback_info = {
                    'migration_id': migration_id,
                    'rollback_file': str(rollback_file),
                    'created_at': rollback_data.get('created_at'),
                    'database_path': rollback_data.get('database_path'),
                    'yandex_embeddings_count': len(rollback_data.get('yandex_embeddings_before_migration', [])),
                    'file_size': rollback_file.stat().st_size
                }
                
                rollback_points.append(rollback_info)
                
            except Exception as e:
                logger.warning(f"Failed to load rollback data from {rollback_file}: {e}")
        
        # Сортировать по времени создания (новые первыми)
        rollback_points.sort(key=lambda x: x['created_at'], reverse=True)
        
        logger.info(f"Found {len(rollback_points)} rollback points")
        return rollback_points
    
    def validate_backup(self, backup_file: str) -> bool:
        """Проверить целостность бэкапа"""
        logger.info(f"Validating backup: {backup_file}")
        
        try:
            # Проверить, что файл существует и не пустой
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Backup file does not exist: {backup_file}")
                return False
            
            if backup_path.stat().st_size == 0:
                logger.error(f"Backup file is empty: {backup_file}")
                return False
            
            # Проверить, что это валидная SQLite база данных
            conn = sqlite3.connect(backup_file)
            cursor = conn.cursor()
            
            # Проверить основные таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['documents', 'embeddings']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"Backup missing required tables: {missing_tables}")
                conn.close()
                return False
            
            # Проверить, что таблицы содержат данные
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            emb_count = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info(f"Backup validation passed:")
            logger.info(f"  Documents: {doc_count}")
            logger.info(f"  Embeddings: {emb_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup validation failed: {e}")
            return False
    
    def create_pre_rollback_backup(self) -> str:
        """Создать бэкап перед rollback"""
        logger.info("Creating pre-rollback backup...")
        
        try:
            # Создать директорию для бэкапов
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Создать имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_rollback_backup = self.backup_dir / f"pre_rollback_backup_{timestamp}.sqlite"
            
            # Скопировать текущую базу данных
            shutil.copy2(self.db_path, pre_rollback_backup)
            
            # Создать метаданные
            metadata = {
                'backup_type': 'pre_rollback',
                'original_db_path': str(self.db_path),
                'created_at': datetime.now().isoformat(),
                'backup_size_bytes': pre_rollback_backup.stat().st_size
            }
            
            metadata_file = self.backup_dir / f"pre_rollback_metadata_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Pre-rollback backup created: {pre_rollback_backup}")
            return str(pre_rollback_backup)
            
        except Exception as e:
            logger.error(f"Failed to create pre-rollback backup: {e}")
            raise RollbackError(f"Pre-rollback backup failed: {e}")
    
    def rollback_from_backup(self, backup_file: str, create_pre_rollback_backup: bool = True) -> bool:
        """Откатиться к состоянию из бэкапа"""
        logger.info(f"Starting rollback from backup: {backup_file}")
        
        try:
            # Проверить валидность бэкапа
            if not self.validate_backup(backup_file):
                raise RollbackError("Backup validation failed")
            
            # Создать бэкап текущего состояния
            if create_pre_rollback_backup:
                pre_rollback_backup = self.create_pre_rollback_backup()
                self.rollback_log.append(f"Pre-rollback backup created: {pre_rollback_backup}")
            
            # Заменить текущую базу данных бэкапом
            logger.info("Replacing current database with backup...")
            shutil.copy2(backup_file, self.db_path)
            
            # Проверить, что rollback прошел успешно
            if not self.validate_backup(self.db_path):
                raise RollbackError("Rollback validation failed")
            
            self.rollback_log.append(f"Database restored from backup: {backup_file}")
            logger.info("✅ Rollback from backup completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback from backup failed: {e}")
            self.rollback_log.append(f"Rollback failed: {e}")
            return False
    
    def rollback_from_rollback_point(self, rollback_file: str) -> bool:
        """Откатиться к состоянию из точки отката"""
        logger.info(f"Starting rollback from rollback point: {rollback_file}")
        
        try:
            # Загрузить данные отката
            with open(rollback_file, 'r') as f:
                rollback_data = json.load(f)
            
            # Создать бэкап текущего состояния
            pre_rollback_backup = self.create_pre_rollback_backup()
            self.rollback_log.append(f"Pre-rollback backup created: {pre_rollback_backup}")
            
            # Подключиться к базе данных
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Удалить все Yandex Cloud эмбеддинги
            cursor.execute("DELETE FROM embeddings WHERE provider = 'yandex_cloud'")
            deleted_count = cursor.rowcount
            
            logger.info(f"Deleted {deleted_count} Yandex Cloud embeddings")
            self.rollback_log.append(f"Deleted {deleted_count} Yandex Cloud embeddings")
            
            # Восстановить предыдущие Yandex Cloud эмбеддинги если они были
            previous_embeddings = rollback_data.get('yandex_embeddings_before_migration', [])
            
            restored_count = 0
            for embedding_data in previous_embeddings:
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
                restored_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Restored {restored_count} previous Yandex Cloud embeddings")
            self.rollback_log.append(f"Restored {restored_count} previous embeddings")
            
            logger.info("✅ Rollback from rollback point completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback from rollback point failed: {e}")
            self.rollback_log.append(f"Rollback failed: {e}")
            return False
    
    def cleanup_migration_artifacts(self, migration_id: str, dry_run: bool = True) -> Dict[str, Any]:
        """Очистить артефакты миграции"""
        logger.info(f"Cleaning up migration artifacts for: {migration_id}")
        
        artifacts_to_clean = {
            'backup_files': [],
            'rollback_files': [],
            'report_files': [],
            'log_files': []
        }
        
        # Найти файлы для очистки
        patterns = {
            'backup_files': [
                f"vector_db_backup_{migration_id}.sqlite",
                f"backup_metadata_{migration_id}.json",
                f"pre_rollback_backup_{migration_id}.sqlite",
                f"pre_rollback_metadata_{migration_id}.json"
            ],
            'rollback_files': [
                f"rollback_data_{migration_id}.json"
            ],
            'report_files': [
                f"migration_report_{migration_id}.json",
                f"validation_report_{migration_id}.json"
            ],
            'log_files': [
                f"migration_{migration_id}.log"
            ]
        }
        
        # Сканировать файлы
        for category, file_patterns in patterns.items():
            for pattern in file_patterns:
                # Проверить в текущей директории
                if Path(pattern).exists():
                    artifacts_to_clean[category].append(str(Path(pattern)))
                
                # Проверить в директории бэкапов
                backup_file = self.backup_dir / pattern
                if backup_file.exists():
                    artifacts_to_clean[category].append(str(backup_file))
        
        # Подсчитать общий размер
        total_size = 0
        total_files = 0
        
        for category, files in artifacts_to_clean.items():
            for file_path in files:
                try:
                    size = Path(file_path).stat().st_size
                    total_size += size
                    total_files += 1
                except:
                    pass
        
        cleanup_summary = {
            'migration_id': migration_id,
            'artifacts_found': artifacts_to_clean,
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'dry_run': dry_run,
            'cleaned_files': [],
            'cleanup_errors': []
        }
        
        if dry_run:
            logger.info(f"DRY RUN: Would clean {total_files} files ({total_size / (1024 * 1024):.2f} MB)")
            return cleanup_summary
        
        # Выполнить очистку
        for category, files in artifacts_to_clean.items():
            for file_path in files:
                try:
                    Path(file_path).unlink()
                    cleanup_summary['cleaned_files'].append(file_path)
                    logger.info(f"Deleted: {file_path}")
                except Exception as e:
                    cleanup_summary['cleanup_errors'].append(f"Failed to delete {file_path}: {e}")
                    logger.error(f"Failed to delete {file_path}: {e}")
        
        logger.info(f"Cleanup completed: {len(cleanup_summary['cleaned_files'])} files deleted")
        return cleanup_summary
    
    def generate_rollback_report(self) -> Dict[str, Any]:
        """Создать отчет о rollback"""
        report = {
            'rollback_timestamp': datetime.now().isoformat(),
            'database_path': self.db_path,
            'backup_directory': str(self.backup_dir),
            'rollback_log': self.rollback_log,
            'available_backups': self.list_available_backups(),
            'available_rollback_points': self.list_rollback_points()
        }
        
        return report
    
    def save_rollback_report(self, report: Dict[str, Any], output_file: str = None) -> str:
        """Сохранить отчет о rollback"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"rollback_report_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Rollback report saved: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save rollback report: {e}")
            return None

def main():
    """Main rollback script"""
    parser = argparse.ArgumentParser(description="Migration rollback system")
    
    parser.add_argument(
        '--database',
        default='files/vector_db.sqlite',
        help='Path to the database file'
    )
    
    parser.add_argument(
        '--backup-dir',
        default='files/migration_backup',
        help='Path to backup directory'
    )
    
    parser.add_argument(
        '--action',
        choices=['list-backups', 'list-rollback-points', 'rollback-backup', 'rollback-point', 'cleanup'],
        required=True,
        help='Action to perform'
    )
    
    parser.add_argument(
        '--backup-file',
        help='Backup file for rollback-backup action'
    )
    
    parser.add_argument(
        '--rollback-file',
        help='Rollback file for rollback-point action'
    )
    
    parser.add_argument(
        '--migration-id',
        help='Migration ID for cleanup action'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no actual changes)'
    )
    
    parser.add_argument(
        '--no-pre-backup',
        action='store_true',
        help='Skip creating pre-rollback backup'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    rollback_system = MigrationRollback(args.database, args.backup_dir)
    
    try:
        if args.action == 'list-backups':
            backups = rollback_system.list_available_backups()
            print(json.dumps(backups, indent=2, default=str))
        
        elif args.action == 'list-rollback-points':
            rollback_points = rollback_system.list_rollback_points()
            print(json.dumps(rollback_points, indent=2, default=str))
        
        elif args.action == 'rollback-backup':
            if not args.backup_file:
                logger.error("--backup-file is required for rollback-backup action")
                return 1
            
            success = rollback_system.rollback_from_backup(
                args.backup_file,
                create_pre_rollback_backup=not args.no_pre_backup
            )
            
            if success:
                logger.info("✅ Rollback from backup completed successfully")
                return 0
            else:
                logger.error("❌ Rollback from backup failed")
                return 1
        
        elif args.action == 'rollback-point':
            if not args.rollback_file:
                logger.error("--rollback-file is required for rollback-point action")
                return 1
            
            success = rollback_system.rollback_from_rollback_point(args.rollback_file)
            
            if success:
                logger.info("✅ Rollback from rollback point completed successfully")
                return 0
            else:
                logger.error("❌ Rollback from rollback point failed")
                return 1
        
        elif args.action == 'cleanup':
            if not args.migration_id:
                logger.error("--migration-id is required for cleanup action")
                return 1
            
            cleanup_result = rollback_system.cleanup_migration_artifacts(
                args.migration_id,
                dry_run=args.dry_run
            )
            
            print(json.dumps(cleanup_result, indent=2, default=str))
            return 0
        
        # Generate and save report
        report = rollback_system.generate_rollback_report()
        rollback_system.save_rollback_report(report)
        
        return 0
        
    except Exception as e:
        logger.error(f"Rollback operation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())