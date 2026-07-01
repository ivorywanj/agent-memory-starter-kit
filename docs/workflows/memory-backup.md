# /memory backup

Use this workflow when the user wants to move or preserve a memory library.

## User Experience

Create a zip backup and report the file path.

Do not ask advanced storage questions in v1.

## Agent Command

```bash
scripts/memory backup
```

Optional explicit output:

```bash
scripts/memory backup --output ./agent-memory-backup.zip
```

## Pass Criteria

- Backup is a zip file.
- Backup excludes `.env*`, secrets, temporary dialogue data, search indexes, raw runs, generated drafts, and local database files.
- Backup runs the memory guard before writing the zip.
