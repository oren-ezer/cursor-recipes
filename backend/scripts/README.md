# Database Backup and Restore Scripts

This directory contains scripts for backing up and restoring your Recipe Application database.

## Files

- `db_backup_restore.py` - Main Python script with backup/restore logic
- `backup_restore.sh` - Shell wrapper script for easier usage
- `README.md` - This documentation file

## Prerequisites

1. **Environment Setup**: Ensure you have the required environment variables:
   ```bash
   export DATABASE_URL="postgresql://username:password@host:port/database"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional
   ```

2. **Dependencies**: The script uses the existing project dependencies via `uv`.

## Quick Start

### Using the Shell Script (Recommended)

```bash
# Navigate to the backend directory
cd backend

# Create a backup
./scripts/backup_restore.sh dump

# Create a backup with custom name
./scripts/backup_restore.sh dump my_backup_name

# List available backups
./scripts/backup_restore.sh list

# Restore from backup
./scripts/backup_restore.sh upload my_backup_name

# Show database statistics
./scripts/backup_restore.sh stats

# Show help
./scripts/backup_restore.sh help
```

### Using the Python Script Directly

```bash
# Navigate to the backend directory
cd backend

# Create a backup
uv run python scripts/db_backup_restore.py dump --output-dir ./backups/my_backup

# Upload data to database
uv run python scripts/db_backup_restore.py upload --input-dir ./backups/my_backup

# Skip database structure verification during upload
uv run python scripts/db_backup_restore.py upload --input-dir ./backups/my_backup --skip-verification

# Show database statistics
uv run python scripts/db_backup_restore.py stats

# Use custom database URL
uv run python scripts/db_backup_restore.py dump --output-dir ./backups/custom --database-url "postgresql://..."
```

## How It Works

### Dump Mode

1. **Connects** to the database using the provided DATABASE_URL
2. **Extracts** all data from tables in the correct order:
   - users
   - tags  
   - recipes
   - recipe_tags
3. **Converts** each record to JSON format, handling datetime fields
4. **Saves** each table's data to a separate JSON file
5. **Creates** a metadata file (`backup_info.json`) with backup information

### Upload Mode

1. **Verifies** database structure (can be skipped with `--skip-verification`)
2. **Loads** backup metadata to validate the backup
3. **Clears** existing data from all tables (in reverse dependency order)
4. **Uploads** data from JSON files (in correct dependency order)
5. **Updates** database sequences for auto-increment columns
6. **Provides** final statistics

### Database Structure Verification

The script verifies that the target database has the expected:
- Tables: `users`, `recipes`, `tags`, `recipe_tags`
- Critical columns for each table
- Proper relationships and constraints

## File Structure

```
backend/
├── scripts/
│   ├── db_backup_restore.py    # Main Python script
│   ├── backup_restore.sh       # Shell wrapper
│   └── README.md              # This file
├── backups/                   # Created automatically
│   ├── backup_20241201_143022/
│   │   ├── users.json
│   │   ├── tags.json
│   │   ├── recipes.json
│   │   ├── recipe_tags.json
│   │   └── backup_info.json
│   └── my_custom_backup/
│       └── ...
└── ...
```

## Backup File Format

Each table's data is stored as a JSON array of objects:

```json
[
  {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00.000000",
    ...
  }
]
```

The `backup_info.json` contains metadata:

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "database_url": "host.example.com:5432/database",
  "tables": {
    "users": {
      "count": 150,
      "file": "users.json"
    },
    ...
  }
}
```

## Safety Features

- **Structure Verification**: Ensures target database has correct schema
- **Confirmation Prompts**: Shell script asks for confirmation before destructive operations
- **Logging**: Comprehensive logging to both console and `db_backup_restore.log`
- **Error Handling**: Graceful handling of errors with detailed messages
- **Sequence Updates**: Automatically updates auto-increment sequences after restore

## Common Use Cases

### 1. Before Database Migration
```bash
# Create backup before running migrations
./scripts/backup_restore.sh dump pre_migration_backup
```

### 2. Environment Setup
```bash
# Dump from production
DATABASE_URL="postgresql://prod-url" ./scripts/backup_restore.sh dump prod_data

# Upload to development
DATABASE_URL="postgresql://dev-url" ./scripts/backup_restore.sh upload prod_data
```

### 3. Testing Data Reset
```bash
# Create test data backup
./scripts/backup_restore.sh dump clean_test_data

# Reset to clean state anytime
./scripts/backup_restore.sh upload clean_test_data
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x scripts/backup_restore.sh
   ```

2. **Database Connection Error**
   - Verify `DATABASE_URL` is correct
   - Ensure database server is running
   - Check network connectivity

3. **Missing Dependencies**
   ```bash
   uv sync  # Install dependencies
   ```

4. **Structure Verification Failed**
   - Run database migrations first: `uv run alembic upgrade head`
   - Use `--skip-verification` flag to bypass (not recommended)

### Debug Mode

For detailed debugging, check the log file:
```bash
tail -f db_backup_restore.log
```

## Security Considerations

- **Database URLs**: Never commit database URLs to version control
- **Backup Files**: Backup files contain sensitive data - store securely
- **Environment Variables**: Use `.env` files or secure environment variable management
- **Access Control**: Restrict access to backup files and scripts

## Performance

- **Large Datasets**: For very large databases, consider using PostgreSQL's native `pg_dump` and `pg_restore`
- **Network**: Upload/download times depend on database size and network speed
- **Memory**: Script loads entire tables into memory - monitor for large datasets