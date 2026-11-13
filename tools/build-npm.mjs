#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const output = process.argv[2];
if (!output || !path.isAbsolute(output)) throw Error('Provide an absolute new staging directory.');
if (fs.existsSync(output)) throw Error('Staging directory already exists; use a fresh one.');
fs.mkdirSync(output, {recursive: true});
for (const name of ['bin','lib','skills','LICENSE','VERSION','package.json']) fs.cpSync(path.join(root,name),path.join(output,name),{
  recursive:true,errorOnExist:true,force:false,
  filter: source => !source.split(path.sep).includes('__pycache__') && !/\.py[co]$/.test(source)
});
fs.mkdirSync(path.join(output,'docs'));
fs.copyFileSync(path.join(root,'docs/npm-installation.md'),path.join(output,'docs/npm-installation.md'));
const base='https://github.com/theihtishaam/exactwork-skills/blob/main/';
const raw='https://raw.githubusercontent.com/theihtishaam/exactwork-skills/main/';
let readme=fs.readFileSync(path.join(root,'README.md'),'utf8');
readme=readme.replace(/(!?)\[([^\]]*)\]\(([^)]+)\)/g,(whole,image,label,target)=>{
  if (/^(https?:|#|mailto:)/.test(target)) return whole;
  return `${image}[${label}](${image?raw:base}${target})`;
});
fs.writeFileSync(path.join(output,'README.md'),readme);
console.log(`Prepared ${output}`);
