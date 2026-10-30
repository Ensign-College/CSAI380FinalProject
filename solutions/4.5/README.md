# 4.5 Streaming or Micro-batches — Teacher Notes

> Exercise status: ✅ VERIFIED 2026-10-30 against a temporary GKE Autopilot cluster in us-east1 (instructor test project, namespace verify15-stedi): starter Kafka values, `customer-risk` round trip, STEDI patch, `POST /simulation` → live risk events on the topic and in the logging consumer (123 events in ~4 minutes).

## Solutions

### Patch TODO — `KAFKA_STEDI_EVENTS_TOPIC`

Completed patch in [stedi-kafka-patch.yaml](stedi-kafka-patch.yaml); the added variable:

```yaml
            - name: KAFKA_STEDI_EVENTS_TOPIC
              value: "customer-risk"
```

`KAFKA_STEDI_EVENTS_TOPIC` (added to stedi-web 2026-10-29, default `stedi-events`) is the topic STEDI publishes risk events to. `KAFKA_RISK_TOPIC` is the topic STEDI *consumes*, so setting it alone sends nothing to `customer-risk`. `KafkaProducerUtil` reads `KAFKA_BROKER` from the environment.

### Command transcript

```bash
helm upgrade --install kafka oci://registry-1.docker.io/bitnamicharts/kafka \
  -n <ns> -f helm/kafka-values.yaml

kubectl apply -f k8s/kafka/kafka-client.yaml -n <ns>
kubectl exec -it kafka-client -n <ns> -- bash

# inside the pod
kafka-topics.sh --create --topic customer-risk --partitions 1 --replication-factor 1 \
  --bootstrap-server kafka.<ns>.svc.cluster.local:9092
kafka-console-producer.sh --topic customer-risk \
  --bootstrap-server kafka.<ns>.svc.cluster.local:9092
# second terminal
kafka-console-consumer.sh --topic customer-risk --from-beginning \
  --bootstrap-server kafka.<ns>.svc.cluster.local:9092

# connect STEDI and start the simulation
kubectl patch deployment stedi -n <ns> --patch-file k8s/kafka/stedi-kafka-patch.yaml
kubectl port-forward svc/stedi 8080:80 -n <ns>
curl -X POST http://localhost:8080/simulation    # start (GET checks, DELETE stops)

kubectl apply -f k8s/kafka/logging-consumer.yaml -n <ns>
kubectl logs -f deployment/risk-logging-consumer -n <ns>
```

### Processing-model answer key

STEDI risk events are **streaming**: events are produced continuously as users complete step tests and consumed within seconds, one event at a time, with no accumulation window. Batch would fit a nightly re-score of all historical customers; micro-batch would fit aggregating risk scores every few minutes for a dashboard where second-level latency is unnecessary.

## Gotchas

- **Kafka install hangs; `kafka-controller-0` stuck `Init:ImagePullBackOff` (found 2026-10-30).** `docker.io/bitnami/kafka:4.0.0-debian-12-r10` returns NotFound: Bitnami removed its legacy tags from Docker Hub in 2025, and `bitnami/kafka:3.9` (client and logging-consumer pods) is gone too. The starter values now pull `bitnamilegacy/kafka` with `global.security.allowInsecureImages: true` and set replication factor 1 for internal topics, matching the verified 4.4 values; the client and consumer use `bitnamilegacy/kafka:4.0.0-debian-12-r10`. A failed release must be removed first: `helm uninstall kafka -n <ns>` and delete its PVC.

- **Bitnami chart renamed broker values to `controller.*`** in the KRaft era; older tutorials that set `replicaCount` at the top level silently deploy defaults (chart key renames).
- **Consumer says `LEADER_NOT_AVAILABLE` right after install** — Kafka takes a minute to elect; retry rather than reinstalling.
- **Patch replaces the whole env list?** No — a strategic-merge patch on a named container merges env entries, but if students hand-edit and re-apply the full deployment they may clobber week-2 Redis env vars. Check `kubectl get deploy stedi -o yaml` after patching.
- **Events go to `stedi-events`, not `customer-risk`.** STEDI log says `Sending to Kafka Topic: stedi-events`: the patch set `KAFKA_RISK_TOPIC` (consume side) instead of `KAFKA_STEDI_EVENTS_TOPIC`, or the image predates October 2026. Fix the variable or rebuild from current stedi-web.
- **Scoring fails with `ERR unknown command 'JSON.GET'`, no events sent.** `redis-stedi` still runs `redis:7`; change it to `redis:8` (current 2.5 starter) and re-apply.
- **`POST /simulation` returns 403, or the timer page toggle flips back off** ("Simulation mode is disabled on this server"). The patch's `ENABLE_SIMULATION_MODE=true` is missing or wasn't applied; check `kubectl get deploy stedi -o yaml | grep -A1 ENABLE_SIMULATION_MODE`.
- **Toggle off but `GET /simulation` still `true`.** Stopping waits for the current pass through the customers (up to about a minute); the switch updates before the server does.
- **Simulation produces nothing** if STEDI cannot reach Redis — the simulation creates users/sessions through the same code paths; verify week-2 services are still healthy first.
- **DNS name differs if the Helm release isn't `kafka`** — service is `<release>.<ns>.svc.cluster.local`; students who ran `helm install my-kafka ...` must adjust every bootstrap-server string.
- **`--from-beginning` floods with old dummy events** during the STEDI demo; drop the flag when capturing "live" evidence.
