# Changelog

## v0.1.4

- Added user-facing `/memory new`, `/memory connect`, and `/memory backup` shortcuts.
- Added productized user-flow documentation with measurable T21-T26 acceptance criteria.
- Added public fixture tests for quick entry, cross-Agent connection, and zip backup exclusions.
- Strengthened first-screen terminology checks for external-user onboarding.

## v0.1.3

- Added `memory share` for pointer-only bridge files across Codex, Claude Code, Cursor, and generic Agents.
- Added public Agent sharing docs and `/memory-share` workflow.
- Added tests proving bridges point to one shared runtime without copying user memory into Agent workspaces.

## v0.1.2

- Added Agent-led first-run wizard documentation.
- Made real-user onboarding ask one question at a time instead of using the demo answers fixture.
- Added project workspace pointers for initialization.
- Strengthened public release checks for first-run wizard and workspace pointer documentation.

## v0.1.1

- Reworked README as a product homepage for external users.
- Added checked-in release notes for GitHub Release publishing.
- Strengthened public release checks for README sections and release notes.
- Kept the runtime interface unchanged from v0.1.0.

## v0.1.0

- Initial public starter kit.
- CLI initializer for Markdown memory runtimes.
- `remember -> recall -> improve -> forget` local memory loop.
- Public fixture tests, memory guard, and release scan.
- GitHub Actions CI for public package validation.
