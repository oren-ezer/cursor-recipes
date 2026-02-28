#!/bin/bash

# Database Backup and Restore Helper Script
# 
# This script provides easy-to-use commands for backing up and restoring
# your recipe application database.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$BACKEND_DIR/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
check_environment() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed or not in PATH"
        print_info "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    if [ ! -f "$BACKEND_DIR/pyproject.toml" ]; then
        print_error "pyproject.toml not found in $BACKEND_DIR"
        exit 1
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 {dump|upload|stats|help}"
    echo ""
    echo "Commands:"
    echo "  dump [backup_name]    - Create a backup of the current database"
    echo "  upload <backup_name>  - Restore database from a backup"
    echo "  stats                 - Show current database statistics"
    echo "  help                  - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dump                      # Create backup with timestamp"
    echo "  $0 dump prod_backup          # Create backup named 'prod_backup'"
    echo "  $0 upload prod_backup        # Restore from 'prod_backup'"
    echo "  $0 stats                     # Show database stats"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL    - PostgreSQL connection string (required)"
    echo "  OPENAI_API_KEY  - OpenAI API key (optional)"
    echo ""
}

# Create a database backup
create_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    fi
    
    local backup_path="$BACKUP_DIR/$backup_name"
    
    print_info "Creating backup: $backup_name"
    print_info "Backup location: $backup_path"
    
    # Create backup directory
    mkdir -p "$backup_path"
    
    # Run the backup script
    cd "$BACKEND_DIR"
    if uv run python scripts/db_backup_restore.py dump --output-dir "$backup_path"; then
        print_success "Backup created successfully: $backup_name"
        print_info "Backup files:"
        ls -la "$backup_path"
    else
        print_error "Backup failed"
        exit 1
    fi
}

# Restore from a database backup
restore_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        print_error "Backup name is required for restore operation"
        show_usage
        exit 1
    fi
    
    local backup_path="$BACKUP_DIR/$backup_name"
    
    print_error "================================================"
    print_error "backup_path: $backup_path"
    print_error "BACKUP_DIR: $BACKUP_DIR"
    print_error "backup_name: $backup_name"
    print_error "================================================"  
    if [ ! -d "$backup_path" ]; then
        print_error "Backup not found: $backup_path"
        print_info "Available backups:"
        if [ -d "$BACKUP_DIR" ]; then
            ls -1 "$BACKUP_DIR" 2>/dev/null || echo "  No backups found"
        else
            echo "  No backup directory found"
        fi
        exit 1
    fi
    
    print_warning "This will replace all data in the current database!"
    print_info "Restoring from backup: $backup_name"
    print_info "Backup location: $backup_path"
    
    # Ask for confirmation
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    # Run the restore script
    cd "$BACKEND_DIR"
    if uv run python scripts/db_backup_restore.py upload --input-dir "$backup_path"; then
        print_success "Database restored successfully from: $backup_name"
    else
        print_error "Restore failed"
        exit 1
    fi
}

# Show database statistics
show_stats() {
    print_info "Getting database statistics..."
    
    cd "$BACKEND_DIR"
    if uv run python scripts/db_backup_restore.py stats; then
        print_success "Statistics retrieved successfully"
    else
        print_error "Failed to get database statistics"
        exit 1
    fi
}

# List available backups
list_backups() {
    print_info "Available backups:"
    if [ -d "$BACKUP_DIR" ]; then
        if [ -n "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
            for backup in "$BACKUP_DIR"/*; do
                if [ -d "$backup" ]; then
                    local backup_name=$(basename "$backup")
                    local backup_info="$backup/backup_info.json"
                    if [ -f "$backup_info" ]; then
                        local timestamp=$(python3 -c "import json; print(json.load(open('$backup_info'))['timestamp'])" 2>/dev/null || echo "unknown")
                        echo "  $backup_name (created: $timestamp)"
                    else
                        echo "  $backup_name (no metadata)"
                    fi
                fi
            done
        else
            echo "  No backups found"
        fi
    else
        echo "  No backup directory found"
    fi
}

# Main script logic
main() {
    local command="$1"
    shift || true
    
    case "$command" in
        "dump")
            check_environment
            create_backup "$1"
            ;;
        "upload"|"restore")
            check_environment
            restore_backup "$1"
            ;;
        "stats")
            check_environment
            show_stats
            ;;
        "list")
            list_backups
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        "")
            print_error "No command specified"
            show_usage
            exit 1
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Check if script is being sourced or executed
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
