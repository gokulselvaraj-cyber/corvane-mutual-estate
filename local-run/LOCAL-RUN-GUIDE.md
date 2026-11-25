# Running the Corvane estate locally, stage by stage

> **Retired 2026-11-24:** the `K1_MSOCK-develop` checkout this guide uses was removed. Its run results are in `estates/stage-validation/archive-develop/` and its contract schemas are in `estates/stage-validation/contract-schemas/`. Current runs use `K1_MSOCK-msockdev` (see `run-plan-full.md`).

The local run uses MSOCK's own one-machine harness from the **Develop** branch. The engine runs in one process, the
database is one SQLite file, objects are plain folders, and Temporal runs as its dev server. Every stage leaves its
trace in the work folder, so you can see what went in, what each job did, where it was stored and what came out.

Develop is not exactly what msock-dev runs (the msock-dev branch is about 500 commits apart and has the local harness
removed). Stage behaviour is close but not identical; check a surprising result against the site before reporting it.

## Where things are

| What | Path |
|---|---|
| Engine checkout (Develop, detached worktree) | `~/Downloads/MSOCK/MSOCK_repo/K1_MSOCK-develop` |
| Run settings (this folder, never uploaded) | `~/Downloads/MSOCK/MSOCK_repo/estates/corvane-mutual/local-run/` |
| The estate it reads | `../estate-v2/corvane-estate` (v2), as a file-drop source |
| Temporal dev server | `~/Library/Caches/msock-temporal/` (done) |
| Tree-sitter grammars | `~/Library/Caches/tree-sitter-language-pack/` (**missing**, see step 0) |

Files here:

| File | Purpose |
|---|---|
| `run-rules.yaml` + `recipe-rules.yaml` | Run 1: standard recipe 2026.10.47 with stages 05, 07, 08 (the optional AI stages) off |
| `run-full.yaml` + `recipe-full.yaml` | Run 2: the standard recipe as it is; stops at the first AI stage with no recorded answer |
| `stage_view.py` | Read-only viewer for a run's `msock.db` |

**One local-only change in the engine worktree** (uncommitted; `git diff` in `K1_MSOCK-develop` shows it): line 23 of
`registry/reference-samples/json-schema.expect.yaml` is commented out. The JSON Schema reader (2.0.10 and 2.0.11)
leaves a `#/definitions/...` reference unresolved (`raw:`) when the schema has no `$id`, so it fails its own
reference sample at start-up. The start-up check judges the **unchanged standard recipe**, so a product-recipe
override cannot route around it, and the run refuses with `bound_part_missing: 2 parts`. msock-dev does not hit this
because its parts arrive pre-approved in the signed seed bundle, so the reader bug is probably live there too.
Worth reporting to the parse-core owners. Corvane has no `*.schema.json` files.

## Step 0: the grammars (blocked today)

The company web filter blocks the grammar download from GitHub. Until the folder exists, every code reader fails
its check at start-up and the run refuses with `bound_part_missing: 42 parts` (all `no_key_1`).

Get the Linux x86_64 grammar folder from the platform team: it is baked into every MSOCK service image at
`/opt/msock/cache/tree-sitter-language-pack`. Put it at `~/Library/Caches/tree-sitter-language-pack`, then check it:

```bash
cd ~/Downloads/MSOCK/MSOCK_repo/K1_MSOCK-develop
export PATH=$HOME/.local/bin:$PATH
uv run python ops/dev/grammars.py        # exit 0: every grammar matches the pinned checksums
```

The check compares each library's bytes with `deploy/image/grammars.lock.json`, so a copied folder is verified.

The pack also refuses a cache folder that group or others can write to, and then every reader quietly writes only
gaps (the start-up check reports `CNF-013 ... made no item`). After copying, make it private:

```bash
C=~/Library/Caches/tree-sitter-language-pack
find $C -type d -exec chmod 700 {} +; find $C -type f -exec chmod 600 {} +; find $C -name '*.so' -exec chmod 700 {} +
```

Done on 18 Nov 2026 from msock-dev's `msock/pool-worker:msock-dev-d8ba98e3-b132` image (layer 15 only).

## Step 1: run the estate

From the engine checkout (`export PATH=$HOME/.local/bin:$PATH` first):

```bash
# Run 1: rules only, end to end (about 5 to 15 minutes; the first minutes are the parts' start-up checks)
MSOCK_LOCAL_PROFILE=1 uv run msock run ../estates/corvane-mutual/local-run --config run-rules.yaml \
  --work .work/corvane-rules --fresh --census .work/corvane-rules-census 2> .work/corvane-rules.log | tee .work/corvane-rules.json

# Run 2: AI stages on; stops at the frontier and writes what the AI jobs would have been asked
MSOCK_LOCAL_PROFILE=1 uv run msock run ../estates/corvane-mutual/local-run --config run-full.yaml \
  --work .work/corvane-full --fresh --census .work/corvane-full-census 2> .work/corvane-full.log | tee .work/corvane-full.json

# Ask the published version (run 1)
MSOCK_LOCAL_PROFILE=1 uv run msock ask .work/corvane-rules "Who calls the claims-service approve endpoint?" \
  --project corvane-mutual --as rita
```

`MSOCK_LOCAL_PROFILE=1` is required on a laptop and must never be set on a shared installation.

Exit codes: `0` finished; `2` stopped at a frontier of missing AI answers, a plan limit, or a refusal (each named on
stderr); `3` a job stopped for another reason or a lane failed; `1` could not run or hit `--run-timeout`.

## Step 2: read it stage by stage

`stage_view.py` opens `msock.db` read-only. Start with the summary, then drill in:

```bash
cd ~/Downloads/MSOCK/MSOCK_repo/estates/corvane-mutual/local-run
W=../../../K1_MSOCK-develop/.work/corvane-rules
python3 stage_view.py $W summary          # jobs by stage and status, errors, records, AI calls
python3 stage_view.py $W snapshot         # what was frozen (stage 01) and what was quarantined
python3 stage_view.py $W jobs 04          # every stage-04 job: part, unit, status, error
python3 stage_view.py $W jobs 04 failed   # only the failed ones
python3 stage_view.py $W job 3fa9         # one job by key prefix: spec (its inputs), attempts, events, records
python3 stage_view.py $W records 09       # what stage 09 wrote, by type, state and trust level
python3 stage_view.py $W graph            # the assembled graph: nodes, links, known unknowns
python3 stage_view.py $W held             # parked jobs, operator queue, review items
python3 stage_view.py $W events 60        # the last 60 run events
```

### What to look at for each stage

| Stage | Input | Processing | Where it is stored | Output and status |
|---|---|---|---|---|
| 00 Add sources | `run-*.yaml` `sources:` | file-drop connector part | `source_registrations` | registration row per source |
| 01 Copy and freeze | the estate folder | copy, fingerprint, secret scan at `gate.ingest`, data-sample rule | `source_snapshots`, `snapshot_files`, `source_blobs`; bytes under `objects/` | `snapshot` view: `quarantined`, `data_class` per file |
| 02 Take stock | frozen files | one unit per file, kind from the ontology | `jobs` (stage 02), units in each job's `unit_key` | `jobs 02` |
| 03 Plan (G1) | units and recipe | not-covered report; scope signed by policy (`policy:unattended`) | `review_steps`, `run_events` | `summary`, `REVIEW STEPS` |
| 04 Read by rules | one frozen file per job | sealed reader part (bwrap sandbox), then its map | `jobs`, `attempts`; reader output under `objects/msock-jobs/<key>/output/bundle/` (`manifest.json`, `records-*.jsonl`) | `jobs 04`; `records 04`; `error_code` on failures (e.g. `ContractError`) |
| 05 Read with AI | units the parsers can't read | AI reader via the gateway, masked prompt | `ai_calls`, `ai_results`, `budget_ledger` | off in run 1; in run 2 the census names each missing answer |
| 06 Index | records of each unit | search index | `search_lists`, `search_entries` | `summary` |
| 07 Find patterns / 08 Write up | records, index | deterministic queries, then AI write-ups | `jobs`, `records`, `ai_calls` | off in run 1 |
| 09 Model things | candidate records | identity resolver; proposals accepted by review mode | `records` (stage 09), `review_items`, `lifecycle_events` | `records 09`; `held` |
| 10 Link things | modelled things | legal links only; unresolved references become known unknowns (D21) | `records` (stage 10), `open_items` | `records 10` |
| A Assemble | admitted records | composer build, 21 dimension statuses, deliverables | `builds`, `graph_nodes`, `graph_links`, `graph_unknowns`, `components` | `graph`; run report `phases` |
| T Check | the build | every citation re-checked against the frozen file | `checker_figures`, `line_coverage` | run report |
| P Publish | the checked candidate | versioned folder, manifest, signature (local HMAC key in `keys/`) | `versions`, `objects/packages/` | `versions` row, `version_id` in the run report |
| Q Ask | the published version | answer with a receipt | `answer_receipts`, `answer_cache` | `msock ask` output |

### Logs and reports

| What | Where |
|---|---|
| The run's report (stages, lanes, frontier, held, gaps, spend) | stdout: `.work/corvane-*.json` |
| Why a job or lane stopped, refusals | stderr: `.work/corvane-*.log` (`held:`, `stopped:`, `failed:` lines) |
| Frontier census: each AI job that had no answer, and what it needed | `--census` folder: `<estate>-frontier-<stage>.json` |
| Simulated time and cost per stage | `--census` folder: `<estate>-timings.json` |
| Per-job event trail | `run_events` (`events` view, or `job <key>`) |
| Spans with durations and tokens | `telemetry_spans` table |
| Parked jobs and why | `dead_letter`, `operator_queue` (`held` view) |

Times in the report are simulated seconds (a fixed clock), so two runs of the same estate are byte-identical.

## Comparing with run 92 on msock-dev

Run 92 parked at stage 05 (OutputUnparseable, PromptOverLimit, GuardDenied) and failed in stage 10 on a heartbeat
timeout. Locally, run 2's census shows the stage-05 jobs and their prompts' sizes without spending anything, and
run 1 shows whether the six stage-04 ContractErrors (java, liquibase, python, csharp, ddl, go) reproduce on Develop:
`python3 stage_view.py $W jobs 04 failed`, then `job <key>` on each.
