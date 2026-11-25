# Run plan: Corvane Mutual v1, full recipe, on msock-dev code (2026-11-18)

Engine checkout: `~/Downloads/MSOCK/MSOCK_repo/K1_MSOCK-msockdev` (commit 6170d52f7). Estate: the in-place folder
`estates/corvane-mutual/estate/corvane-estate` (543 files after the weak-spot additions). Run settings:
`run-full-v1-msockdev.yaml` (70 questions T01-T70, two sources) with `recipe-full-msockdev.yaml`. What changed and why:
`estates/stage-validation/expected-estate/corvane-weakspot-changes.json`.

Prerequisites are those of `LOCAL-RUN-GUIDE.md` (grammar cache in `~/Library/Caches/tree-sitter-language-pack`, made
private; `uv` on the PATH). `MSOCK_LOCAL_PROFILE=1` is for a laptop only.

```bash
cd ~/Downloads/MSOCK/MSOCK_repo/K1_MSOCK-msockdev
export PATH=$HOME/.local/bin:$PATH
mkdir -p .work
W=.work/corvane-v1-full                  # the work folder
C=.work/corvane-v1-full-capture          # the capture folder the comparator reads (W/../<W name>-capture)
mkdir -p $C/probes
# receipts in W/msock.db, counted read-only (used before and after the SQ-C10 probes)
count_receipts() { uv run python -c "import sqlite3; c = sqlite3.connect('file:$W/msock.db?mode=ro', uri=True); \
print(c.execute(\"SELECT count(*) FROM answer_receipts WHERE project='corvane-mutual'\").fetchone()[0])"; }
```

### Capture layout (what `estates/stage-validation/verify_run.py` reads for stages A, T, P and Q)

| file in `$C` | written by | read for |
|---|---|---|
| `report-sitting1.json` | sitting 1 stdout (`tee`); a Temporal banner before the JSON is skipped | asks (status, code, mode) T01-T70, certificate, publication: D-Q-001..004, D-Q-030..091, N-Q-001, D-T-040, N-T-001, D-T-045, D-P-029 |
| `run.log` | sitting 1 stderr | reviewer only |
| `report-sitting2.json`, `run-2.log` | sitting 2 | needle scan of answers (D-Q-023..028) |
| `report-sitting3.json`, `run-3.log` | sitting 3 (optional) | D-T-035 |
| `probes/receipts-before.txt` | `count_receipts` before the probes | D-Q-018, D-Q-020 |
| `probes/version-2.txt` | `msock ask --version 2` stdout + `exit: <code>` | D-Q-016 |
| `probes/version-1-T07.txt` | `msock ask --version 1` stdout + `exit: <code>` | D-Q-018, and the end of sitting 1's receipt window (N-Q-002) |
| `probes/version-two.txt` | `msock ask --version two` stdout + `exit: <code>` | D-Q-017 |
| `probes/receipts-after.txt` | `count_receipts` after the three probes | D-Q-018, D-Q-020 |
| `probes/version-3.txt` | `msock ask --version 3` after sitting 2, stdout + `exit: <code>` | D-Q-019 |

No per-question answer files are needed: the harness asks each run-file question through Ask, which commits every
delivered answer and its receipt to `answer_receipts` in `$W/msock.db` (in ask order; refused answers write none), and
the report's `phases.after_run.asks` keeps each question's status, mode and refusal code. The comparator pairs the two.
The package (`$W/objects/packages/corvane-mutual/1`), the keys (`$W/keys`, for the manifest signature and sealed
receipts), the CheckResult, versions, certificates and gap rows are read from the work folder itself.

The default `--run-timeout` is 900 seconds; the full recipe with AI stages takes longer, so add for example
`--run-timeout 14400` to sittings 1 to 3 if the run stops with exit 1 at the timeout.

## Sitting 1: the full run

```bash
MSOCK_LOCAL_PROFILE=1 uv run msock run ../estates/corvane-mutual/local-run --config run-full-v1-msockdev.yaml \
  --work $W --fresh --census .work/corvane-v1-full-census \
  2> $C/run.log | tee $C/report-sitting1.json
```

(`.work/corvane-v1-full.json` / `.log` in older notes are these two files.)

Look for:

- Stage 00 (S00-C7, multi-source): two stage-00 jobs, `claims#source:corvane-estate` pinned and
  `claims#source:corvane-archive` failed then parked. The archive folder does not exist, so the file-drop connector
  copies nothing and stops with `CON-004 nothing was copied`: code `connector_failed` (its kind CON-004), failure class
  `part_fault`, one retry, then parked for good. It is **not** `source_unreachable` (that code comes only from git and
  the database connectors). Because `part_fault` is parked for good it counts as a named gap, outside the parked share,
  so stage 00 ends `proceed_with_gaps` and corvane-estate carries on. A `source_unreachable` park would not be a gap:
  with two sources its share (0.5) is above `stop_above` (0.20) and the lane would stop.
- Stage 04 (S04-C14): one stage-04 record held by gate.admit, steering rule `new-identity`: the Configuration
  `claims.triage.referral-note` from `services/claims-service/src/main/java/com/corvane/claims/service/ReferralNoteSettings.java:16`
  (state `candidate`, a review item). S09-C7 / S10-C11 only if that held element reaches stages 09 / 10.
- Stage 05 (S05-C12): comprehender-doc jobs held at gate.ai-in also for `docs/help/claims-chatbot-faq.html`
  (role-markup), `docs/help/claim-payout-timescales.html` (invisible-characters) and
  `ops/runbooks/manual-claim-approval.md` (new-identity), besides the earlier X18/G17 files.
- Ask (Q): 70 answers. Expected for T61-T70: T61, T62, T63 refused (`guard_denied`); T64 refused when its file window
  includes runbook lines 9-10, else answered; T65-T68 `not_known`; T69 and T70 answered with the email and the IBAN
  masked. The full-run expected distribution therefore becomes answered 56, not_known 8, refused 6 (T64 may move one
  from refused to answered), and 64 receipts (65 if T64 is answered).

### Extra Ask commands after sitting 1 (SQ-C10)

Run these **before sitting 2**: sitting 2 publishes again, and its version could then be number 2.

```bash
Q="What is the auto-approve limit for claims in production?"
count_receipts > $C/probes/receipts-before.txt

# A version above the pointer: Ask raises NoSuchVersion (HTTP 404 version_not_found); the command line prints
# {"status": "refused", "code": "version_not_found", "reason": "no version 2"} and exits 2. It is not not_known.
MSOCK_LOCAL_PROFILE=1 uv run msock ask $W "$Q" --project corvane-mutual --as rita --version 2 \
  > $C/probes/version-2.txt 2>> $C/probes/stderr.log; echo "exit: $?" >> $C/probes/version-2.txt

# The same question pinned to version 1: answered, receipt version corvane-mutual/1 (SQ-C4).
MSOCK_LOCAL_PROFILE=1 uv run msock ask $W "$Q" --project corvane-mutual --as rita --version 1 \
  > $C/probes/version-1-T07.txt 2>> $C/probes/stderr.log; echo "exit: $?" >> $C/probes/version-1-T07.txt

# A version id that is not a number: NoSuchVersion as well ("no version two").
MSOCK_LOCAL_PROFILE=1 uv run msock ask $W "$Q" --project corvane-mutual --as rita --version two \
  > $C/probes/version-two.txt 2>> $C/probes/stderr.log; echo "exit: $?" >> $C/probes/version-two.txt

count_receipts > $C/probes/receipts-after.txt     # expected: before + 1 (only the version-1 probe writes one)
```

A withdrawn or redacted version would give HTTP 410 `version_withdrawn` with `newest_readable`; nothing in this plan
withdraws a version.

## Sitting 2: the same estate again, same work folder (reuse)

No `--fresh`, nothing changed in the estate or the run settings:

```bash
MSOCK_LOCAL_PROFILE=1 uv run msock run ../estates/corvane-mutual/local-run --config run-full-v1-msockdev.yaml \
  --work $W --census .work/corvane-v1-full-census-2 \
  2> $C/run-2.log | tee $C/report-sitting2.json
```

Expected reuse:

- S00-C8: the stage-00 job of corvane-estate copies again but freezes to the same snapshot id (re-pinned, no new
  `source_snapshots` row). corvane-archive fails and parks again in the same way.
- S01-C10: the same snapshot id re-pinned (`last_pinned_at` moves), 0 new `source_snapshots` rows.
- S04-C13: every stage-04 job `reused`, 0 new stage-04 attempts.
- S05-C15: 0 new stage-05 `ai_calls`; stage-05 jobs reused.
- S07-C10: every stage-07 lens job (and the critic, if planned) reused, 0 new stage-07 `ai_calls`.
- S08-C9: every stage-08 producer and reconciler job reused, 0 new stage-08 `ai_calls`.

The local harness always publishes (`--no-publish` is not honoured locally), so sitting 2 may publish a second
version. After it, repeat the SQ-C10 probe one number higher:

```bash
MSOCK_LOCAL_PROFILE=1 uv run msock ask $W "$Q" --project corvane-mutual --as rita --version 3 \
  > $C/probes/version-3.txt 2>> $C/probes/stderr.log; echo "exit: $?" >> $C/probes/version-3.txt
```

Note whether `latest` is now version 1 or 2 (the receipts of sitting 2 say which).

## Sitting 3 (optional): the after-run check in full mode (ST-C6)

`checks.mode: full` is not set in `recipe-full-msockdev.yaml`: msock-dev resolves and accepts it, but its Checker has
no usefulness measure wired, so a full check always fails ("usefulness: not measured") and the harness then stops
before publish, which would remove every Ask answer from sittings 1 and 2. It runs on its own instead:

```bash
MSOCK_LOCAL_PROFILE=1 uv run msock run ../estates/corvane-mutual/local-run --config run-full-v1-checksfull-msockdev.yaml \
  --work .work/corvane-v1-checksfull --fresh --census .work/corvane-v1-checksfull-census \
  2> $C/run-3.log | tee $C/report-sitting3.json
```

Keep the work folder name `.work/corvane-v1-checksfull`: the comparator finds it next to `$W` (D-T-036).

Expected: the run report's after-run step shows `check.mode: full` and `passed: false` with the failure
"usefulness: not measured" (and accuracy failures for any dimension whose sample is not graded), then
`publication: not_reached: the rule-only check failed`. No `check_mode_unavailable` (that is only for refresh).

## Judging the run (the assurance comparator)

After sitting 1 and its probes (and again after sitting 2), from the engine checkout; it only reads `$W` and `$C`:

```bash
cd ~/Downloads/MSOCK/MSOCK_repo/estates/stage-validation
../../K1_MSOCK-msockdev/.venv/bin/python verify_run.py ../../K1_MSOCK-msockdev/.work/corvane-v1-full \
  --out assurance/verdicts-corvane-v1-full.json
# defaults: --capture ../../K1_MSOCK-msockdev/.work/corvane-v1-full-capture, --report <capture>/report-sitting1.json,
# --expected assurance/expected.json, --golden golden-corvane.json
```

## Reading the results

```bash
cd ~/Downloads/MSOCK/MSOCK_repo/estates/corvane-mutual/local-run
W=../../../K1_MSOCK-msockdev/.work/corvane-v1-full
python3 stage_view.py $W summary
python3 stage_view.py $W jobs 00          # the two sources: pinned and parked
python3 stage_view.py $W held             # parked jobs and review items (the held Configuration record)
```
