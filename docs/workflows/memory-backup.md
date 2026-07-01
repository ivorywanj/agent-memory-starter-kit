# memory backup

Use this workflow when the user wants to preserve a memory library or move it to another computer.

## User Experience

Create a zip backup and report the file path.

Do not ask advanced storage questions in v1.

## Agent Command

```bash
memory backup
```

Optional explicit output:

```bash
memory backup --output ./agent-memory-backup.zip
```

## Pass Criteria

- Backup is a zip file.
- Backup does not connect, import, switch, or initialize memory libraries.
- Backup excludes `.env*`, secrets, temporary dialogue data, search indexes, raw runs, generated drafts, and local database files.
- Backup runs the memory guard before writing the zip.
