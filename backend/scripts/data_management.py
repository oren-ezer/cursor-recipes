#!/usr/bin/env python3
"""
Data management: database dump, restore (upload), list one backup, and statistics.

All backup data lives under: backend/scripts/backups/<backup_subfolder>/

Usage:
    python data_management.py dump [backup_subfolder]
    python data_management.py upload <backup_subfolder>
    python data_management.py upload_seed <backup_subfolder>
    python data_management.py upload_demo <backup_subfolder>
    python data_management.py list <backup_subfolder>
    python data_management.py stats
    python data_management.py clean [--yes] [--include-alembic]

Environment variables required:
    DATABASE_URL: PostgreSQL connection string
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import AbstractSet, Dict, List

# Add the backend directory to Python path so we can import src modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlmodel import create_engine, Session, text
from sqlalchemy import inspect, MetaData, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.schema import sort_tables
from src.core.config import settings
from src.core.security import hash_password

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Set up logging after _backups_root() is available."""
    log_dir = _backups_root()
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'data_management.log'),
        ],
    )

# Restored backups never rewrite Alembic revision rows (schema is managed by migrations).
_SKIP_UPLOAD_TABLES = frozenset({"alembic_version"})

# Subsets for partial uploads. Keep these in sync when adding new models.
_SEED_TABLES = ("users", "tags", "llm_configs")
_DEMO_TABLES = _SEED_TABLES + ("recipes", "recipe_tags")


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _reflect_metadata(engine) -> MetaData:
    meta = MetaData()
    meta.reflect(bind=engine)
    return meta


def _fk_insert_delete_orders(engine) -> tuple[List[str], List[str]]:
    """Return (insert_order, delete_order) using FK dependencies (parents before children on insert)."""
    meta = _reflect_metadata(engine)
    if not meta.tables:
        return [], []
    ordered = sort_tables(meta.tables.values())
    insert_order = [t.name for t in ordered]
    delete_order = list(reversed(insert_order))
    return insert_order, delete_order


def _get_table_object(metadata: MetaData, table_name: str):
    if f"public.{table_name}" in metadata.tables:
        return metadata.tables[f"public.{table_name}"]
    if table_name in metadata.tables:
        return metadata.tables[table_name]
    for fullname in metadata.tables:
        if fullname.split(".")[-1] == table_name:
            return metadata.tables[fullname]
    return None


def _is_bcrypt_hash(value: str) -> bool:
    return value.startswith(("$2b$", "$2a$", "$2y$")) and len(value) >= 59


def _hash_cleartext_passwords(table_name: str, row: dict) -> None:
    """If this is a users row with a plain-text password, hash it in-place."""
    if table_name != "users":
        return
    pwd = row.get("hashed_password")
    if pwd and not _is_bcrypt_hash(pwd):
        row["hashed_password"] = hash_password(pwd)
        logger.info("Hashed plain-text password for user %s", row.get("email", row.get("id")))


def _coerce_row_datetimes(row: dict) -> None:
    """In-place: parse ISO-like strings to datetime for upload."""
    for key, value in list(row.items()):
        if not isinstance(value, str):
            continue
        if "T" not in value or not any(x in value for x in (".", "+", "-", "Z")):
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            row[key] = parsed
        except ValueError:
            pass


def _sync_postgres_id_sequences(
    session: Session,
    insert_order: List[str],
    skip: AbstractSet[str],
) -> None:
    """Best-effort reset serial sequences to max(id)+1 for tables with an id column.

    Each attempt is wrapped in a SAVEPOINT so a failure on one table
    does not poison the transaction for subsequent tables.
    """
    logger.info("Updating id sequences where applicable (PostgreSQL)...")
    for table_name in insert_order:
        if table_name in skip:
            continue
        safe = _quote_ident(table_name)
        fq = f"public.{table_name.replace(chr(34), '')}"
        try:
            with session.begin_nested():
                session.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{fq}', 'id'), "
                        f"(SELECT COALESCE(MAX(id), 0) FROM {safe}) + 1, false)"
                    )
                )
        except Exception:
            try:
                with session.begin_nested():
                    session.execute(
                        text(
                            f"SELECT setval('{table_name}_id_seq', "
                            f"COALESCE((SELECT MAX(id) FROM {safe}), 0) + 1, false)"
                        )
                    )
            except Exception as e2:
                logger.warning(
                    "Could not update sequence for %s: %s",
                    table_name,
                    e2,
                )


_SCRIPTS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


def _backups_root() -> Path:
    return _SCRIPTS_DIR / "backups"


def _format_backups_root_missing(operation: str) -> str:
    root = _backups_root()
    return (
        f"Backups folder not found for '{operation}'.\n"
        f"  Expected backups root: {root}\n"
        f"Create it with: mkdir -p {root}\n"
        f"Or run 'dump' first to create a timestamped backup under {root}."
    )


def _format_backup_subfolder_missing(operation: str, backup_subfolder: str) -> str:
    root = _backups_root()
    target = root / backup_subfolder
    lines: List[str] = [
        f"Backup subfolder not found for '{operation}'.",
        f"  Backup name (subfolder): {backup_subfolder!r}",
        f"  Expected path:           {target}",
        f"  Resolved path:           {target.resolve()}",
        f"  Backups root:            {root}",
    ]
    if not root.is_dir():
        lines.append(f"  The backups root directory does not exist: {root}")
        lines.append(f"  Create it with: mkdir -p {root}")
    elif not target.exists():
        lines.append(f"  Path does not exist (not a file or directory): {target}")
        try:
            subdirs = sorted(p.name for p in root.iterdir() if p.is_dir())
            if subdirs:
                lines.append(
                    f"  Existing backup subfolders under {root}:\n    "
                    + "\n    ".join(subdirs)
                )
            else:
                lines.append(f"  No subfolders found under {root} (directory exists but is empty).")
        except OSError as e:
            lines.append(f"  Could not list {root}: {e}")
    elif target.is_file():
        lines.append(f"  Expected a directory but found a file: {target}")
    else:
        lines.append(f"  Path exists but is not a directory: {target}")
    return "\n".join(lines)


class DataManagement:
    """
    Handle database dump, restore (upload), clean, and statistics.
    """

    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided")

        self.engine = create_engine(self.database_url)

        logger.info(f"Initialized with database: {self.database_url.split('@')[1] if '@' in self.database_url else 'local'}")

    def verify_backup_tables_exist(self, backup_info: dict) -> bool:
        """Ensure every table listed in backup_info exists in the target database."""
        try:
            inspector = inspect(self.engine)
            existing = set(inspector.get_table_names())
            tables_meta = backup_info.get("tables") or {}
            missing = [name for name in tables_meta if name not in existing]
            if missing:
                logger.error(
                    "Backup references tables not present in the database: %s. "
                    "Run migrations (alembic upgrade head) or use a backup from a compatible schema.",
                    missing,
                )
                return False
            logger.info("Backup / database table names are consistent")
            return True
        except Exception as e:
            logger.error(f"Structure verification failed: {str(e)}")
            return False

    def dump_data(self, output_dir: str) -> bool:
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Starting full database dump to {output_path}")

            inspector = inspect(self.engine)
            table_names = sorted(inspector.get_table_names())

            backup_info = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database_url": self.database_url.split("@")[1] if "@" in self.database_url else "local",
                "format": 2,
                "tables": {},
            }

            with Session(self.engine) as session:
                for table_name in table_names:
                    logger.info(f"Dumping table: {table_name}")
                    safe = _quote_ident(table_name)
                    result = session.execute(text(f"SELECT * FROM {safe}"))
                    records = [dict(row._mapping) for row in result]

                    table_file = output_path / f"{table_name}.json"
                    with open(table_file, "w", encoding="utf-8") as f:
                        json.dump(records, f, indent=2, default=str)

                    backup_info["tables"][table_name] = {
                        "count": len(records),
                        "file": f"{table_name}.json",
                    }
                    logger.info(f"Dumped {len(records)} records from {table_name}")

            metadata_file = output_path / "backup_info.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(backup_info, f, indent=2)

            logger.info(f"Data dump completed successfully. Backup info saved to {metadata_file}")
            return True

        except Exception as e:
            logger.error(f"Data dump failed: {str(e)}")
            return False

    def upload_data(
        self,
        input_dir: str,
        verify_structure: bool = True,
        only_tables: tuple[str, ...] | None = None,
    ) -> bool:
        """Restore data from a backup directory.

        Args:
            input_dir: Path to the backup subfolder.
            verify_structure: Check that backup tables exist in the DB.
            only_tables: If given, restrict the upload to this subset of tables.
        """
        try:
            input_path = Path(input_dir).resolve()
            if not input_path.exists():
                logger.error(
                    f"Upload input path does not exist.\n"
                    f"  Path: {input_path}\n"
                    f"  Backups root: {_backups_root()}"
                )
                return False

            if not input_path.is_dir():
                logger.error(
                    f"Upload input path is not a directory.\n"
                    f"  Path: {input_path}\n"
                    f"  Is file: {input_path.is_file()}"
                )
                return False

            metadata_file = input_path / "backup_info.json"
            if not metadata_file.exists():
                logger.error(
                    f"Backup metadata file missing (required for upload).\n"
                    f"  Expected file: {metadata_file}\n"
                    f"  Backup directory: {input_path}\n"
                    f"  Contents: {sorted(p.name for p in input_path.iterdir()) if input_path.is_dir() else 'n/a'}"
                )
                return False

            with open(metadata_file, "r", encoding="utf-8") as f:
                backup_info = json.load(f)

            if verify_structure and not self.verify_backup_tables_exist(backup_info):
                logger.error("Database structure verification failed. Aborting upload.")
                return False

            tables_meta = backup_info.get("tables") or {}
            tables_in_backup = set(tables_meta.keys())

            if only_tables is not None:
                requested = set(only_tables)
                missing_in_backup = requested - tables_in_backup
                if missing_in_backup:
                    logger.warning(
                        "Requested tables not found in backup (skipped): %s",
                        sorted(missing_in_backup),
                    )
                tables_in_backup = tables_in_backup & requested
                logger.info("Partial upload — tables: %s", sorted(tables_in_backup))

            logger.info(
                f"Starting data upload from backup created: {backup_info.get('timestamp', 'unknown')}"
            )

            is_partial = only_tables is not None
            insert_order, delete_order = _fk_insert_delete_orders(self.engine)
            reflected = _reflect_metadata(self.engine)

            with Session(self.engine) as session:
                if is_partial:
                    logger.info(
                        "Partial upload — using upsert (existing rows updated, "
                        "FKs stay intact, extra DB rows kept)."
                    )
                else:
                    logger.info("Clearing existing data (FK-safe order; alembic_version not modified)...")
                    for table_name in delete_order:
                        if table_name in _SKIP_UPLOAD_TABLES:
                            continue
                        if table_name not in tables_in_backup:
                            continue
                        safe = _quote_ident(table_name)
                        r = session.execute(text(f"SELECT COUNT(*) FROM {safe}")).first()
                        n = int(r[0]) if r else 0
                        if n:
                            session.execute(text(f"DELETE FROM {safe}"))
                            logger.info(f"Cleared {n} records from {table_name}")

                    session.commit()

                for table_name in insert_order:
                    if table_name in _SKIP_UPLOAD_TABLES:
                        logger.info(
                            f"Skipping data upload for {table_name} (leave revision to Alembic)"
                        )
                        continue
                    if table_name not in tables_in_backup:
                        continue

                    table_file = input_path / f"{table_name}.json"
                    if not table_file.exists():
                        logger.warning(f"Table file not found: {table_file}, skipping...")
                        continue

                    table_obj = _get_table_object(reflected, table_name)
                    if table_obj is None:
                        logger.error(
                            f"Table {table_name!r} not found in reflected schema; skipping insert"
                        )
                        continue

                    logger.info(f"Uploading data to table: {table_name}")

                    with open(table_file, "r", encoding="utf-8") as f:
                        records = json.load(f)

                    if not records:
                        logger.info(f"No records to upload for {table_name}")
                        continue

                    pk_cols = [c.name for c in table_obj.primary_key.columns]

                    uploaded_count = 0
                    for record_data in records:
                        try:
                            row = dict(record_data)
                            allowed = {c.name for c in table_obj.columns}
                            row = {k: v for k, v in row.items() if k in allowed}
                            _coerce_row_datetimes(row)
                            _hash_cleartext_passwords(table_name, row)

                            if is_partial and pk_cols:
                                stmt = pg_insert(table_obj).values(**row)
                                update_cols = {
                                    k: v for k, v in row.items() if k not in pk_cols
                                }
                                stmt = stmt.on_conflict_do_update(
                                    index_elements=pk_cols,
                                    set_=update_cols,
                                )
                                session.execute(stmt)
                            else:
                                session.execute(insert(table_obj).values(**row))

                            uploaded_count += 1
                        except Exception as e:
                            logger.error(
                                "Failed to upload record to %s: %s — %s",
                                table_name,
                                record_data.get("id", record_data),
                                e,
                            )
                            continue

                    session.commit()
                    logger.info(f"Uploaded {uploaded_count} records to {table_name}")

                seq_skip = frozenset(
                    _SKIP_UPLOAD_TABLES
                    | {t for t in insert_order if t not in tables_in_backup}
                )
                _sync_postgres_id_sequences(session, insert_order, seq_skip)

                session.commit()

                logger.info("Data upload completed successfully")
                return True

        except Exception as e:
            logger.error(f"Data upload failed: {str(e)}")
            return False

    def clean_all_data(self, *, include_alembic: bool = False) -> bool:
        """
        Delete all rows from every reflected table in FK-safe order.

        By default ``alembic_version`` is left untouched so migration history stays valid.
        """
        try:
            insert_order, delete_order = _fk_insert_delete_orders(self.engine)
            skip = frozenset() if include_alembic else _SKIP_UPLOAD_TABLES

            with Session(self.engine) as session:
                logger.info(
                    "Deleting all rows in dependency order%s.",
                    " (including alembic_version)" if include_alembic else " (alembic_version preserved)",
                )
                for table_name in delete_order:
                    if table_name in skip:
                        logger.info("Skipping table %s", table_name)
                        continue
                    safe = _quote_ident(table_name)
                    r = session.execute(text(f"SELECT COUNT(*) FROM {safe}")).first()
                    n = int(r[0]) if r else 0
                    if n:
                        session.execute(text(f"DELETE FROM {safe}"))
                        logger.info("Cleared %s records from %s", n, table_name)

                session.commit()

                seq_skip: AbstractSet[str] = skip
                _sync_postgres_id_sequences(session, insert_order, seq_skip)

                session.commit()

            logger.info("Database clean completed successfully")
            return True

        except Exception as e:
            logger.error("Database clean failed: %s", e)
            return False

    def get_database_stats(self) -> Dict[str, int]:
        """Row counts for every table in the connected database (via inspector)."""
        stats: Dict[str, int] = {}
        try:
            inspector = inspect(self.engine)
            table_names = sorted(inspector.get_table_names())
            with Session(self.engine) as session:
                for table_name in table_names:
                    safe_ident = table_name.replace('"', '""')
                    try:
                        result = session.exec(
                            text(f'SELECT COUNT(*) AS n FROM "{safe_ident}"')
                        ).first()
                        val = result[0] if result is not None else 0
                        stats[table_name] = int(val)
                    except Exception as e:
                        logger.warning(
                            "Could not count rows for table %s: %s",
                            table_name,
                            e,
                        )
                        stats[table_name] = -1
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")

        return stats


def _run_list(backup_subfolder: str) -> int:
    root = _backups_root()
    target = root / backup_subfolder

    if not root.is_dir():
        print(_format_backups_root_missing("list"))
        return 1

    if not target.is_dir():
        print(_format_backup_subfolder_missing("list", backup_subfolder))
        return 1

    meta = target / "backup_info.json"
    print(f"Backup: {backup_subfolder}")
    print(f"Path:   {target.resolve()}")
    print(f"Root:   {root.resolve()}")
    if meta.is_file():
        with open(meta, encoding="utf-8") as f:
            info = json.load(f)
        print(f"Metadata (backup_info.json):\n{json.dumps(info, indent=2)}")
    else:
        print("No backup_info.json in this folder.")
    files = sorted(p.name for p in target.iterdir() if p.is_file())
    print(f"Files ({len(files)}): {', '.join(files)}")
    return 0


def main() -> int:
    _configure_logging()

    parser = argparse.ArgumentParser(
        description="Data management: all data under <running_dir>/backups/<subfolder>/"
    )
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    dump_parser = subparsers.add_parser("dump", help="Write JSON backup under backups/<subfolder>/")
    dump_parser.add_argument(
        "backup_subfolder",
        nargs="?",
        default=None,
        help="Subfolder name under backups/ (default: backup_YYYYMMDD_HHMMSS)",
    )
    dump_parser.add_argument("--database-url", help="Database URL (defaults to env DATABASE_URL)")

    upload_parser = subparsers.add_parser("upload", help="Restore from backups/<subfolder>/")
    upload_parser.add_argument(
        "backup_subfolder",
        help="Subfolder name under backups/ (the backup to restore)",
    )
    upload_parser.add_argument("--database-url", help="Database URL (defaults to env DATABASE_URL)")
    upload_parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip database structure verification",
    )

    list_parser = subparsers.add_parser("list", help="Show metadata and files for backups/<subfolder>/")
    list_parser.add_argument(
        "backup_subfolder",
        help="Subfolder name under backups/",
    )

    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("--database-url", help="Database URL (defaults to env DATABASE_URL)")

    clean_parser = subparsers.add_parser(
        "clean",
        help="Delete all rows from all tables (FK-safe); preserves alembic_version by default",
    )
    clean_parser.add_argument("--database-url", help="Database URL (defaults to env DATABASE_URL)")
    clean_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip interactive confirmation",
    )
    clean_parser.add_argument(
        "--include-alembic",
        action="store_true",
        help="Also delete alembic_version (breaks migration stamp until you fix it)",
    )

    upload_seed_parser = subparsers.add_parser(
        "upload_seed",
        help=f"Upload only seed tables ({', '.join(_SEED_TABLES)}) from a backup",
    )
    upload_seed_parser.add_argument(
        "backup_subfolder",
        help="Subfolder name under backups/",
    )
    upload_seed_parser.add_argument("--database-url", help="Database URL (defaults to env DATABASE_URL)")

    upload_demo_parser = subparsers.add_parser(
        "upload_demo",
        help=f"Upload seed + demo tables ({', '.join(_DEMO_TABLES)}) from a backup",
    )
    upload_demo_parser.add_argument(
        "backup_subfolder",
        help="Subfolder name under backups/",
    )
    upload_demo_parser.add_argument("--database-url", help="Database URL (defaults to env DATABASE_URL)")

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return 1

    try:
        if args.mode == "list":
            return _run_list(args.backup_subfolder)

        if args.mode in ("upload", "upload_seed", "upload_demo"):
            root = _backups_root()
            if not root.is_dir():
                print(_format_backups_root_missing(args.mode))
                return 1
            name = args.backup_subfolder
            target = root / name
            if not target.is_dir():
                print(_format_backup_subfolder_missing(args.mode, name))
                return 1
            manager = DataManagement(database_url=getattr(args, "database_url", None))
            logger.info(f"Upload source: {target.resolve()}")
            verify = not getattr(args, "skip_verification", False)
            only: tuple[str, ...] | None = None
            if args.mode == "upload_seed":
                only = _SEED_TABLES
            elif args.mode == "upload_demo":
                only = _DEMO_TABLES
            success = manager.upload_data(
                str(target), verify_structure=verify, only_tables=only,
            )
            if success:
                stats = manager.get_database_stats()
                logger.info(f"Final database stats: {stats}")
            return 0 if success else 1

        manager = DataManagement(database_url=getattr(args, "database_url", None))

        if args.mode == "dump":
            root = _backups_root()
            root.mkdir(parents=True, exist_ok=True)
            name = args.backup_subfolder or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir = str(root / name)
            logger.info(f"Dump target: {output_dir}")
            success = manager.dump_data(output_dir)
            return 0 if success else 1

        if args.mode == "stats":
            stats = manager.get_database_stats()
            if not stats:
                print("\nNo tables found (or could not inspect the database).")
                return 1
            width = max(len(name) for name in stats)
            width = max(width, len("Table"))
            print("\nDatabase statistics (row counts per table)")
            print("-" * (width + 14))
            print(f"{'Table':<{width}}  {'Rows':>10}")
            print("-" * (width + 14))
            for table, count in stats.items():
                row_display = f"{count:>10}" if count >= 0 else f"{'n/a':>10}"
                print(f"{table:<{width}}  {row_display}")
            print("-" * (width + 14))
            total = sum(c for c in stats.values() if c >= 0)
            skipped = sum(1 for c in stats.values() if c < 0)
            print(f"{'Total rows':<{width}}  {total:>10}")
            if skipped:
                print(f"({skipped} table(s) could not be counted; see log.)")
            return 0

        if args.mode == "clean":
            if not args.yes:
                try:
                    reply = input(
                        "This deletes all rows in every table (alembic_version is kept unless "
                        "--include-alembic). Type 'yes' to continue: "
                    )
                except EOFError:
                    print("Cancelled (no input).")
                    return 1
                if reply.strip().lower() != "yes":
                    print("Cancelled.")
                    return 0
            success = manager.clean_all_data(include_alembic=args.include_alembic)
            if success:
                stats = manager.get_database_stats()
                logger.info("Row counts after clean: %s", stats)
            return 0 if success else 1

    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
