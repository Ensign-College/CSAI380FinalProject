# 2.5 Saving the Data — Teacher Notes

> Exercise status: 🚧 DRAFT — Redis image changed 2026-10-29 to `redis:8`; needs a GKE run. Previously: ✅ VERIFIED 2026-10-15 against a GKE Autopilot cluster (us-central1) in an instructor test project (namespace verify-stedi).

## Solutions

### Redis TODO — volumeClaimTemplates

Completed StatefulSet in [redis-statefulset.yaml](redis-statefulset.yaml); the added section:

```yaml
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

### MySQL TODO — storage size

`storage: 10Gi` (see [mysql-statefulset.yaml](mysql-statefulset.yaml)). Justification students should give: the class dataset is tiny, but MySQL needs headroom for binlogs/redo logs, and GKE standard PD storage is billed per GB so 10Gi is a cheap, safe floor.

### Secret creation (never committed)

```bash
kubectl create secret generic redis-secrets -n <ns> --from-literal=REDIS_PASS='<password>'
kubectl create secret generic mysql-secrets -n <ns> --from-literal=MYSQL_ROOT_PASSWORD='<password>'
```

### Persistence test transcript

```bash
kubectl exec -it mysql-0 -n <ns> -- mysql -u root -p
mysql> USE stedi;
mysql> CREATE TABLE persistence_test (id INT PRIMARY KEY, note VARCHAR(64));
mysql> INSERT INTO persistence_test VALUES (1, 'survives pod replacement');
kubectl delete pod mysql-0 -n <ns>
kubectl wait --for=condition=Ready pod/mysql-0 -n <ns> --timeout=180s
kubectl exec -it mysql-0 -n <ns> -- mysql -u root -p -e "SELECT * FROM stedi.persistence_test;"

kubectl exec -it redis-stedi-0 -n <ns> -- redis-cli -a '<password>' SET testkey hello
kubectl delete pod redis-stedi-0 -n <ns>
kubectl exec -it redis-stedi-0 -n <ns> -- redis-cli -a '<password>' GET testkey   # "hello"
```

### Workbench connection

```bash
kubectl get service mysql-public-dev -n <ns>   # wait for EXTERNAL-IP
# Workbench: host=<EXTERNAL-IP>, port=3306, user=root, password=<mysql-secrets value>
kubectl delete -f k8s/stateful/mysql-loadbalancer-dev.yaml -n <ns>   # cleanup!
```

## Gotchas

- **STEDI step tests fail with `ERR unknown command 'JSON.GET'`.** STEDI stores and scores balance tests with RedisJSON, which `redis:7` lacks. The starter moved to `redis:8` on 2026-10-29. Students on `redis:7` change the image and re-apply; the existing volume upgrades in place (tested locally: a Redis 7 AOF volume opened in Redis 8 with data intact).

- **PVC stuck `Pending`.** Symptom: pod `Pending`, PVC event `waiting for first consumer` or no default StorageClass. Fix: GKE's `standard-rwo` is default; if the cluster was customized, add `storageClassName: standard-rwo` to the claim.
- **Redis AOF + no PVC = silent data loss.** If students skip the volumeClaimTemplates TODO, Redis still starts and the test key vanishes after delete — that is the intended lesson, but check they noticed.
- **MySQL pod OOMKilled on startup.** Symptom: restart with reason `OOMKilled`. Fix: `mysql:8.4` needs ~512Mi; don't let students lower the request below that.
- **LoadBalancer takes several minutes.** `EXTERNAL-IP <pending>` is normal for 2–5 min; students often assume failure and re-apply.
- **Deleting the StatefulSet does not delete PVCs.** Useful for recovery demos, but students re-testing from scratch must `kubectl delete pvc` explicitly or old passwords/data linger.
- **Workbench 8.x may reject the connection with caching_sha2_password errors** on older Workbench versions; upgrading Workbench is simpler than changing the MySQL auth plugin.
- **`kubectl wait` races the StatefulSet controller (hit during verification).** Right after `kubectl delete pod mysql-0`, `kubectl wait` can fail with `pods "mysql-0" not found` because the replacement pod hasn't been created yet. Fix: `sleep 10-15` (or retry the wait) before waiting on readiness.
- **MySQL needs ~20s after Ready before accepting connections** — an immediate `kubectl exec ... mysql` after the pod goes Ready can get `ERROR 2013 Lost connection`; retry briefly.
