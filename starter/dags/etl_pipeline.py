"""ETL DAG for CSAI 380 — 3.5 Working ETL Pipeline.

Extracts a country-codes CSV from a GCS bucket, transforms it, and loads the
result into the MySQL operational data store deployed in week 2.
"""

from datetime import datetime

from airflow.decorators import dag, task

GCS_BUCKET = "<project-id>-<your-namespace>-etl"   # Terraform output: etl_bucket
GCS_OBJECT = "country-codes-sample.csv"
MYSQL_CONN_ID = "stedi_mysql"                      # define in Airflow UI: Admin > Connections


@dag(
    dag_id="stedi_etl_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["csai380"],
)
def stedi_etl_pipeline():
    @task
    def extract() -> list[dict]:
        """Download the CSV from GCS and parse it into rows."""
        import csv
        import io

        from airflow.providers.google.cloud.hooks.gcs import GCSHook

        data = GCSHook().download(bucket_name=GCS_BUCKET, object_name=GCS_OBJECT)
        reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
        return list(reader)

    @task
    def transform(rows: list[dict]) -> list[dict]:
        # TODO(student): keep only the columns needed for the signup-location
        # report (ISO3166-1-Alpha-3, official English name, capital, continent,
        # currency name, internet TLD) and drop rows missing a country code.
        raise NotImplementedError("implement the transform step")

    @task
    def load(rows: list[dict]) -> int:
        """Insert transformed rows into MySQL."""
        from airflow.providers.mysql.hooks.mysql import MySqlHook

        hook = MySqlHook(mysql_conn_id=MYSQL_CONN_ID)
        hook.run(
            """
            CREATE TABLE IF NOT EXISTS country_codes (
                alpha3 CHAR(3) PRIMARY KEY,
                country_name VARCHAR(255),
                capital VARCHAR(255),
                continent VARCHAR(64),
                currency_name VARCHAR(128),
                internet_tld VARCHAR(16)
            )
            """
        )
        # TODO(student): insert the rows (hint: hook.insert_rows with
        # replace=True keeps the pipeline idempotent across reruns).
        raise NotImplementedError("implement the load step")

    load(transform(extract()))


stedi_etl_pipeline()
