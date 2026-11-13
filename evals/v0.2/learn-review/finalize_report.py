import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,datetime
root=Path(r'<WORKSPACE>/work/v02/learn-review')
script=root.parent/'learn_candidate/scripts/learn.py'
sha=hashlib.sha256(script.read_bytes()).hexdigest()
report=root/'review-results.md'
text=report.read_text(encoding='utf-8-sig')
text=text.replace('Status: initial reproduction complete; implementation fixes and independent verification pending.', 'Status: all three reproduced defects were fixed by the author and independently verified. Final combined suite: 38 tests passed in 5.707 seconds (32 candidate tests plus 6 independent tests).')
text=text.replace('Real `promote --apply` rejected a candidate with a failed scope label despite declared token savings;', 'Real `promote --apply` separately rejected failed correctness and scope labels despite declared token savings;')
text += f'''
## Final fix verification

- Completed rollback with a matching remaining pending transaction permits a cleanup-only retry using the restored expected hash. It verifies the completion marker and backup, and does not rewrite the procedure. A new intervening user edit is still rejected and preserved.
- Every existing pending JSON record is validated, including falsey values. The candidate regression covers `{{}}`, `null`, `[]`, `false`, `0`, and an empty JSON string.
- Nonfinite aggregate telemetry is rejected before returning or persisting an evaluation; the real CLI now returns structured JSON with exit 2 for the reproduced overflow.
- The original 29 tests, three author-added regressions, and all six independent review tests passed together. The independent CLI gate test contains separate correctness and scope subcases; the recovery edit test checks both claimed restored and edited hashes.
- Final reviewed script SHA-256: `{sha}`.
- Candidate MIT frontmatter and the existing MIT LICENSE were added as requested. Main benchmark candidate source was not modified.

Reproduce with `python work/v02/learn-review/test_independent_review.py` from the workspace. The harness places all temporary fixtures beneath `learn-review` and disables Python bytecode writes. `verification.json` records the observed test result and final source identity. This is local implementation verification, not evidence that the learner improves model performance.
'''
report.write_text(text,encoding='utf-8')
verification={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runner':'work/v02/learn-review/test_independent_review.py','candidate_tests':32,'independent_tests':6,'total_tests':38,'passed':38,'failures':0,'errors':0,'observed_suite_seconds':5.707,'script_sha256':sha,'reviewed_scope':'learn_candidate only; main experiment candidate unchanged','initial_reproduced_failures':['pending-cleanup retry blocked by completed marker','falsey pending JSON bypasses validation','finite duration aggregate overflow breaks structured CLI result'],'final_status':'all reproduced defects fixed and independently verified'}
(root/'verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verification))
