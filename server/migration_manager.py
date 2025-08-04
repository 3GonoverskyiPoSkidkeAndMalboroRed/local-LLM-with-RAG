#!/usr/bin/env python3
"""
Главный менеджер системы миграции данных
Объединяет все компоненты миграции в единый интерфейс
"""

import os
import sys
import json
import argparse
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrate_to_yandex_cloud import DatabaseMigrator
from embedding_migration_utils import EmbeddingMigrationUtils, create_migration_summary
from migration_validator import DataIntegrityValidator
from migration_rollback import MigrationRollback

logger = logging.getLogger(__name__)

class MigrationManager:
    """Главный менеджер миграции"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('database_path', 'files/vector_db.sqlite')
        self.backup_dir = config.get('backup_path', 'files/migration_backup')
        
        # Инициализация компонентов
        self.migrator = DatabaseMigrator(config)
        self.validator = DataIntegrityValidator(self.db_path)
        self.rollback_system = MigrationRollback(self.db_path, self.backup_dir)
        
        logger.info("Migration Manager initialized")
    
    def print_banner(self):
        """Вывести баннер системы миграции"""
        print("=" * 80)
        print("🔄 YANDEX CLOUD MIGRATION SYSTEM")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Backup Directory: {self.backup_dir}")
        print(f"Migration Mode: {'DRY RUN' if self.config.get('dry_run') else 'LIVE'}")
        print("=" * 80)
        print()
    
    def analyze_migration_status(self) -> Dict[str, Any]:
        """Анализ текущего статуса миграции"""
        logger.info("Analyzing migration status...")
        
        try:
            # Создать сводку миграции
            summary = create_migration_summary(self.db_path)
            
            # Получить доступные бэкапы
            backups = self.rollback_system.list_available_backups()
            
            # Получить точки отката
            rollback_points = self.rollback_system.list_rollback_points()
            
            status = {
                'database_exists': Path(self.db_path).exists(),
                'migration_summary': summary,
                'available_backups': len(backups),
                'available_rollback_points': len(rollback_points),
                'migration_needed': summary.get('migration_needed', False),
                'latest_backup': backups[0] if backups else None,
                'latest_rollback_point': rollback_points[0] if rollback_points else None
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to analyze migration status: {e}")
            return {'error': str(e)}
    
    def print_migration_status(self, status: Dict[str, Any]):
        """Вывести статус миграции"""
        print("📊 MIGRATION STATUS")
        print("-" * 40)
        
        if 'error' in status:
            print(f"❌ Error: {status['error']}")
            return
        
        print(f"Database exists: {'✅' if status['database_exists'] else '❌'}")
        print(f"Migration needed: {'⚠️  Yes' if status['migration_needed'] else '✅ No'}")
        print(f"Available backups: {status['available_backups']}")
        print(f"Available rollback points: {status['available_rollback_points']}")
        
        if status['migration_summary']:
            summary = status['migration_summary']
            print(f"Documents without Yandex embeddings: {summary.get('documents_without_yandex_embeddings', 0)}")
            print(f"Embedding providers: {', '.join(summary.get('embedding_providers', []))}")
        
        if status['latest_backup']:
            backup = status['latest_backup']
            print(f"Latest backup: {backup['migration_id']} ({backup['backup_created']})")
        
        print()
    
    async def run_migration_workflow(self) -> bool:
        """Запустить полный workflow миграции"""
        logger.info("Starting migration workflow...")
        
        try:
            # Шаг 1: Анализ статуса
            print("🔍 Step 1: Analyzing migration status...")
            status = self.analyze_migration_status()
            self.print_migration_status(status)
            
            if not status.get('migration_needed', False):
                print("✅ No migration needed - all documents already have Yandex embeddings")
                return True
            
            # Шаг 2: Запуск миграции
            print("🚀 Step 2: Running database migration...")
            migration_success = await self.migrator.run_migration()
            
            if not migration_success:
                print("❌ Migration failed")
                return False
            
            # Шаг 3: Валидация
            if not self.config.get('dry_run', False):
                print("✅ Step 3: Validating migration results...")
                validation_report = self.validator.run_full_validation()
                
                if not validation_report['overall_valid']:
                    print("❌ Migration validation failed")
                    
                    # Предложить rollback
                    print("🔄 Would you like to rollback the migration? (y/N): ", end="")
                    response = input().strip().lower()
                    
                    if response == 'y':
                        print("🔄 Rolling back migration...")
                        # Найти последнюю точку отката
                        rollback_points = self.rollback_system.list_rollback_points()
                        if rollback_points:
                            latest_rollback = rollback_points[0]['rollback_file']
                            rollback_success = self.rollback_system.rollback_from_rollback_point(latest_rollback)
                            
                            if rollback_success:
                                print("✅ Rollback completed successfully")
                            else:
                                print("❌ Rollback failed")
                        else:
                            print("❌ No rollback points available")
                    
                    return False
            
            print("🎉 Migration workflow completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration workflow failed: {e}")
            print(f"❌ Migration workflow failed: {e}")
            return False
    
    def run_validation_workflow(self) -> bool:
        """Запустить workflow валидации"""
        logger.info("Starting validation workflow...")
        
        try:
            print("🔍 Running comprehensive validation...")
            validation_report = self.validator.run_full_validation()
            
            # Сохранить отчет
            report_file = self.validator.save_validation_report(validation_report)
            
            if validation_report['overall_valid']:
                print("✅ All validations passed!")
            else:
                print("⚠️  Some validations failed - check the report for details")
            
            print(f"📄 Validation report saved: {report_file}")
            return validation_report['overall_valid']
            
        except Exception as e:
            logger.error(f"Validation workflow failed: {e}")
            print(f"❌ Validation workflow failed: {e}")
            return False
    
    def run_rollback_workflow(self, rollback_type: str, rollback_target: str = None) -> bool:
        """Запустить workflow отката"""
        logger.info(f"Starting rollback workflow: {rollback_type}")
        
        try:
            if rollback_type == 'backup':
                if not rollback_target:
                    # Показать доступные бэкапы
                    backups = self.rollback_system.list_available_backups()
                    if not backups:
                        print("❌ No backups available for rollback")
                        return False
                    
                    print("📋 Available backups:")
                    for i, backup in enumerate(backups):
                        print(f"  {i+1}. {backup['migration_id']} - {backup['backup_created']} ({backup['backup_size']} bytes)")
                    
                    print("Select backup number (or 0 to cancel): ", end="")
                    try:
                        choice = int(input().strip())
                        if choice == 0:
                            print("Rollback cancelled")
                            return False
                        if 1 <= choice <= len(backups):
                            rollback_target = backups[choice-1]['backup_file']
                        else:
                            print("Invalid choice")
                            return False
                    except ValueError:
                        print("Invalid input")
                        return False
                
                print(f"🔄 Rolling back from backup: {rollback_target}")
                success = self.rollback_system.rollback_from_backup(rollback_target)
                
            elif rollback_type == 'rollback_point':
                if not rollback_target:
                    # Показать доступные точки отката
                    rollback_points = self.rollback_system.list_rollback_points()
                    if not rollback_points:
                        print("❌ No rollback points available")
                        return False
                    
                    print("📋 Available rollback points:")
                    for i, point in enumerate(rollback_points):
                        print(f"  {i+1}. {point['migration_id']} - {point['created_at']} ({point['yandex_embeddings_count']} embeddings)")
                    
                    print("Select rollback point number (or 0 to cancel): ", end="")
                    try:
                        choice = int(input().strip())
                        if choice == 0:
                            print("Rollback cancelled")
                            return False
                        if 1 <= choice <= len(rollback_points):
                            rollback_target = rollback_points[choice-1]['rollback_file']
                        else:
                            print("Invalid choice")
                            return False
                    except ValueError:
                        print("Invalid input")
                        return False
                
                print(f"🔄 Rolling back from rollback point: {rollback_target}")
                success = self.rollback_system.rollback_from_rollback_point(rollback_target)
            
            else:
                print(f"❌ Unknown rollback type: {rollback_type}")
                return False
            
            if success:
                print("✅ Rollback completed successfully!")
                
                # Запустить валидацию после отката
                print("🔍 Validating database after rollback...")
                validation_report = self.validator.run_full_validation()
                
                if validation_report['overall_valid']:
                    print("✅ Post-rollback validation passed")
                else:
                    print("⚠️  Post-rollback validation has issues")
                
                return True
            else:
                print("❌ Rollback failed")
                return False
                
        except Exception as e:
            logger.error(f"Rollback workflow failed: {e}")
            print(f"❌ Rollback workflow failed: {e}")
            return False
    
    def run_cleanup_workflow(self, migration_id: str = None, dry_run: bool = True) -> bool:
        """Запустить workflow очистки"""
        logger.info("Starting cleanup workflow...")
        
        try:
            if not migration_id:
                # Показать доступные миграции для очистки
                backups = self.rollback_system.list_available_backups()
                rollback_points = self.rollback_system.list_rollback_points()
                
                all_migrations = set()
                for backup in backups:
                    all_migrations.add(backup['migration_id'])
                for point in rollback_points:
                    all_migrations.add(point['migration_id'])
                
                if not all_migrations:
                    print("❌ No migration artifacts found for cleanup")
                    return False
                
                print("📋 Available migrations for cleanup:")
                migration_list = sorted(list(all_migrations))
                for i, mid in enumerate(migration_list):
                    print(f"  {i+1}. {mid}")
                
                print("Select migration number (or 0 to cancel): ", end="")
                try:
                    choice = int(input().strip())
                    if choice == 0:
                        print("Cleanup cancelled")
                        return False
                    if 1 <= choice <= len(migration_list):
                        migration_id = migration_list[choice-1]
                    else:
                        print("Invalid choice")
                        return False
                except ValueError:
                    print("Invalid input")
                    return False
            
            print(f"🧹 Cleaning up migration artifacts for: {migration_id}")
            cleanup_result = self.rollback_system.cleanup_migration_artifacts(migration_id, dry_run=dry_run)
            
            if dry_run:
                print(f"DRY RUN: Would clean {cleanup_result['total_files']} files ({cleanup_result['total_size_mb']:.2f} MB)")
            else:
                print(f"✅ Cleaned {len(cleanup_result['cleaned_files'])} files")
                if cleanup_result['cleanup_errors']:
                    print(f"⚠️  {len(cleanup_result['cleanup_errors'])} errors occurred")
            
            return True
            
        except Exception as e:
            logger.error(f"Cleanup workflow failed: {e}")
            print(f"❌ Cleanup workflow failed: {e}")
            return False

def main():
    """Main migration manager"""
    parser = argparse.ArgumentParser(description="Yandex Cloud Migration Manager")
    
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
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing documents'
    )
    
    parser.add_argument(
        '--workflow',
        choices=['migrate', 'validate', 'rollback', 'cleanup', 'status'],
        required=True,
        help='Workflow to execute'
    )
    
    parser.add_argument(
        '--rollback-type',
        choices=['backup', 'rollback_point'],
        help='Type of rollback for rollback workflow'
    )
    
    parser.add_argument(
        '--rollback-target',
        help='Specific backup file or rollback point file'
    )
    
    parser.add_argument(
        '--migration-id',
        help='Migration ID for cleanup workflow'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no actual changes)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration_manager.log'),
            logging.StreamHandler()
        ]
    )
    
    # Configuration
    config = {
        'database_path': args.database,
        'backup_path': args.backup_dir,
        'batch_size': args.batch_size,
        'dry_run': args.dry_run
    }
    
    manager = MigrationManager(config)
    manager.print_banner()
    
    try:
        if args.workflow == 'status':
            status = manager.analyze_migration_status()
            manager.print_migration_status(status)
            print(json.dumps(status, indent=2, default=str))
            return 0
        
        elif args.workflow == 'migrate':
            success = asyncio.run(manager.run_migration_workflow())
            return 0 if success else 1
        
        elif args.workflow == 'validate':
            success = manager.run_validation_workflow()
            return 0 if success else 1
        
        elif args.workflow == 'rollback':
            if not args.rollback_type:
                print("❌ --rollback-type is required for rollback workflow")
                return 1
            
            success = manager.run_rollback_workflow(args.rollback_type, args.rollback_target)
            return 0 if success else 1
        
        elif args.workflow == 'cleanup':
            success = manager.run_cleanup_workflow(args.migration_id, args.dry_run)
            return 0 if success else 1
        
        else:
            print(f"❌ Unknown workflow: {args.workflow}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Migration manager failed: {e}")
        print(f"❌ Migration manager failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())