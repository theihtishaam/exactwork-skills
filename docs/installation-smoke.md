# Direct installation check

On 2026-11-13, Skills CLI 1.8.1 ran on Windows with Node.js 24.15.0 against the public repository at commit `87f9d3fbb0f6e921dbedd7db728dadc8a9bb2fc4`. The target was a new isolated project directory, not an existing user project. Telemetry was disabled for the check.

Discovery returned exactly the six published skills:

```sh
npx --yes skills add theihtishaam/exactwork-skills --list
```

All six were installed into the project's `.agents/skills/` directory for Codex:

```sh
npx --yes skills add theihtishaam/exactwork-skills --skill exactwork exactwork-context exactwork-learn exactwork-research exactwork-review exactwork-handoff -a codex -y
```

Both commands exited successfully. The CLI reported that all six folders were copied. The installed skill files were then compared with the published source. The bundled context and learning helper entrypoints were also checked with `--help`.

This checks repository discovery, installation and file delivery. It does not establish that a host activated a skill, that the model followed it, or that other agent clients installed successfully. Those remain separate checks. The behavioral study in this repository used explicit instruction injection through Codex CLI.

The [Skills CLI documentation](https://github.com/vercel-labs/skills#install-a-skill) currently specifies Node.js 22.20 or newer. The repository's Python installer remains an alternative and supports a preview before applying changes. Python 3.10+ is required for the optional Python helpers even when installation uses the Skills CLI.
