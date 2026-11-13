"""Private outcome verifier. Never include this file in an agent task workspace."""
from pathlib import Path
import argparse, copy, importlib.util, json, math, shutil, subprocess, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=json.loads((Path(__file__).parent/'private_expected.json').read_text())

def grade(cid, workspace):
    checks=[]
    def add(name,passed,detail=None):
        checks.append({'check':name,'passed':bool(passed),'detail':detail})
    fixture=ROOT/'cases'/cid/'input'
    generated={p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    initial={p.relative_to(fixture).as_posix() for p in fixture.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if cid=='d02':
        allowed={'report.py','test_report.py','answer.md'} | {p for p in generated if Path(p).name.startswith('test_') and p.endswith('.py') and '/' not in p}
        for name in initial-{'report.py','test_report.py'}:
            add('preserve '+name,(workspace/name).exists() and (workspace/name).read_bytes()==(fixture/name).read_bytes())
        add('no unrelated files',not (generated-initial-allowed),sorted(generated-initial-allowed))
        add('regression artifact',any((workspace/n).read_bytes()!=(fixture/n).read_bytes() for n in ['test_report.py'] if (workspace/n).exists()) or any(n.startswith('test_') and n not in initial for n in generated))
        try:
            run=subprocess.run([sys.executable,'-B','-m','unittest','discover','-v'],cwd=workspace,capture_output=True,text=True,timeout=20)
            add('candidate regression suite passes',run.returncode==0,(run.stdout+run.stderr)[-1800:])
            with tempfile.TemporaryDirectory(prefix='exactwork-regression-oracle-') as scratch:
                copied=Path(scratch)
                for path in workspace.glob('*.py'):shutil.copy2(path,copied/path.name)
                (copied/'report.py').write_bytes((fixture/'report.py').read_bytes())
                baseline=subprocess.run([sys.executable,'-B','-m','unittest','discover','-v'],cwd=copied,capture_output=True,text=True,timeout=20)
                # A regression test should distinguish vulnerable from repaired behavior.
                add('regression detects original defect',baseline.returncode!=0 and ('FAIL:' in baseline.stderr or 'ERROR:' in baseline.stderr),(baseline.stdout+baseline.stderr)[-1800:])
        except Exception as exc:add('regression execution',False,type(exc).__name__+': '+str(exc))
        try:
            spec=importlib.util.spec_from_file_location('candidate_report',workspace/'report.py')
            mod=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            f=mod.summarize
            def row(id='a',currency='USD',direction='credit',amount='0.29',status='posted'):
                return dict(id=id,currency=currency,direction=direction,amount=amount,status=status)
            def bucket(c,d):return {'credits_cents':c,'debits_cents':d,'net_cents':c-d}
            def exact(name, rows, expected):
                before=copy.deepcopy(rows)
                try:
                    result=f(rows)
                    add(name,result==expected,{'actual':result,'expected':expected})
                except Exception as exc:add(name,False,type(exc).__name__+': '+str(exc))
                add(name+' input preserved',rows==before)
            def rejects(name,rows):
                before=copy.deepcopy(rows)
                try:f(rows)
                except ValueError:add(name,True)
                except Exception as exc:add(name,False,'Wrong error: '+type(exc).__name__)
                else:add(name,False,'No ValueError')
                add(name+' input preserved',rows==before)
            exact('exact cents',[row()],{'USD':bucket(29,0)})
            exact('currency-scoped id',[row(),row(currency='EUR',amount='3.00')],{'USD':bucket(29,0),'EUR':bucket(300,0)})
            exact('retry deduplication',[row(),row()],{'USD':bucket(29,0)})
            exact('legitimate opposing entries',[row(),row(id='b',direction='debit')],{'USD':bucket(29,29)})
            exact('preserve currency case',[row(),row(currency='usd')],{'USD':bucket(29,0),'usd':bucket(29,0)})
            exact('large exact amount',[row(amount='90071992547409.93')],{'USD':bucket(9007199254740993,0)})
            exact('pending not parsed',[row(status='pending',amount='not money')],{})
            exact('empty input',[],{})
            rejects('conflicting retry',[row(),row(amount='1.00')])
            for value in ['0.001','NaN','Infinity','-1.00']:
                rejects('invalid amount '+value,[row(amount=value)])
            rejects('invalid direction',[row(direction='refund')])
            rejects('invalid status',[row(status='unknown')])
        except Exception as exc:add('module execution',False,type(exc).__name__+': '+str(exc))
    elif cid=='d04':
        expect=(fixture/'ui-labels.json').read_bytes().replace(b'Pay noww',b'Pay now')
        add('exact requested edit',(workspace/'ui-labels.json').exists() and (workspace/'ui-labels.json').read_bytes()==expect)
        add('other file unchanged',(workspace/'README.md').exists() and (workspace/'README.md').read_bytes()==(fixture/'README.md').read_bytes())
        add('no extra artifacts',generated==initial,sorted(generated-initial))
    else:
        for name in initial:
            add('preserve '+name,(workspace/name).exists() and (workspace/name).read_bytes()==(fixture/name).read_bytes())
        add('only requested output',not(generated-initial-{'answer.json'}),sorted(generated-initial-{'answer.json'}))
        try:
            answer=json.loads((workspace/'answer.json').read_text(encoding='utf-8-sig'))
            add('valid JSON object',isinstance(answer,dict))
            if cid in ['d01','h01']:
                exp=EXPECTED[cid]
                add('job state',answer.get('job_state')==exp['job_state'])
                add('capture completeness',answer.get('capture_complete') is exp['capture_complete'])
                findings=answer.get('failures',[])
                add('findings list',isinstance(findings,list))
                findings=findings if isinstance(findings,list) else []
                add('exact distinct failure inventory',len(findings)==len(exp['findings']) and {f.get('code') for f in findings if isinstance(f,dict)}=={f['code'] for f in exp['findings']})
                for item in exp['findings']:
                    matches=[f for f in findings if isinstance(f,dict) and f.get('code')==item['code']]
                    found=matches[0] if len(matches)==1 else {}
                    add(item['code']+' stage',found.get('stage')==item['stage'])
                    add(item['code']+' first evidence line',found.get('first_line')==item['first_line'])
                    add(item['code']+' cause evidence line',found.get('causal_line') in item['causal_lines'])
                    add(item['code']+' explanation and next check',bool(found.get('explanation')) and bool(found.get('next_check')))
                # Semantic causal interpretation and grounded next checks still need blind review.
            elif cid=='d03':
                for field in ['observed_success','standardized_success','total_tokens_per_run']:
                    for arm,value in EXPECTED[cid][field].items():
                        actual=answer.get(field,{}).get(arm)
                        add(field+' '+arm,isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isclose(actual,value,rel_tol=1e-6,abs_tol=1e-6))
                for field in ['causal_improvement_established','total_token_reduction_established']:
                    add(field,answer.get(field) is False)
                declared = ['A — Baseline run', 'B — Candidate run', 'C — Launch draft', 'D — Decision requirement']
                aliases = {heading: heading[0] for heading in declared}
                aliases.update({heading[0]: heading[0] for heading in declared})
                supplied = answer.get('source_sections', [])
                identified = {aliases.get(' '.join(value.split())) for value in supplied if isinstance(value, str)} if isinstance(supplied, list) else set()
                add('sources identify data sections',{'A','B'}.issubset(identified))
                add('recommendation exists',bool(answer.get('recommendation')))
                # Semantic recommendation, source interpretation, and causal caveat require blind review.
            elif cid=='h02':
                findings=answer.get('findings')
                add('structured findings',isinstance(findings,list) and all(isinstance(f,dict) and all(f.get(k) is not None for k in ['file','line','trigger','observed','expected','explanation']) for f in findings))
                # Do NOT judge review quality by keyword matching or a forced finding count.
                add('review requires independent semantic grading',True,'Private rubric: reproduce triggers; two known independent defects; reward only supported consequences, allow additional valid findings.')
        except Exception as exc:add('read answer',False,type(exc).__name__+': '+str(exc))
    return {'case':cid,'passed':sum(c['passed'] for c in checks),'total':len(checks),'deterministic_success':all(c['passed'] for c in checks),'semantic_review_required':cid in ['d01','d03','h01','h02'],'checks':checks}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('case',choices=['d01','d02','d03','d04','h01','h02'])
    ap.add_argument('workspace',type=Path)
    args=ap.parse_args()
    result=grade(args.case,args.workspace.resolve())
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['deterministic_success'] else 1)
