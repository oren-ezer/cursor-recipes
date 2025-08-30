#!/usr/bin/env python3
"""
Database Backup and Restore Script

This script provides two modes:
1. dump: Extract all data from database tables into JSON files
2. upload: Verify database structure and upload data from JSON files

Usage:
    python db_backup_restore.py dump --output-dir ./backup
    python db_backup_restore.py upload --input-dir ./backup

Environment variables required:
    DATABASE_URL: PostgreSQL connection string
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio

# Add the backend directory to Python path so we can import src modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlmodel import create_engine, Session, text, select
from sqlalchemy import inspect, MetaData
from src.core.config import settings
from src.models.user import User
from src.models.recipe import Recipe
from src.models.tag import Tag, TagCategory
from src.models.recipe_tag import RecipeTag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_backup_restore.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseBackupRestore:
    """
    Handle database backup and restore operations.
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize with database connection.
        
        Args:
            database_url: PostgreSQL connection string, defaults to settings.DATABASE_URL
        """
        self.database_url = database_url or settings.DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided")
        
        self.engine = create_engine(self.database_url)
        
        # Define table models in dependency order (for proper insertion)
        # Note: alembic_version is handled separately as it doesn't have a SQLModel class
        self.table_models = [
            ('users', User),
            ('tags', Tag),
            ('recipes', Recipe),
            ('recipe_tags', RecipeTag),
        ]
        
        logger.info(f"Initialized with database: {self.database_url.split('@')[1] if '@' in self.database_url else 'local'}")
    
    def verify_database_structure(self) -> bool:
        """
        Verify that the database has the expected structure.
        
        Returns:
            bool: True if structure is valid, False otherwise
        """
        try:
            logger.info("Verifying database structure...")
            
            with Session(self.engine) as session:
                inspector = inspect(self.engine)
                existing_tables = inspector.get_table_names()
                
                # Expected tables
                expected_tables = {'users', 'recipes', 'tags', 'recipe_tags', 'alembic_version'}
                missing_tables = expected_tables - set(existing_tables)
                
                if missing_tables:
                    logger.error(f"Missing tables: {missing_tables}")
                    return False
                
                # Verify critical columns exist
                table_columns = {
                    'users': ['id', 'uuid', 'email', 'full_name', 'hashed_password'],
                    'recipes': ['id', 'uuid', 'title', 'description', 'user_id'],
                    'tags': ['id', 'uuid', 'name', 'category', 'recipe_counter'],
                    'recipe_tags': ['id', 'recipe_id', 'tag_id']
                }
                
                for table_name, required_columns in table_columns.items():
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    missing_columns = set(required_columns) - set(columns)
                    
                    if missing_columns:
                        logger.error(f"Table {table_name} missing columns: {missing_columns}")
                        return False
                
                logger.info("Database structure verification passed")
                return True
                
        except Exception as e:
            logger.error(f"Database structure verification failed: {str(e)}")
            return False
    
    def dump_data(self, output_dir: str) -> bool:
        """
        Extract all data from database tables and save to JSON files.
        
        Args:
            output_dir: Directory to save backup files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting data dump to {output_path}")
            
            with Session(self.engine) as session:
                backup_info = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'database_url': self.database_url.split('@')[1] if '@' in self.database_url else 'local',
                    'tables': {}
                }
                
                # Dump application tables
                for table_name, model_class in self.table_models:
                    logger.info(f"Dumping table: {table_name}")
                    
                    # Get all records
                    stmt = select(model_class)
                    results = session.exec(stmt).all()
                    
                    # Convert to dictionaries
                    records = []
                    for record in results:
                        record_dict = record.model_dump()
                        
                        # Handle datetime fields
                        for key, value in record_dict.items():
                            if isinstance(value, datetime):
                                record_dict[key] = value.isoformat()
                        
                        records.append(record_dict)
                    
                    # Save to JSON file
                    table_file = output_path / f"{table_name}.json"
                    with open(table_file, 'w', encoding='utf-8') as f:
                        json.dump(records, f, indent=2, default=str)
                    
                    backup_info['tables'][table_name] = {
                        'count': len(records),
                        'file': f"{table_name}.json"
                    }
                    
                    logger.info(f"Dumped {len(records)} records from {table_name}")
                
                # Dump alembic_version table (doesn't have SQLModel class)
                logger.info("Dumping table: alembic_version")
                alembic_result = session.exec(text("SELECT version_num FROM alembic_version"))
                alembic_records = [{'version_num': row[0]} for row in alembic_result]
                
                # Save alembic_version to JSON file
                alembic_file = output_path / "alembic_version.json"
                with open(alembic_file, 'w', encoding='utf-8') as f:
                    json.dump(alembic_records, f, indent=2)
                
                backup_info['tables']['alembic_version'] = {
                    'count': len(alembic_records),
                    'file': 'alembic_version.json'
                }
                
                logger.info(f"Dumped {len(alembic_records)} records from alembic_version")
                
                # Save backup metadata
                metadata_file = output_path / "backup_info.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_info, f, indent=2)
                
                logger.info(f"Data dump completed successfully. Backup info saved to {metadata_file}")
                return True
                
        except Exception as e:
            logger.error(f"Data dump failed: {str(e)}")
            return False
    
    def upload_data(self, input_dir: str, verify_structure: bool = True) -> bool:
        """
        Upload data from JSON files to database.
        
        Args:
            input_dir: Directory containing backup files
            verify_structure: Whether to verify database structure first
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            input_path = Path(input_dir)
            if not input_path.exists():
                logger.error(f"Input directory does not exist: {input_path}")
                return False
            
            # Verify database structure if requested
            if verify_structure and not self.verify_database_structure():
                logger.error("Database structure verification failed. Aborting upload.")
                return False
            
            # Load backup metadata
            metadata_file = input_path / "backup_info.json"
            if not metadata_file.exists():
                logger.error(f"Backup metadata file not found: {metadata_file}")
                return False
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            logger.info(f"Starting data upload from backup created: {backup_info['timestamp']}")
            
            with Session(self.engine) as session:
                # Clear existing data in reverse order
                logger.info("Clearing existing data...")
                
                # Clear application tables
                for table_name, model_class in reversed(self.table_models):
                    count_before = session.exec(select(model_class)).all()
                    if count_before:
                        session.exec(text(f"DELETE FROM {table_name}"))
                        logger.info(f"Cleared {len(count_before)} records from {table_name}")
                
                # Clear alembic_version (should be done last as it's not dependent on other tables)
                alembic_count = session.exec(text("SELECT COUNT(*) FROM alembic_version")).first()
                if alembic_count and alembic_count > 0:
                    session.exec(text("DELETE FROM alembic_version"))
                    logger.info(f"Cleared {alembic_count} records from alembic_version")
                
                session.commit()
                
                # Upload data in dependency order
                for table_name, model_class in self.table_models:
                    table_file = input_path / f"{table_name}.json"
                    
                    if not table_file.exists():
                        logger.warning(f"Table file not found: {table_file}, skipping...")
                        continue
                    
                    logger.info(f"Uploading data to table: {table_name}")
                    
                    with open(table_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                    
                    if not records:
                        logger.info(f"No records to upload for {table_name}")
                        continue
                    
                    # Insert records
                    uploaded_count = 0
                    for record_data in records:
                        try:
                            # Handle datetime fields
                            for key, value in record_data.items():
                                if isinstance(value, str) and 'T' in value and ('.' in value or '+' in value or 'Z' in value):
                                    try:
                                        # Try to parse as ISO datetime
                                        parsed_dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                        # Ensure timezone awareness
                                        if parsed_dt.tzinfo is None:
                                            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                                        record_data[key] = parsed_dt
                                    except ValueError:
                                        # Keep as string if parsing fails
                                        pass
                            
                            # Create model instance
                            record = model_class(**record_data)
                            session.add(record)
                            uploaded_count += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to upload record to {table_name}: {record_data.get('id', 'unknown')} - {str(e)}")
                            continue
                    
                    session.commit()
                    logger.info(f"Uploaded {uploaded_count} records to {table_name}")
                
                # Upload alembic_version data
                alembic_file = input_path / "alembic_version.json"
                if alembic_file.exists():
                    logger.info("Uploading data to table: alembic_version")
                    
                    with open(alembic_file, 'r', encoding='utf-8') as f:
                        alembic_records = json.load(f)
                    
                    uploaded_count = 0
                    for record_data in alembic_records:
                        try:
                            # Insert alembic version directly with SQL
                            session.exec(text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"), 
                                       {'version_num': record_data['version_num']})
                            uploaded_count += 1
                        except Exception as e:
                            logger.error(f"Failed to upload alembic_version record: {record_data} - {str(e)}")
                            continue
                    
                    session.commit()
                    logger.info(f"Uploaded {uploaded_count} records to alembic_version")
                else:
                    logger.warning("alembic_version.json not found, skipping alembic version restore")
                
                # Update sequences for auto-increment columns
                logger.info("Updating database sequences...")
                for table_name, _ in self.table_models:
                    try:
                        session.exec(text(f"""
                            SELECT setval('{table_name}_id_seq', 
                                         COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, 
                                         false)
                        """))
                    except Exception as e:
                        logger.warning(f"Could not update sequence for {table_name}: {str(e)}")
                
                session.commit()
                
                logger.info("Data upload completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Data upload failed: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get current database statistics.
        
        Returns:
            Dict with table names and record counts
        """
        stats = {}
        try:
            with Session(self.engine) as session:
                # Get stats for application tables
                for table_name, model_class in self.table_models:
                    count = len(session.exec(select(model_class)).all())
                    stats[table_name] = count
                
                # Get stats for alembic_version
                alembic_result = session.exec(text("SELECT COUNT(*) FROM alembic_version")).first()
                stats['alembic_version'] = int(alembic_result[0]) if alembic_result else 0
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            
        return stats


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Database Backup and Restore Tool')
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Dump mode
    dump_parser = subparsers.add_parser('dump', help='Extract data from database')
    dump_parser.add_argument('--output-dir', required=True, help='Output directory for backup files')
    dump_parser.add_argument('--database-url', help='Database URL (defaults to env DATABASE_URL)')
    
    # Upload mode
    upload_parser = subparsers.add_parser('upload', help='Upload data to database')
    upload_parser.add_argument('--input-dir', required=True, help='Input directory containing backup files')
    upload_parser.add_argument('--database-url', help='Database URL (defaults to env DATABASE_URL)')
    upload_parser.add_argument('--skip-verification', action='store_true', 
                             help='Skip database structure verification')
    
    # Stats mode
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--database-url', help='Database URL (defaults to env DATABASE_URL)')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return 1
    
    try:
        # Initialize backup/restore handler
        db_handler = DatabaseBackupRestore(database_url=args.database_url)
        
        if args.mode == 'dump':
            logger.info(f"Starting dump mode - output directory: {args.output_dir}")
            success = db_handler.dump_data(args.output_dir)
            if success:
                logger.info("Dump completed successfully")
                return 0
            else:
                logger.error("Dump failed")
                return 1
                
        elif args.mode == 'upload':
            logger.info(f"Starting upload mode - input directory: {args.input_dir}")
            verify = not args.skip_verification
            success = db_handler.upload_data(args.input_dir, verify_structure=verify)
            if success:
                logger.info("Upload completed successfully")
                # Show final stats
                stats = db_handler.get_database_stats()
                logger.info(f"Final database stats: {stats}")
                return 0
            else:
                logger.error("Upload failed")
                return 1
                
        elif args.mode == 'stats':
            logger.info("Getting database statistics...")
            stats = db_handler.get_database_stats()
            print("\nDatabase Statistics:")
            print("-" * 30)
            for table, count in stats.items():
                print(f"{table:<15}: {count:>10}")
            print("-" * 30)
            total = sum(stats.values())
            print(f"{'Total':<15}: {total:>10}")
            return 0
            
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())
