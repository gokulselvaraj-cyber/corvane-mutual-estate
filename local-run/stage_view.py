#!/usr/bin/env python3
"""Read-only view of a local MSOCK run's work folder (msock.db), stage by stage.

    python3 stage_view.py WORK summary                  # every stage: jobs by status, errors, records, AI calls
    python3 stage_view.py WORK jobs [STAGE] [STATUS]    # the jobs of a stage (e.g. 04), optionally one status
    python3 stage_view.py WORK job JOB_KEY_PREFIX       # one job: spec, attempts, events, AI calls, records it wrote
    python3 stage_view.py WORK snapshot [PATTERN]       # frozen files: size, lines, quarantine, data class, code page
    python3 stage_view.py WORK records [STAGE]          # records by stage, type, state and trust level
    python3 stage_view.py WORK graph                    # graph size of the newest build, nodes by kind, known unknowns
    python3 stage_view.py WORK events [N]               # the last N run events (default 40)
    python3 stage_view.py WORK held                     # parked jobs, the operator queue and review items

The database is opened read-only; nothing in the work folder is changed.
"""

import json
import sqlite3
import sys
from pathlib import Path


def connect(work: str) -> sqlite3.Connection:
    db = Path(work) / "msock.db"
    if not db.exists():
        sys.exit(f"no msock.db in {work}")
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def table(rows, cols=None, width=60):
    rows = list(rows)
    if not rows:
        print("  (none)")
        return
    cols = cols or rows[0].keys()
    cell = lambda v: ("" if v is None else str(v)).replace("\n", " ")[:width]
    w = {k: max(len(k), *(len(cell(r[k])) for r in rows)) for k in cols}
    print("  " + "  ".join(k.ljust(w[k]) for k in cols))
    for r in rows:
        print("  " + "  ".join(cell(r[k]).ljust(w[k]) for k in cols))


def summary(c):
    print("RUNS")
    table(c.execute("select run_id, recipe_version, cause, started_at, ended_at from runs order by started_at"))
    print("\nLANES")
    table(c.execute("select run_id, application, status, stop_reason from lanes"))
    print("\nJOBS BY STAGE AND STATUS")
    table(c.execute("select stage, status, count(*) jobs, count(distinct part_id) parts from jobs "
                    "group by stage, status order by stage, status"))
    print("\nERRORS BY STAGE")
    table(c.execute("select stage, error_code, count(*) jobs from jobs where error_code is not null "
                    "group by stage, error_code order by stage, jobs desc"))
    print("\nRECORDS WRITTEN BY STAGE")
    table(c.execute("select stage, state, count(*) records from records group by stage, state order by stage"))
    print("\nAI CALLS BY STAGE")
    table(c.execute("select stage, status, count(*) calls, sum(tokens_in) tokens_in, sum(tokens_out) tokens_out, "
                    "sum(reused) reused from ai_calls group by stage, status order by stage"))
    print("\nREVIEW STEPS")
    table(c.execute("select stage, step, part_id, status, shown from review_steps order by stage, step"))


def jobs(c, stage=None, status=None):
    q, args = "select job_key, stage, job_type, part_id, part_version, unit_key, status, attempts, error_code, " \
              "lane from jobs where 1=1", []
    if stage:
        q, args = q + " and stage like ?", [*args, f"{stage}%"]
    if status:
        q, args = q + " and status = ?", [*args, status]
    table(c.execute(q + " order by stage, part_id, unit_key", args), width=48)


def job(c, prefix):
    rows = c.execute("select * from jobs where job_key like ?", [f"{prefix}%"]).fetchall()
    if len(rows) != 1:
        sys.exit(f"{len(rows)} jobs match {prefix!r}; give more of the key")
    j = rows[0]
    key = j["job_key"]
    print("JOB")
    for k in j.keys():
        v = j[k]
        if k == "spec" and v:
            try:
                v = json.dumps(json.loads(v), indent=2)
            except ValueError:
                pass
        print(f"  {k}: {v}")
    print("\nATTEMPTS")
    table(c.execute("select n, worker, started_at, ended_at, stop_reason, failure_class, tokens_in, tokens_out "
                    "from attempts where job_key = ? order by n", [key]))
    print("\nRUN EVENTS")
    table(c.execute("select seq, event, detail, at from run_events where job_key = ? order by seq", [key]), width=90)
    print("\nAI CALLS")
    table(c.execute("select model, template, status, tokens_in, tokens_out, reused, response_ms from ai_calls "
                    "where job_key = ?", [key]))
    print("\nRECORDS IT WROTE")
    table(c.execute("select record_id, type, kind, state, trust_level, layer from records where job_key = ?", [key]))
    print("\nPARKED")
    table(c.execute("select failure_class, reason, parked_at from dead_letter where job_key = ?", [key]), width=90)


def snapshot(c, pattern=None):
    q, args = "select path, size, lines, quarantined, data_class, code_page from snapshot_files", []
    if pattern:
        q, args = q + " where path like ?", [f"%{pattern}%"]
    table(c.execute(q + " order by path", args), width=80)
    print("\nQUARANTINED OR CLASSED")
    table(c.execute("select data_class, quarantined, count(*) files from snapshot_files group by 1, 2"))


def records(c, stage=None):
    q, args = "select stage, type, state, trust_level, count(*) n from records", []
    if stage:
        q, args = q + " where stage like ?", [f"{stage}%"]
    table(c.execute(q + " group by 1, 2, 3, 4 order by 1, n desc", args))


def graph(c):
    head = c.execute("select list_id, nodes, links, known_unknowns, created_at from builds "
                     "order by created_at desc limit 1").fetchone()
    if head is None:
        print("  no build yet (stage A not reached)")
        return
    table([head])
    lid = head["list_id"]
    print("\nNODES BY KIND")
    table(c.execute("select kind, home_dimension, count(*) n from graph_nodes where list_id = ? "
                    "group by 1, 2 order by n desc", [lid]))
    print("\nLINKS BY RELATION")
    table(c.execute("select relation, count(*) n from graph_links where list_id = ? group by 1 order by n desc", [lid]))
    print("\nKNOWN UNKNOWNS")
    table(c.execute("select scope, count(*) n from graph_unknowns where list_id = ? group by 1", [lid]))


def events(c, n=40):
    rows = c.execute("select seq, run_id, job_key, event, detail, at from run_events order by seq desc limit ?",
                     [int(n)]).fetchall()
    table(reversed(rows), width=70)


def held(c):
    print("PARKED JOBS")
    table(c.execute("select d.job_key, j.stage, j.part_id, d.failure_class, d.reason from dead_letter d "
                    "left join jobs j using (job_key)"), width=70)
    print("\nOPERATOR QUEUE")
    table(c.execute("select item_id, job_key, failure_class, status, reason from operator_queue"), width=70)
    print("\nREVIEW ITEMS")
    table(c.execute("select stage, kind, code, status, count(*) n from review_items group by 1, 2, 3, 4"))


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    c, cmd, rest = connect(argv[1]), argv[2], argv[3:]
    views = {"summary": summary, "jobs": jobs, "job": job, "snapshot": snapshot, "records": records,
             "graph": graph, "events": events, "held": held}
    if cmd not in views:
        sys.exit(__doc__)
    views[cmd](c, *rest)


if __name__ == "__main__":
    main(sys.argv)
