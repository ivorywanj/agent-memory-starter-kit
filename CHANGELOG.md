# Changelog

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
