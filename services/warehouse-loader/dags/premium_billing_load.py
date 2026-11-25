"""Airflow DAG: loads the nightly premium billing file produced by mainframe JCL PRMNIGHT.

PRMNIGHT runs 01:30 Europe/London Mon-Sat and its STEP040 drops the file in /landing/billing.
This DAG starts at 04:00 and waits up to 2 hours for the file before failing (alert: BillingFileLate).
"""
from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor

LONDON = pendulum.timezone("Europe/London")

with DAG(
    dag_id="premium_billing_load",
    schedule="0 4 * * 1-6",
    start_date=datetime(2026, 1, 5, tzinfo=LONDON),
    catchup=False,
    default_args={"owner": "team-data-platform", "retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["billing", "mainframe", "J3"],
) as dag:
    wait_for_file = FileSensor(
        task_id="wait_for_billing_file",
        filepath="/landing/billing/CORV.PRM.BILLING.DAILY.D{{ ds_nodash }}.txt",
        poke_interval=300,
        timeout=7200,
        mode="reschedule",
    )
    load = BashOperator(
        task_id="load_billing_file",
        bash_command="python -m corvane_loader.billing --file /landing/billing/CORV.PRM.BILLING.DAILY.D{{ ds_nodash }}.txt",
    )
    refresh_view = BashOperator(
        task_id="refresh_premium_by_line",
        bash_command="psql \"$WAREHOUSE_DSN\" -c 'REFRESH MATERIALIZED VIEW CONCURRENTLY dw.mv_premium_by_line_month'",
    )
    wait_for_file >> load >> refresh_view
