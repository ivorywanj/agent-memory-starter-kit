# memory backup

Use this workflow when the user wants to preserve a memory library or move it to another computer.

## User Experience

Create a zip backup and report the file path.

Do not ask advanced storage questions in v1.
Do not ask which memory library to back up when the current installed memory library is known. If a question is needed, ask where to save the zip backup. You can also say "use the default backup folder".

Start with:

```text
I will create a zip backup of your memory library.

Where should I save the zip backup? You can also say "use the default backup folder".
```

Backup does not connect, import, restore, switch, or initialize a memory library.

## Agent Command

```bash
memory backup
```

Optional explicit output:

```bash
memory backup --output ./journeymem-backup.zip
```

## Pass Criteria

- Backup is a zip file.
- Backup does not connect, import, switch, or initialize memory libraries.
- Response asks where to save the zip backup and may offer the default backup folder.
- Response does not mix backup with connect, import, restore, switch, or initialization.
- Backup excludes `.env*`, secrets, temporary dialogue data, search indexes, raw runs, generated drafts, and local database files.
- Backup runs the memory guard before writing the zip.
