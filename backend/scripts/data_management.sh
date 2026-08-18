#!/bin/bash

# Data management helper: dump / upload / list / stats / clean
#
# All backups live under: backend/scripts/backups/<subfolder>/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
BACKUPS_DIR="${SCRIPT_DIR}/backups"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Database name from DATABASE_URL env or backend/.env (path after last /).
database_name_from_env() {
    local url="${DATABASE_URL:-}"
    if [ -z "$url" ] && [ -f "$BACKEND_DIR/.env" ]; then
        url="$(grep -E '^[[:space:]]*DATABASE_URL=' "$BACKEND_DIR/.env" | tail -1 | cut -d= -f2-)"
        url="${url#"${url%%[![:space:]]*}"}"
        url="${url%\"}"
        url="${url#\"}"
        url="${url%\'}"
        url="${url#\'}"
    fi
    url="${url%%\?*}"
    if [ -z "$url" ]; then
        echo "(unknown)"
        return
    fi
    echo "${url##*/}"
}

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

show_usage() {
    echo "Usage: $0 {dump|upload|upload_seed|upload_demo|build_db|list|stats|clean|help}"
    echo ""
    echo "All data is stored under: ${BACKUPS_DIR}/<subfolder>/"
    echo ""
    echo "Commands:"
    echo "  dump [subfolder]   - Create backup in backups/<subfolder>/ (default name: backup_YYYYMMDD_HHMMSS)"
    echo "                       Binary image BYTEA is stored as base64 in JSON (format 3)."
    echo "  upload <subfolder>      - Restore all tables from backups/<subfolder>/ (includes image blobs)"
    echo "  upload_seed <subfolder> - Restore only seed tables (users, tags, llm_configs, app_settings)"
    echo "  upload_demo <subfolder> - Restore seed + demo tables (+ recipes, recipe_tags, recipe_images, interactions)"
    echo "  build_db <subfolder> [seed|demo|full] - Drop/recreate public schema, alembic upgrade head, then populate"
    echo "                       Default dataset=demo (users/tags/llm_configs/app_settings/recipes/interactions)"
    echo "  list <subfolder>        - Show backup_info and files for backups/<subfolder>/"
    echo "  stats              - Show database row counts"
    echo "  clean              - Delete all rows (FK-safe; keeps alembic_version by default)"
    echo "  help               - This message"
    echo ""
    echo "Images / re-dump:"
    echo "  Backups older than format 3 may have broken recipe_images.data (\"<memory at …>\")."
    echo "  After upgrading the script, re-dump from a DB that still has real image bytes:"
    echo "    $0 dump seed_with_images"
    echo "  Then restore onto a clean migrated DB with: $0 upload seed_with_images"
    echo "  (or $0 upload_demo seed_with_images for a partial upsert)."
    echo "  Or rebuild everything in one step: $0 build_db seed_with_images"
    echo ""
    echo "Examples:"
    echo "  $0 dump"
    echo "  $0 dump my_snapshot"
    echo "  $0 list backup_20260228_214601"
    echo "  $0 upload backup_20260228_214601"
    echo "  $0 build_db seed_with_images_verify"
    echo "  $0 build_db seed_with_images_verify full"
    echo ""
}

create_backup() {
    local subfolder="$1"
    if [ -z "$subfolder" ]; then
        subfolder="backup_$(date +%Y%m%d_%H%M%S)"
    fi
    local backup_path="${BACKUPS_DIR}/${subfolder}"

    print_info "Backup subfolder:  ${subfolder}"
    print_info "Full path:         ${backup_path}"

    mkdir -p "$backup_path"

    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py dump "$subfolder"; then
        print_success "Backup created: ${backup_path}"
        print_info "Contents:"
        ls -la "$backup_path"
    else
        print_error "Dump failed"
        exit 1
    fi
}

restore_backup() {
    local subfolder="$1"
    if [ -z "$subfolder" ]; then
        print_error "upload requires a backup subfolder name."
        print_error "  Example: $0 upload backup_20260228_214601"
        print_error "  Backups live under: ${BACKUPS_DIR}/<subfolder>/"
        exit 1
    fi

    local backup_path="${BACKUPS_DIR}/${subfolder}"

    if [ ! -d "$BACKUPS_DIR" ]; then
        print_error "Backups directory does not exist: ${BACKUPS_DIR}"
        print_error "Run a dump first."
        exit 1
    fi

    if [ ! -d "$backup_path" ]; then
        print_error "Backup subfolder not found."
        print_error "  Subfolder name: ${subfolder}"
        print_error "  Expected path: ${backup_path}"
        if [ -n "$(ls -A "$BACKUPS_DIR" 2>/dev/null)" ]; then
            print_error "Existing subfolders under ${BACKUPS_DIR}:"
            ls -1 "$BACKUPS_DIR" 2>/dev/null | sed 's/^/    /' || true
        else
            print_error "  (backups dir exists but is empty)"
        fi
        exit 1
    fi

    print_warning "This will replace all data in the current database!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        exit 0
    fi

    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py upload "$subfolder"; then
        print_success "Restored from: ${backup_path}"
    else
        print_error "Upload failed"
        exit 1
    fi
}

list_one_backup() {
    local subfolder="$1"
    if [ -z "$subfolder" ]; then
        print_error "list requires a backup subfolder name."
        print_error "  Example: $0 list backup_20260228_214601"
        print_error "  Backups live under: ${BACKUPS_DIR}/<subfolder>/"
        exit 1
    fi

    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py list "$subfolder"; then
        return 0
    else
        exit 1
    fi
}

show_stats() {
    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py stats; then
        print_success "Statistics done"
    else
        print_error "stats failed"
        exit 1
    fi
}

partial_upload() {
    local mode="$1"
    local subfolder="$2"
    if [ -z "$subfolder" ]; then
        print_error "${mode} requires a backup subfolder name."
        print_error "  Example: $0 ${mode} backup_20260228_214601"
        print_error "  Backups live under: ${BACKUPS_DIR}/<subfolder>/"
        exit 1
    fi

    local backup_path="${BACKUPS_DIR}/${subfolder}"

    if [ ! -d "$BACKUPS_DIR" ]; then
        print_error "Backups directory does not exist: ${BACKUPS_DIR}"
        print_error "Run a dump first."
        exit 1
    fi

    if [ ! -d "$backup_path" ]; then
        print_error "Backup subfolder not found."
        print_error "  Subfolder name: ${subfolder}"
        print_error "  Expected path: ${backup_path}"
        if [ -n "$(ls -A "$BACKUPS_DIR" 2>/dev/null)" ]; then
            print_error "Existing subfolders under ${BACKUPS_DIR}:"
            ls -1 "$BACKUPS_DIR" 2>/dev/null | sed 's/^/    /' || true
        else
            print_error "  (backups dir exists but is empty)"
        fi
        exit 1
    fi

    print_warning "This will replace ${mode} tables in the current database!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        exit 0
    fi

    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py "${mode}" "$subfolder"; then
        print_success "Partial restore (${mode}) from: ${backup_path}"
    else
        print_error "${mode} failed"
        exit 1
    fi
}

clean_database() {
    print_warning "This will delete ALL rows in every table (alembic_version is kept)."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        exit 0
    fi

    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py clean --yes; then
        print_success "Database cleaned"
    else
        print_error "clean failed"
        exit 1
    fi
}

build_database() {
    local subfolder="$1"
    local dataset="${2:-demo}"

    if [ -z "$subfolder" ]; then
        print_error "build_db requires a backup subfolder name."
        print_error "  Example: $0 build_db seed_with_images_verify"
        print_error "  Optional dataset: seed | demo | full (default: demo)"
        print_error "  Backups live under: ${BACKUPS_DIR}/<subfolder>/"
        exit 1
    fi

    case "$dataset" in
        seed|demo|full) ;;
        *)
            print_error "Unknown dataset: ${dataset} (expected seed|demo|full)"
            exit 1
            ;;
    esac

    local backup_path="${BACKUPS_DIR}/${subfolder}"
    if [ ! -d "$backup_path" ]; then
        print_error "Backup subfolder not found: ${backup_path}"
        if [ -d "$BACKUPS_DIR" ] && [ -n "$(ls -A "$BACKUPS_DIR" 2>/dev/null)" ]; then
            print_error "Existing subfolders:"
            ls -1 "$BACKUPS_DIR" 2>/dev/null | sed 's/^/    /' || true
        fi
        exit 1
    fi

    local db_name
    db_name="$(database_name_from_env)"
    print_warning "This will DROP schema public on database '${db_name}', run alembic upgrade head, then load dataset=${dataset} from ${subfolder}."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        exit 0
    fi

    cd "$BACKEND_DIR"
    if uv run python scripts/data_management.py build_db "$subfolder" --dataset "$dataset" --yes; then
        print_success "Database built from: ${backup_path} (dataset=${dataset}, database=${db_name})"
    else
        print_error "build_db failed"
        exit 1
    fi
}

main() {
    local command="$1"
    shift || true

    case "$command" in
        dump)
            check_environment
            create_backup "$1"
            ;;
        upload|restore)
            check_environment
            restore_backup "$1"
            ;;
        upload_seed)
            check_environment
            partial_upload "upload_seed" "$1"
            ;;
        upload_demo)
            check_environment
            partial_upload "upload_demo" "$1"
            ;;
        build_db)
            check_environment
            build_database "$1" "$2"
            ;;
        list)
            list_one_backup "$1"
            ;;
        stats)
            check_environment
            show_stats
            ;;
        clean)
            check_environment
            clean_database
            ;;
        help|--help|-h)
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

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
