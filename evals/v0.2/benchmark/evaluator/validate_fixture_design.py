"""Check private oracle solutions, initial faults, and evidence line alignment."""
from pathlib import Path
import importlib.util,json,shutil,tempfile
from grade import ROOT, EXPECTED, grade

reference='''from decimal import Decimal, InvalidOperation, localcontext

def summarize(rows):
    totals={}
    seen={}
    for row in rows:
        status=row['status']
        if status not in ('posted','pending'):raise ValueError('invalid status')
        if status=='pending':continue
        if row['direction'] not in ('credit','debit'):raise ValueError('invalid direction')
        key=(row['currency'],row['id'])
        if key in seen:
            if seen[key]!=row:raise ValueError('conflicting duplicate')
            continue
        try:
            value=Decimal(row['amount'])
        except (InvalidOperation,TypeError,ValueError):raise ValueError('invalid amount') from None
        if not value.is_finite() or value<0 or value.as_tuple().exponent < -2:
            raise ValueError('invalid amount')
        with localcontext() as context:
            context.prec=max(28,len(value.as_tuple().digits)+abs(value.as_tuple().exponent)+3)
            cents=int(value*100)
        seen[key]=dict(row)
        bucket=totals.setdefault(row['currency'],dict(credits_cents=0,debits_cents=0,net_cents=0))
        bucket['credits_cents' if row['direction']=='credit' else 'debits_cents']+=cents
        bucket['net_cents']=bucket['credits_cents']-bucket['debits_cents']
    return totals
'''

with tempfile.TemporaryDirectory(prefix='exactwork-benchmark-design-') as tmp:
    base=Path(tmp)
    for cid in ['d01','d02','d03','d04','h01','h02']:
        dest=base/cid
        shutil.copytree(ROOT/'cases'/cid/'input',dest,ignore=shutil.ignore_patterns('__pycache__'))
        if cid in ['d01','h01']:
            expected=EXPECTED[cid]
            lines=(dest/'run.log').read_text(encoding='utf-8').splitlines()
            findings=[]
            for item in expected['findings']:
                assert item['code'] in lines[item['first_line']-1]
                assert any('Error' in lines[n-1] or 'Timeout' in lines[n-1] for n in item['causal_lines'])
                findings.append(dict(stage=item['stage'],code=item['code'],first_line=item['first_line'],causal_line=item['causal_lines'][0],explanation='Design oracle: '+lines[item['causal_lines'][0]-1],next_check='Inspect the observed cause in the affected stage.'))
            (dest/'answer.json').write_text(json.dumps(dict(job_state=expected['job_state'],capture_complete=expected['capture_complete'],failures=findings)))
        elif cid=='d02':
            assert not grade(cid,dest)['deterministic_success']
            (dest/'report.py').write_text(reference)
            with (dest/'test_report.py').open('a') as out:out.write("\nclass AddedRegression(unittest.TestCase):\n    def test_exact_cents(self):\n        self.assertEqual(summarize([dict(id='a',currency='USD',direction='credit',amount='0.29',status='posted')])['USD']['credits_cents'],29)\n")
        elif cid=='d03':
            answer=dict(EXPECTED[cid])
            answer.update(recommendation='Run matched tasks with the same model and settings, repeated trials, and complete usage before a causal performance claim.',source_sections=['A','B','D'])
            (dest/'answer.json').write_text(json.dumps(answer))
        elif cid=='d04':
            p=dest/'ui-labels.json'
            p.write_bytes(p.read_bytes().replace(b'Pay noww',b'Pay now'))
        else:
            spec=importlib.util.spec_from_file_location('queue_probe',dest/'task_queue.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            a,b=module.TaskQueue(2),module.TaskQueue(2)
            a.put('x');assert b.get()=='x'
            q=module.TaskQueue(1,items=[]);q.put('a')
            try:q.put('b')
            except OverflowError:pass
            else:raise AssertionError('overflow not reproduced')
            assert len(q)==2
            (dest/'answer.json').write_text(json.dumps({'findings':[{'file':'task_queue.py','line':2,'trigger':'Create a and b; put x in a; get from b','observed':'b returns x','expected':'b empty','explanation':'default list shared'},{'file':'task_queue.py','line':9,'trigger':'capacity 1 fresh list; put a then b','observed':'OverflowError but len is 2','expected':'len remains 1','explanation':'mutation precedes capacity rejection'}]}))
        result=grade(cid,dest)
        assert result['deterministic_success'],result
        print(cid, 'design verified',result['passed'], '/',result['total'])
print('All six fixture designs verified. These are oracle checks, not model trials.')
