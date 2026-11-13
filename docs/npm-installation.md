# Install from npm

Package: `@theihtisham/exactwork-skills`. The npm account is `theihtisham`; the GitHub owner is `theihtishaam`.

```sh
# Install all six skills for detected supported tools, at user scope.
npx @theihtisham/exactwork-skills install --detected

# Preview without writing files.
npx @theihtisham/exactwork-skills install --detected --dry-run

# Explicit agents, in an existing project.
npx @theihtisham/exactwork-skills install --agent codex --agent claude --project ./my-project

# Install to every listed target, whether detected or not.
npx @theihtisham/exactwork-skills install --all-agents

# Check installed files against the package.
npx @theihtisham/exactwork-skills verify --detected
```

Node.js 20+ is required. Python 3.10+ is needed only for the optional context and learning helpers. No Python is required to copy or read the skills. For a persistent command, use `npm install -g @theihtisham/exactwork-skills`, then `exactwork-skills install --detected`. Installing the npm package alone does not write into agent directories: the explicit `install` command does that.

The package includes all six skill folders. Installation uses bundled files, with no GitHub clone, runtime dependency packages, hooks or installer telemetry. npm itself uses its normal registry and package cache and records registry downloads. Those counts are downloads, not unique users or verified installations.

Supported agent names: `codex`, `claude`, `opencode`, `harness`, `gemini`, `copilot`, `cursor`, `cline`, and `shared`. Select agents with repeated `--agent` options or comma-separated names. `--skill` selects individual skills; all six are the default. Unknown targets and arguments are refused.

Detection checks the presence of known application directories and executable names on PATH. It reads no configuration contents or credentials and executes no detected program. This is a heuristic: stale folders can count as detected, and custom profiles or portable installations can be missed. Use an explicit agent when necessary. `shared` is an explicit destination, not a detected application.

User and project paths follow the [compatibility matrix](compatibility.md). Custom profile roots and environment-specific overrides are not automatically resolved. `--all-agents` means the listed supported targets, not every AI application or hosted service. Multiple skill roots can cause duplicate discovery in some clients; choose explicit targets for the clients you use.

Before writing, every selected destination is checked. Differing existing files or extra files block the complete selection. Identical files are unchanged. Source and destination symlinks/junctions are rejected. Files are created exclusively. No configuration or permissions are changed. Do not modify destination paths or run simultaneous installs during installation: this is not a filesystem transaction, and an I/O failure can leave partial new files. Review partial output before retrying.

Updates also preserve differing existing files. Preview the new package and compare it with your current copy before manually relocating any conflicting folders. This version deliberately has no automatic update-overwrite or uninstall command.

After installation, reload the agent and confirm that a skill appears and can be invoked. `verify` checks installed bytes only; it does not establish native activation or model behavior. Cloud and remote agents may need installation in their own environment. No universal activation or quality guarantee is implied.

## Package preparation

`node tools/build-npm.mjs /absolute/staging/directory` creates a clean npm staging folder and rewrites README asset/document links to the public GitHub sources. Run `npm pack` in that folder and publish the reviewed tarball with `npm publish /path/to/package.tgz --access public`. The package allowlist excludes evaluation transcripts, images and unrelated workspace files. Run `npm test` from the repository before packaging.
