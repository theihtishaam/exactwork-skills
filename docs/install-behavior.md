# Installation behavior

The installer copies selected skill directories from this repository into the client-specific root of an explicitly supplied, existing project. It does not read configuration, credentials, browser data, or network resources.

- Preview is the default. Only `--apply` writes files.
- The entire selected set is checked before copying begins. A differing existing bundle blocks the installation; an exactly identical bundle is a no-op.
- Source/destination symbolic links, Windows junctions/reparse points, path escapes, and unsafe skill names are rejected. This conservative policy may reject a legitimate linked project; choose a real directory instead.
- It never overwrites or deletes a file. It does not install hooks, edit `AGENTS.md`, change permissions, or enable disabled client features.
- No update or uninstall automation is provided. For an update, inspect differences and manually preserve/move your old skill before installing. To remove a copy, remove only the exact skill directory shown by the installer, after checking it contains no edits you need.
- Preflight is not a filesystem transaction. Disk failure or interruption may leave some newly created files. Stop, inspect the printed destinations, and reconcile the partial installation manually. Do not run simultaneous installs or modify target paths concurrently.

Exit status: `0` means preview/success/no-op; `2` means refused input or conflict; `1` means an I/O failure. Read the output before assuming an installation completed. Native discovery still needs a fresh/reloaded client session and verification in that client.

Each bundle includes its MIT license. Skill instructions themselves require no Python and make no network calls. The agent using them can still use its own authorized tools; the skills are not a sandbox.
