# Component measurements

`performance-repeats.json` is the original six-sample measurement record with local path prefixes removed. `performance-repeats.md` explains the experiment. Both measured implementations are supplied: `context_slice_before.py` and the released `skills/exactwork-context/scripts/context_slice.py`.

To reproduce on your machine, run `python performance_repeat_coordinator.py --output NEW_RESULT_DIRECTORY` from here. The result directory must not already exist. The script generates a synthetic 1.6 MB file, executes three alternating-order pairs in fresh processes, verifies full output equality, and writes new reports and sample outputs to the new directory. Published records are preserved. Imports, process launch, fixture creation, and output-file writes are excluded from the timing interval. Expect results to differ with hardware and load. This script does not invoke an AI model or network.

The comparison concerns an inefficient draft of our own helper, not Ponytail, ripgrep, or the prior released instructions. Long source lines are deliberately truncated to the output budget and marked as such. Equal output proves equality of that selection, not semantic completeness of a diagnosis.

Instruction and excerpt counts use `o200k_base` in the recorded authoring environment. An excerpt is only part of the input an agent may need. These counts are not billed usage or proof of task-token savings.
