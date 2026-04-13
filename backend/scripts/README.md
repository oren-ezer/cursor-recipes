# Data management scripts

JSON snapshots live under **`backend/scripts/backups/<subfolder>/`** (always the same location regardless of where you invoke the commands from).

## Files

- `data_management.py` — CLI: `dump`, `upload`, `list`, `stats`, `clean`
- `data_management.sh` — Shell wrapper
- `README.md` — This file

## Layout

```
backend/scripts/
  backups/
    data_management.log              # log file
    backup_20260228_214601/          # or any subfolder name you choose on dump
      <one JSON file per DB table, e.g. users.json, recipes.json, ...>
      backup_info.json               # format 2: lists every dumped table and counts
```

## Commands

| Command | Subfolder | Behavior |
|--------|-----------|----------|
| `dump` | Optional | Writes to `backups/<subfolder>/`. If omitted, subfolder name defaults to `backup_YYYYMMDD_HHMMSS`. |
| `upload` | **Required** | Restores from `backups/<subfolder>/`. |
| `list` | **Required** | Prints `backup_info.json` (if present) and file list for `backups/<subfolder>/`. |
| `stats` | — | Row counts for every table the DB exposes (same discovery as `dump`). |
| `clean` | — | Deletes all rows in FK-safe order; leaves `alembic_version` unchanged (use `clean --include-alembic` in Python only if you really need that). |

## Shell (recommended)

```bash
./scripts/data_management.sh dump
./scripts/data_management.sh dump my_snapshot
./scripts/data_management.sh list backup_20260228_214601
./scripts/data_management.sh upload backup_20260228_214601
./scripts/data_management.sh stats
./scripts/data_management.sh clean
./scripts/data_management.sh help
```

## Python (same rules)

```bash
cd backend

uv run python scripts/data_management.py dump
uv run python scripts/data_management.py dump my_snapshot

uv run python scripts/data_management.py list backup_20260228_214601
uv run python scripts/data_management.py upload backup_20260228_214601
uv run python scripts/data_management.py upload my_snapshot --skip-verification

uv run python scripts/data_management.py stats

uv run python scripts/data_management.py clean
uv run python scripts/data_management.py clean -y
uv run python scripts/data_management.py clean -y --include-alembic

# Optional DB URL override
uv run python scripts/data_management.py dump my_export --database-url "postgresql://..."
```

## How it works

### Dump

1. Creates `backups/<subfolder>/`, introspects the database for table names, and writes one `<table>.json` per table plus `backup_info.json` (`format: 2`). New migrations/tables are included automatically on the next dump.

### Upload

1. Requires `backups/<subfolder>/` to exist and contain `backup_info.json`.
2. Verifies schema (unless `--skip-verification`).
3. Clears tables that appear in the backup (FK-safe order; `alembic_version` is never deleted) and inserts rows in dependency order; attempts PostgreSQL sequence fixes for `id` columns.

### List

1. Requires `backups/<subfolder>/` to exist.
2. Prints path, metadata, and file names (helpful before `upload`).

### Clean

1. Introspects tables and runs `DELETE` in reverse FK order (same ordering idea as `upload`).
2. Skips `alembic_version` by default so migration history stays valid.
3. Best-effort PostgreSQL `id` sequence reset after deletes.

## Safety

- **Upload** overwrites application data; the shell asks for confirmation.
- **Clean** wipes all application rows; the shell asks for confirmation (`clean --yes` / `-y` skips the Python prompt when you already confirmed in the shell).
- **Logs**: `data_management.log` under `backend/scripts/backups/`.

## Troubleshooting

- **`upload` / `list` errors**: Messages include expected path, backups root, and existing subfolder names when relevant.
- **Permissions**: `chmod +x scripts/data_management.sh`

## Performance

For very large databases, prefer PostgreSQL `pg_dump` / `pg_restore`.
