"""Completed solution for starter/dags/etl_pipeline.py (both TODOs solved)."""

from datetime import datetime

from airflow.decorators import dag, task

GCS_BUCKET = "<project-id>-<your-namespace>-etl"
GCS_OBJECT = "country-codes-sample.csv"
MYSQL_CONN_ID = "stedi_mysql"


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
        import csv
        import io

        from airflow.providers.google.cloud.hooks.gcs import GCSHook

        data = GCSHook().download(bucket_name=GCS_BUCKET, object_name=GCS_OBJECT)
        reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
        return list(reader)

    @task
    def transform(rows: list[dict]) -> list[dict]:
        # Solution: keep the six report columns, drop rows missing a country code
        return [
            {
                "alpha3": row["ISO3166-1-Alpha-3"],
                "country_name": row["official_name_en"],
                "capital": row["Capital"],
                "continent": row["Continent"],
                "currency_name": row["currency_name"],
                "internet_tld": row["TLD"],
            }
            for row in rows
            if row.get("ISO3166-1-Alpha-3")
        ]

    @task
    def load(rows: list[dict]) -> int:
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
        # Solution: REPLACE keyed on the alpha3 primary key keeps reruns idempotent
        hook.insert_rows(
            table="country_codes",
            rows=[tuple(r.values()) for r in rows],
            target_fields=list(rows[0].keys()),
            replace=True,
        )
        return len(rows)

    load(transform(extract()))


stedi_etl_pipeline()
