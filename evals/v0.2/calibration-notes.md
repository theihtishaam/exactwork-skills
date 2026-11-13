# Pre-study environment calibration

Two d04 calibration runs preceded the main balanced development schedule. Both are retained under runs/dev/d04/r01 and r02 but excluded from primary comparisons because the environment setup was being established.

- r01: requested workspace-write was downgraded to read-only by Codex 0.145.0 on Windows with no loaded Windows sandbox mode. No edit occurred; this is an infrastructure limitation, not evidence of skill quality.
- r02: an explicit supported restricted-token Windows sandbox mode enabled the requested fixture write. The task passed, but repeated multiline apply_patch.bat argument failures and an unnecessary Git query inflated operations.

Before main trial scheduling, all arms received the same environment facts: fixture has no Git metadata and the Windows apply_patch.bat shim is unreliable for multiline patches; another available local editing method should be used. No candidate-specific workaround was supplied. Calibration usage remains recorded and is not discarded or represented as a skill win.

The correction enables sandbox enforcement; it does not use a bypass flag, disable rules, inspect private settings, or modify persistent application configuration. Main runs use a fresh process, explicit fixture workspace, normal host-managed login, no network task work, and exported new-run telemetry.
