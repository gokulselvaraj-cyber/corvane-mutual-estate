"""Loads CORV.PRM.BILLING.DAILY (from JCL PRMNIGHT) into the warehouse.

Lineage (journey J3): PRMBILL -> CORV.PRM.BILLING.DAILY -> SFTP /landing/billing -> load_billing_file
-> dw.premium_billing_stage -> dw.fn_merge_billing() -> dw.premium_billing -> dw.v_premium_by_line
"""
import argparse
import configparser
import logging
import os
import pathlib
import shutil

from .billrec import RECORD_LENGTH, parse

log = logging.getLogger("corvane_loader.billing")

INSERT_STAGE = """INSERT INTO dw.premium_billing_stage
 (load_id, policy_no, line_code, bill_date, premium_amt, ipt_amt, currency, region)
 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""


def read_config(path: str = "loader.ini") -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path)
    return cfg


def load_billing_file(path: str, dsn: str, dry_run: bool = False) -> int:
    """Parse every 64-byte record, stage it, then merge into dw.premium_billing. Returns rows loaded."""
    records = []
    with open(path, encoding="ascii") as fh:
        for n, line in enumerate(fh, start=1):
            if len(line.rstrip("\r\n")) not in (RECORD_LENGTH, RECORD_LENGTH - 16):
                raise ValueError(f"{path}:{n}: record length {len(line.rstrip())} is not {RECORD_LENGTH}")
            records.append(parse(line))
    log.info("parsed %d billing records from %s", len(records), path)
    if dry_run:
        return len(records)

    import psycopg
    with psycopg.connect(dsn) as conn:
        load_id = conn.execute(
            "INSERT INTO dw.billing_load (file_name, record_count, started_at) VALUES (%s, %s, now()) RETURNING load_id",
            (os.path.basename(path), len(records))).fetchone()[0]
        with conn.cursor() as cur:
            cur.executemany(INSERT_STAGE, [(load_id, r.policy_no, r.line_code, r.bill_date, r.premium_amt,
                                            r.ipt_amt, r.currency, r.region) for r in records])
        merged = conn.execute("SELECT dw.fn_merge_billing(%s)", (load_id,)).fetchone()[0]
        conn.execute("UPDATE dw.billing_load SET merged_count = %s, finished_at = now() WHERE load_id = %s",
                     (merged, load_id))
    return len(records)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    cfg = read_config()
    landing = pathlib.Path(cfg["landing"]["billing_dir"])
    files = [pathlib.Path(args.file)] if args.file else sorted(landing.glob(cfg["landing"]["file_pattern"]))
    for f in files:
        load_billing_file(str(f), cfg["warehouse"]["dsn"], dry_run=args.dry_run)
        if not args.dry_run:
            shutil.move(str(f), cfg["landing"]["archive_dir"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
