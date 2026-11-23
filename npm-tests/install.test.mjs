import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {SKILLS, AGENTS, detectAgents, planInstall, applyPlan} from '../lib/install.mjs';
const repo = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'exactwork-npm-'));
  t.after(() => {
    const abs = path.resolve(root);
    assert.equal(path.dirname(abs), path.resolve(os.tmpdir()));
    assert.ok(path.basename(abs).startsWith('exactwork-npm-'));
    fs.rmSync(abs, {recursive: true, force: true});
  });
  const home = path.join(root, 'home'), project = path.join(root, 'project');
  fs.mkdirSync(home); fs.mkdirSync(project);
  return {root, home, project, bundle: repo, agents: ['codex']};
}
test('preview creates no skill roots', t => {
  const f = fixture(t); const p = planInstall(f);
  assert.equal(p.length, 6); assert.ok(p.every(x => !x.unchanged));
  assert.deepEqual(fs.readdirSync(f.home), []);
});
test('install delivers all skills and is idempotent', t => {
  const f = fixture(t); delete f.project;
  const plans = planInstall(f); applyPlan(plans);
  for (const p of plans) for (const [rel, bytes] of p.source.files) assert.deepEqual(fs.readFileSync(path.join(p.dest, rel)), bytes);
  assert.ok(planInstall(f).every(x => x.unchanged)); applyPlan(planInstall(f));
});
test('project install does not touch home', t => {
  const f = fixture(t); applyPlan(planInstall(f));
  assert.ok(fs.existsSync(path.join(f.project, '.agents/skills/exactwork/SKILL.md')));
  assert.deepEqual(fs.readdirSync(f.home), []);
});
test('every supported agent has an installable explicit destination', t => {
  const f = fixture(t); f.agents = Object.keys(AGENTS);
  const plans = planInstall(f); assert.equal(plans.length, 8 * 6);
  applyPlan(plans); assert.ok(planInstall(f).every(x => x.unchanged));
});
test('late conflict prevents all selected new destinations', t => {
  const f = fixture(t); f.agents = ['claude']; applyPlan(planInstall(f));
  const changed = path.join(f.project, '.claude/skills/exactwork-learn/SKILL.md');
  fs.writeFileSync(changed, 'user changes'); f.agents = ['codex', 'claude'];
  assert.throws(() => planInstall(f), /differs/);
  assert.equal(fs.existsSync(path.join(f.project, '.agents')), false);
  assert.equal(fs.readFileSync(changed, 'utf8'), 'user changes');
});
test('unexpected existing file blocks a merge', t => {
  const f = fixture(t); applyPlan(planInstall(f));
  const unknown = path.join(f.project, '.agents/skills/exactwork/keep.txt'); fs.writeFileSync(unknown, 'keep');
  assert.throws(() => planInstall(f), /Unexpected existing file/);
  assert.equal(fs.readFileSync(unknown, 'utf8'), 'keep');
});
test('destination appearing after preview blocks writes', t => {
  const f = fixture(t); const p = planInstall(f); fs.mkdirSync(p.at(-1).dest, {recursive: true});
  assert.throws(() => applyPlan(p), /appeared/); assert.equal(fs.existsSync(p[0].dest), false);
});
test('edited identical destination is rechecked before writes', t => {
  const f = fixture(t); applyPlan(planInstall(f)); const p = planInstall(f);
  fs.writeFileSync(path.join(p[0].dest, 'SKILL.md'), 'edited');
  assert.throws(() => applyPlan(p), /changed/);
});
test('unknown agent and skill path traversal are refused', t => {
  const f = fixture(t);
  for (const agents of [['../../outside'], ['__proto__']]) assert.throws(() => planInstall({...f, agents}), /Unknown/);
  assert.throws(() => planInstall({...f, skills: ['../../outside']}), /Unknown/);
});
test('missing project and file roots are refused', t => {
  const f = fixture(t); assert.throws(() => planInstall({...f, project: path.join(f.root, 'absent')}), /existing directory/);
  fs.writeFileSync(path.join(f.project, '.agents'), 'file'); assert.throws(() => planInstall(f), /not a directory/);
});
test('destination junction or symlink is refused without writing through it', t => {
  const f = fixture(t), outside = path.join(f.root, 'outside'); fs.mkdirSync(outside);
  try { fs.symlinkSync(outside, path.join(f.project, '.agents'), process.platform === 'win32' ? 'junction' : 'dir'); }
  catch (e) { if (['EPERM', 'EACCES'].includes(e.code)) return t.skip('link privilege unavailable'); throw e; }
  assert.throws(() => planInstall(f), /Link or junction/); assert.deepEqual(fs.readdirSync(outside), []);
});
test('detection uses only known markers and executable names', t => {
  const f = fixture(t); fs.mkdirSync(path.join(f.home, '.dsh')); fs.mkdirSync(path.join(f.home, '.claude'));
  // Detection does not inspect the marker contents.
  fs.writeFileSync(path.join(f.home, '.claude', 'do-not-read.txt'), 'fixture');
  assert.deepEqual(detectAgents({home: f.home, envPath: ''}), ['claude', 'harness']);
  const bin = path.join(f.root, 'bin'); fs.mkdirSync(bin); fs.writeFileSync(path.join(bin, 'codex.cmd'), 'fixture');
  assert.deepEqual(detectAgents({home: f.project, envPath: bin, platform: 'win32'}), ['codex']);
  assert.deepEqual(detectAgents({home: f.project, envPath: ''}), []);
});
test('PATH detection refuses dangling command symlinks', t => {
  const f = fixture(t);
  const bin = path.join(f.root, 'bin'); fs.mkdirSync(bin);
  const command = path.join(bin, process.platform === 'win32' ? 'codex.cmd' : 'codex');
  try { fs.symlinkSync('missing-command-target', command, 'file'); }
  catch (error) {
    if (['EPERM', 'EACCES', 'ENOTSUP'].includes(error.code)) return t.skip('Symlink privilege unavailable');
    throw error;
  }
  assert.deepEqual(detectAgents({home: f.project, envPath: bin, platform: process.platform}), []);
});
test('PATH detection requires executable files on POSIX', t => {
  if (process.platform === 'win32') return t.skip('POSIX executable mode semantics');
  const f = fixture(t);
  const bin = path.join(f.root, 'bin'); fs.mkdirSync(bin);
  const candidate = path.join(bin, 'codex');
  fs.writeFileSync(candidate, 'placeholder file');
  fs.chmodSync(candidate, 0o644);
  assert.deepEqual(detectAgents({home: f.project, envPath: bin}), []);
  fs.chmodSync(candidate, 0o755);
  assert.deepEqual(detectAgents({home: f.project, envPath: bin}), ['codex']);
});
function cli(args) { return spawnSync(process.execPath, [path.join(repo, 'bin/exactwork-skills.mjs'), ...args], {encoding: 'utf8'}); }
test('CLI verifies an installed selection and refuses incompatible flags', t => {
  const f = fixture(t), args = ['--agent', 'harness', '--project', f.project, '--skill', 'exactwork'];
  assert.equal(cli(['verify', ...args]).status, 2);
  assert.equal(cli(['install', ...args, '--dry-run']).status, 0);
  assert.deepEqual(fs.readdirSync(f.project), []);
  const installed = cli(['install', ...args]); assert.equal(installed.status, 0, installed.stderr);
  assert.match(cli(['verify', ...args]).stdout, /VERIFIED/);
  assert.equal(cli(['install', ...args, '--global']).status, 2);
  assert.equal(cli(['install', ...args, '--all-agents']).status, 2);
  assert.equal(cli(['install', '--unknown']).status, 2);
});
