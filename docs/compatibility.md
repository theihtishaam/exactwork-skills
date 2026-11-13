# Compatibility and installation

Checked **2026-11-12**. Exactwork uses the open Agent Skills format: a directory containing `SKILL.md`, with standard `name` and `description` frontmatter and relative links to supporting files. Its instructions require no hooks, background service, API key, or specific model. This is a portable format, not a guarantee that every agent will load or follow it identically. [Agent Skills specification](https://agentskills.io/specification)

## Choose one installation target

Run these commands from the downloaded repository. Python 3.10+ is needed for the installer and the optional context/learning helpers, not for reading the instructions.

```sh
# Preview the core skill's destination. No files are changed.
python tools/install.py --project "./my-project" --client codex --skill exactwork

# Apply the reviewed installation.
python tools/install.py --project "./my-project" --client codex --skill exactwork --apply

# Optionally install all six skills for that client.
python tools/install.py --project "./my-project" --client codex --all --apply
```

Use `python3` instead of `python` if that is your Python command. Substitute your actual project directory and a client below. `--all` means all six Exactwork skills, **not** every client or every project. The default skill is `exactwork`; companions can be installed separately. The installer refuses to overwrite differing existing files.

For manual installation, copy an entire directory such as `skills/exactwork/` into the selected root. The result must be `<root>/exactwork/SKILL.md`; do not add another `skills/` grouping level. The installer targets projects only. Personal roots below are documented manual alternatives, not locations it silently modifies.

## Client matrix

**Documented** means first-party documentation describes the format and path. **Source inspected** additionally means relevant implementation was read. Neither proves native skill discovery or a successful end-to-end run in that client. The 0.2 behavioral study used explicit instruction injection through Codex CLI 0.145.0, not native discovery.

| Installer target | Project root | Documented personal root | Explicit invocation | Evidence |
|---|---|---|---|---|
| `codex` | `.agents/skills/` | `~/.agents/skills/` | `$exactwork` | [Documented](https://learn.chatgpt.com/docs/build-skills) |
| `claude` | `.claude/skills/` | `~/.claude/skills/` | `/exactwork` | [Documented](https://code.claude.com/docs/en/skills) |
| `opencode` | `.opencode/skills/` | `~/.config/opencode/skills/` | `@exactwork` in current V2 docs | [Documented](https://opencode.ai/docs/skills/) |
| `harness` | `.dsh/skills/` | `~/.dsh/skills/` | `/exactwork` | [Documented and source inspected](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md), installed package 0.2.2-rc.1 |
| `gemini` | `.gemini/skills/` | `~/.gemini/skills/` | Ask to use `exactwork`; check `/skills list` | [Documented](https://geminicli.com/docs/cli/using-agent-skills/) |
| `copilot` | `.github/skills/` | `~/.copilot/skills/` | Select `/exactwork` when listed | [Documented for Copilot in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills) |
| `cursor` | `.cursor/skills/` | `~/.cursor/skills/` | Select `/exactwork` | [Documented](https://cursor.com/docs/skills) |
| `cline` | `.cline/skills/` | `~/.cline/skills/` | Select `/exactwork` | [Documented](https://docs.cline.bot/customization/skills) |
| `shared` | `.agents/skills/` | `~/.agents/skills/` | Depends on client | Documented for Codex, OpenCode, Harness, Gemini, and Cursor |

`~` means your home directory. Custom configurations, disabled skill features, trust settings, and older client versions can change availability. DeepSeek **models** running through another agent use that agent's discovery behavior; “Harness” here means the DeepSeek Harness application.

## Shared roots and duplicate skills

There is no verified single directory recognized by all these clients. `.agents/skills` is useful for the five clients listed above; Claude Code, Cline, and the current Copilot harness have different documented destinations.

Choose one active definition per client and scope. Installing identical bundles into several roots can create overlapping discovery. OpenCode resolves duplicate IDs by precedence; Codex can list duplicate names; Cline gives global definitions precedence over project definitions. Some clients support manually linked source directories, but the Exactwork installer deliberately rejects symlinks and reparse points. Neither manual linking nor copying proves that every host deduplicates multiple discovery paths. Follow the linked client documentation before combining installations.

Harness discovers direct bundles, not arbitrary nested skill groups. Its registry, filesystem provider, and skill tool must be enabled. Its default catalog description limit is 500 characters; Exactwork uses shorter descriptions. [Harness skill tool](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.md)

## Verify in your client

Start a fresh session in the intended project. Confirm the skill appears, invoke it explicitly on a small task, and check the tool activity and actual result. Test automatic selection separately using a natural request that fits its description. Discovery alone does not prove successful selection or execution.

Local installation does not automatically deploy into hosted sessions. Claude cloud sessions and Cursor Cloud Agents have separate distribution rules; Cursor does not copy personal `.agents/skills` into remote sessions. Check the relevant client documentation above.

For an unsupported text-capable agent, manually provide the chosen `SKILL.md` and ask it to follow those instructions for the current task. Supply any referenced files it needs. This is **manual instruction mode**, not native skill support, and it adds the provided text to context.

For validation evidence and remaining limits, see the repository's evaluation documentation. Do not interpret this table as certification of every host/model/version combination.
