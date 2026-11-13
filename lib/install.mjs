import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

export const SKILLS = ['exactwork', 'exactwork-research', 'exactwork-review', 'exactwork-handoff', 'exactwork-context', 'exactwork-learn'];
export const AGENTS = {
  codex: {project: '.agents/skills', global: '.agents/skills', markers: ['.codex'], commands: ['codex']},
  claude: {project: '.claude/skills', global: '.claude/skills', markers: ['.claude'], commands: ['claude']},
  opencode: {project: '.opencode/skills', global: '.config/opencode/skills', markers: ['.config/opencode', '.opencode'], commands: ['opencode']},
  harness: {project: '.dsh/skills', global: '.dsh/skills', markers: ['.dsh'], commands: ['dsh']},
  gemini: {project: '.gemini/skills', global: '.gemini/skills', markers: ['.gemini'], commands: ['gemini']},
  copilot: {project: '.github/skills', global: '.copilot/skills', markers: ['.copilot'], commands: ['copilot']},
  cursor: {project: '.cursor/skills', global: '.cursor/skills', markers: ['.cursor'], commands: ['cursor']},
  cline: {project: '.cline/skills', global: '.cline/skills', markers: ['.cline'], commands: ['cline']},
  shared: {project: '.agents/skills', global: '.agents/skills', markers: [], commands: []}
};
export function stat(file) {
  try { return fs.lstatSync(file); } catch (e) { if (e.code === 'ENOENT') return null; throw e; }
}
// No config contents, credentials, shell execution or network are used for detection.
export function detectAgents({home = os.homedir(), project, envPath = process.env.PATH || '', platform = process.platform} = {}) {
  const roots = [home, ...(project ? [project] : [])];
  return Object.entries(AGENTS).filter(([name, a]) => name !== 'shared' && (
    roots.some(root => a.markers.some(m => stat(path.join(root, m))?.isDirectory())) ||
    envPath.split(path.delimiter).filter(Boolean).some(dir => a.commands.some(cmd =>
      (platform === 'win32' ? ['', '.exe', '.cmd', '.bat'] : ['']).some(ext => {
        const s = stat(path.join(dir, cmd + ext)); return s?.isFile() || s?.isSymbolicLink();
      })))
  )).map(([name]) => name);
}
export function checkPath(file) {
  const abs = path.resolve(file);
  const parts = [];
  for (let p = abs;; p = path.dirname(p)) { parts.push(p); if (path.dirname(p) === p) break; }
  for (const p of parts.reverse()) {
    const s = stat(p);
    if (s?.isSymbolicLink()) throw Error(`Link or junction refused: ${p}`);
    if (s && p !== abs && !s.isDirectory()) throw Error(`Parent is not a directory: ${p}`);
  }
  return abs;
}
function readTree(root, expected) {
  checkPath(root);
  if (!stat(root)?.isDirectory()) throw Error(`Expected directory: ${root}`);
  const files = new Map(), dirs = [];
  function visit(folder) {
    for (const name of fs.readdirSync(folder).sort()) {
      const full = path.join(folder, name), rel = path.relative(root, full);
      checkPath(full); const s = stat(full);
      if (s?.isDirectory()) {
        if (expected && !expected.dirs.includes(rel)) throw Error(`Unexpected existing directory: ${full}`);
        dirs.push(rel); visit(full);
      } else if (s?.isFile()) {
        // Refuse unexpected files before reading their contents.
        if (expected && !expected.files.has(rel)) throw Error(`Unexpected existing file: ${full}`);
        files.set(rel, fs.readFileSync(full));
      } else throw Error(`Unsupported file type: ${full}`);
    }
  }
  visit(root); return {files, dirs: dirs.sort()};
}
function equal(a, b) {
  return a.files.size === b.files.size && JSON.stringify(a.dirs) === JSON.stringify(b.dirs) &&
    [...a.files].every(([key, value]) => b.files.get(key)?.equals(value));
}
export function planInstall({bundle, home = os.homedir(), project, agents, skills = SKILLS}) {
  if (!agents?.length) throw Error('No supported tools detected. Select --agent NAME or --all-agents.');
  const names = [...new Set(skills)];
  if (!names.length || names.some(n => !SKILLS.includes(n))) throw Error('Unknown or empty skill selection.');
  if (agents.some(a => !Object.hasOwn(AGENTS, a))) throw Error('Unknown agent selection.');
  const base = checkPath(project || home);
  if (!stat(base)?.isDirectory()) throw Error(`Installation base must be an existing directory: ${base}`);
  const plans = [], destinations = new Set();
  for (const agent of agents) {
    const root = path.join(base, AGENTS[agent][project ? 'project' : 'global']); checkPath(root);
    if (stat(root) && !stat(root).isDirectory()) throw Error(`Skill root is not a directory: ${root}`);
    for (const name of names) {
      const dest = path.join(root, name);
      if (destinations.has(dest)) continue;
      destinations.add(dest);
      const source = readTree(path.join(bundle, 'skills', name));
      if (!source.files.has('SKILL.md')) throw Error(`Missing SKILL.md: ${name}`);
      checkPath(dest); const unchanged = Boolean(stat(dest));
      if (unchanged && !equal(source, readTree(dest, source))) throw Error(`Existing skill differs; no files overwritten: ${dest}`);
      plans.push({name, agent, root, dest, source, unchanged});
    }
  }
  return plans;
}
function makeParents(dir) {
  checkPath(dir);
  const missing = [];
  for (let p = dir; !stat(p); p = path.dirname(p)) missing.push(p);
  for (const p of missing.reverse()) { checkPath(p); fs.mkdirSync(p); }
}
export function applyPlan(plans) {
  // Recheck every destination before the first write; final files use exclusive creation.
  for (const p of plans) {
    checkPath(p.dest);
    if (p.unchanged) {
      if (!equal(p.source, readTree(p.dest, p.source))) throw Error(`Destination changed: ${p.dest}`);
    } else if (stat(p.dest)) throw Error(`Destination appeared: ${p.dest}`);
  }
  for (const p of plans) {
    if (p.unchanged) continue;
    makeParents(p.root); checkPath(p.dest); fs.mkdirSync(p.dest);
    for (const rel of p.source.dirs) { const target = path.join(p.dest, rel); checkPath(target); fs.mkdirSync(target); }
    for (const [rel, data] of p.source.files) { const target = path.join(p.dest, rel); checkPath(target); fs.writeFileSync(target, data, {flag: 'wx'}); }
  }
}
