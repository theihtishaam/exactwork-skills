#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {AGENTS, SKILLS, detectAgents, planInstall, applyPlan} from '../lib/install.mjs';
const bundle = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const version = JSON.parse(fs.readFileSync(path.join(bundle, 'package.json'), 'utf8')).version;
const help = `Exactwork ${version} — six portable agent skills

  exactwork-skills install --detected
  exactwork-skills install --agent codex --agent claude --dry-run
  exactwork-skills install --all-agents --project ./my-project
  exactwork-skills verify --agent harness
  exactwork-skills list

install copies all six skills by default. Global/user scope is the default.
--project PATH    Install into an existing project instead
--global          Explicitly choose user scope (cannot combine with --project)
--detected        Detect supported tools by directories and PATH (default)
--agent NAME      Explicit target; repeat or comma-separate
--all-agents      Every listed target, even when not detected
--skill NAME      Select a skill; repeat or comma-separate (default: all six)
--dry-run         Preview without writes
--version         Print package version

Agents: ${Object.keys(AGENTS).join(', ')}
Existing differing files are never overwritten. No hooks, telemetry or config
edits. Detection is a hint, not proof of native activation. Reload your agent
and verify that the skill is discovered. Optional helpers require Python 3.10+.
`;
try {
  const args = process.argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) { console.log(help); }
  else if (args.length === 1 && args[0] === '--version') console.log(version);
  else {
    const command = args.shift();
    if (!['install', 'verify', 'list'].includes(command)) throw Error(`Unknown command: ${command}`);
    const opts = {agents: [], skills: [], project: undefined, global: false, all: false, detected: false, dry: false};
    while (args.length) {
      const flag = args.shift();
      if (['--agent', '--skill', '--project'].includes(flag)) {
        const value = args.shift(); if (!value || value.startsWith('--')) throw Error(`Missing value for ${flag}`);
        if (flag === '--project') opts.project = path.resolve(value);
        else opts[flag === '--agent' ? 'agents' : 'skills'].push(...value.split(',').filter(Boolean));
      } else if (flag === '--all-agents') opts.all = true;
      else if (flag === '--detected') opts.detected = true;
      else if (flag === '--dry-run') opts.dry = true;
      else if (flag === '--global') opts.global = true;
      else throw Error(`Unknown option: ${flag}`);
    }
    if (opts.global && opts.project) throw Error('Choose --global or --project, not both.');
    if (Number(opts.all) + Number(opts.detected) + Number(opts.agents.length > 0) > 1) throw Error('Choose one agent selection mode.');
    if (command === 'list') { console.log(`Skills: ${SKILLS.join(', ')}\nAgents: ${Object.keys(AGENTS).join(', ')}`); }
    else {
      const agents = opts.all ? Object.keys(AGENTS) : opts.agents.length ? opts.agents : detectAgents({project: opts.project});
      const plans = planInstall({bundle, project: opts.project, agents, skills: opts.skills.length ? opts.skills : SKILLS});
      if (command === 'verify' && plans.some(p => !p.unchanged)) throw Error('Some selected skills are missing; run install first.');
      if (command === 'install' && !opts.dry) applyPlan(plans);
      for (const p of plans) console.log(`${command === 'verify' ? 'VERIFIED' : p.unchanged ? 'UNCHANGED' : opts.dry ? 'WOULD INSTALL' : 'INSTALLED'}: ${p.dest}`);
      console.log(command === 'verify' ? 'File copies match this package. Native activation is a separate check.' : opts.dry ? 'Preview only. No files written.' : 'Done. Reload your agent and check that Exactwork appears in its skill list.');
    }
  }
} catch (e) {
  console.error(`Exactwork: ${e.message}\nNo existing files are intentionally overwritten. An I/O failure may leave partial new files.`);
  process.exitCode = 2;
}
