import sys
sys.dont_write_bytecode = True
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parent
tempfile.tempdir = str(ROOT)
CANDIDATE = ROOT.parents[2] / 'skills/exactwork-learn'
spec = importlib.util.spec_from_file_location('learn_tests', CANDIDATE / 'tests/test_learn.py')
tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
learn = tests.learn

class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self.temp.name).resolve()
        self.proposal, self.evidence, self.base = tests.fixture(self.root)
    def tearDown(self):
        self.temp.cleanup()
    def save_evidence(self):
        (self.root / tests.EVIDENCE).write_bytes(learn.encoded(self.evidence))
    def promote(self):
        return learn.promote(self.root, tests.PROPOSAL, tests.EVIDENCE, learn.TARGET, self.proposal['base_sha256'], True)
    def cli(self, action, *extra):
        return subprocess.run([sys.executable, str(CANDIDATE / 'scripts/learn.py'), action,
            '--project', str(self.root), *extra], capture_output=True)
    def test_real_cli_cannot_apply_rejected_candidate_with_savings(self):
        for row in self.evidence['cases']:
            for arm in ['baseline','candidate']:
                row[arm]['usage'] = {'kind':'actual','measurement_id':'synthetic-boundary','input_tokens':100 if arm=='baseline' else 1,'output_tokens':0}
        for criterion in ['correct','scope']:
            with self.subTest(criterion=criterion):
                self.evidence['cases'][-1]['candidate']['correct'] = True
                self.evidence['cases'][-1]['candidate']['scope'] = True
                self.evidence['cases'][-1]['candidate'][criterion] = False
                self.save_evidence()
                before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                run=self.cli('promote','--proposal',tests.PROPOSAL,'--evidence',tests.EVIDENCE,'--target',learn.TARGET,'--expected-base-sha256',self.proposal['base_sha256'],'--apply')
                self.assertEqual(run.returncode,1,run.stderr)
                self.assertFalse(json.loads(run.stdout)['eligible'])
                self.assertEqual(before,{str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_preexisting_user_edits_survive_real_cli_apply(self):
        edited=b'Explicit independent synthetic user edit\n'
        (self.root/learn.TARGET).write_bytes(edited)
        run=self.cli('promote','--proposal',tests.PROPOSAL,'--evidence',tests.EVIDENCE,'--target',learn.TARGET,'--expected-base-sha256',self.proposal['base_sha256'],'--apply')
        self.assertEqual(run.returncode,2,run.stderr)
        self.assertEqual((self.root/learn.TARGET).read_bytes(),edited)
    def test_pending_cleanup_failure_can_be_retried(self):
        original=learn.exclusive
        def fail_commit(path,data):
            if path.name=='committed.json': raise OSError('synthetic failed commit')
            return original(path,data)
        with patch.object(learn,'exclusive',side_effect=fail_commit), self.assertRaises(learn.Invalid): self.promote()
        pending_path=self.root/'.exactwork/pending.json'
        pending=learn.parse(pending_path.read_bytes())
        original_unlink=Path.unlink
        def fail_cleanup(path,*args,**kwargs):
            if path==pending_path: raise OSError('synthetic pending cleanup failure')
            return original_unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail_cleanup), self.assertRaises(OSError):
            learn.rollback(self.root,pending['version'],self.proposal['candidate']['sha256'],True)
        self.assertEqual((self.root/learn.TARGET).read_bytes(),self.base)
        learn.rollback(self.root,pending['version'],self.proposal['base_sha256'],True)
        self.assertFalse(pending_path.exists())
    def test_falsey_pending_record_is_rejected_before_restore(self):
        result=self.promote()
        (self.root/'.exactwork/pending.json').write_bytes(b'{}\n')
        with self.assertRaises(learn.Invalid):
            learn.rollback(self.root,result['version'],result['sha256'],True)
        self.assertEqual((self.root/learn.TARGET).read_bytes(),(self.root/self.proposal['candidate']['path']).read_bytes())
    def test_pending_cleanup_retry_preserves_new_user_edits(self):
        original=learn.exclusive
        def fail_commit(path,data):
            if path.name=='committed.json': raise OSError('synthetic failed commit')
            return original(path,data)
        with patch.object(learn,'exclusive',side_effect=fail_commit), self.assertRaises(learn.Invalid): self.promote()
        pending_path=self.root/'.exactwork/pending.json'
        pending=learn.parse(pending_path.read_bytes())
        original_unlink=Path.unlink
        def fail_cleanup(path,*args,**kwargs):
            if path==pending_path: raise OSError('synthetic pending cleanup failure')
            return original_unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail_cleanup), self.assertRaises(OSError):
            learn.rollback(self.root,pending['version'],self.proposal['candidate']['sha256'],True)
        edited=b'Synthetic user edit after successful restore, before cleanup retry\n'
        (self.root/learn.TARGET).write_bytes(edited)
        for expected in [self.proposal['base_sha256'], learn.digest(edited)]:
            with self.subTest(expected=expected), self.assertRaises(learn.Invalid):
                learn.rollback(self.root,pending['version'],expected,True)
            self.assertEqual((self.root/learn.TARGET).read_bytes(),edited)
        self.assertTrue(pending_path.exists())
    def test_finite_duration_sum_overflow_has_structured_cli_failure(self):
        for row in self.evidence['cases']:
            for arm in ['baseline','candidate']:
                row[arm]['duration']={'measurement_id':'synthetic-time','milliseconds':1e308}
        self.save_evidence()
        run=self.cli('evaluate','--proposal',tests.PROPOSAL,'--evidence',tests.EVIDENCE)
        self.assertEqual(run.returncode,2,run.stderr)
        self.assertIn('error',json.loads(run.stdout))

if __name__ == '__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(tests),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentReviewTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
