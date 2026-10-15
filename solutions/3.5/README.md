# 3.5 Working ETL Pipeline — Teacher Notes

> Exercise status: 🚧 DRAFT — gotchas below are preliminary and will be expanded during verification testing.

## Solutions

### Completed DAG

Full file in [etl_pipeline.py](etl_pipeline.py). Key pieces students must write:

**Transform** — keep six columns, drop rows with no country code:

```python
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
```

**Load** — idempotent via `replace=True` (MySQL `REPLACE INTO` keyed on the `alpha3` primary key):

```python
hook.insert_rows(
    table="country_codes",
    rows=[tuple(r.values()) for r in rows],
    target_fields=list(rows[0].keys()),
    replace=True,
)
return len(rows)
```

### Airflow values TODO

```yaml
dags:
  gitSync:
    enabled: true
    repo: https://github.com/<student-user>/<student-repo>.git   # their public assignment repo
    branch: main
    subPath: dags
    period: 60s
```

### Setup transcript

```bash
gsutil cp data/country-codes-sample.csv gs://<project-id>-<ns>-etl/
kubectl create secret generic airflow-webserver-secret -n <ns> \
  --from-literal=webserver-secret-key=$(openssl rand -hex 16)
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow -n <ns> -f helm/airflow-values.yaml
kubectl port-forward svc/airflow-api-server 8080:8080 -n <ns>
# UI: Admin > Connections > add "stedi_mysql"
#   conn type: MySQL, host: mysql-0.mysql.<ns>.svc.cluster.local,
#   schema: stedi, login: root, password: <mysql-secrets value>, port: 3306
# Unpause stedi_etl_pipeline, trigger, verify:
kubectl exec -it mysql-0 -n <ns> -- mysql -u root -p \
  -e "SELECT COUNT(*) FROM stedi.country_codes;"   # 22 (the Atlantis row, which has no alpha3 code, is dropped from 23)
```

## Gotchas

- **The chart installs Airflow 2 unless the chart version is current.** Symptom: UI shows 2.x. Fix: `helm repo update` and pin a chart version that ships Airflow 3; verify with `helm search repo apache-airflow`.
- **gitSync can only read public repos without extra setup.** Symptom: dag-processor logs `authentication required`. Fix: make the assignment repo public, or create a gitSync credentials secret — public is simpler for class.
- **DAG never appears in the UI.** Usual causes: wrong `subPath`, DAG file has a syntax error (check the dag-processor pod logs), or students pushed to a branch other than `main`.
- **`extraPipPackages` forces a pod rebuild on every sync** and slows startup; if install times out, raise the webserver/scheduler startup probe timeouts.
- **Airflow 3 renamed the webserver service** (`airflow-api-server` rather than `airflow-webserver`); the port-forward command in the assignment matches 3.x — students on chart 2.x will hit "service not found" (chart key renames strike again).
- **MySQL connection test button may be disabled** in newer Airflow; trigger the DAG and read task logs instead of relying on "Test connection."
- **The intentional invalid row is "Atlantis"** (empty `ISO3166-1-Alpha-3`). The Kosovo row has an empty FIFA code but a valid alpha3 — students filtering on the wrong column will drop Kosovo instead and end up with the wrong row count.
