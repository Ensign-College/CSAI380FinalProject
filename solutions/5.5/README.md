# 5.5 Scaling and Downstream Integration — Teacher Notes

> Exercise status: 🚧 DRAFT — gotchas below are preliminary and will be expanded during verification testing.

## Solutions

### Consumer TODO — idempotent insert

Completed script in [mysql_sink_consumer.py](mysql_sink_consumer.py); the solved loop body:

```python
for message in consumer:
    event_key = f"{message.partition}-{message.offset}"
    cursor.execute(
        """
        INSERT INTO risk_events (event_key, payload, kafka_partition, kafka_offset)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE payload = VALUES(payload)
        """,
        (event_key, json.dumps(message.value), message.partition, message.offset),
    )
    db.commit()
    print(f"stored {event_key}", flush=True)
```

Partition + offset uniquely identify a Kafka message within a topic, so the upsert absorbs at-least-once redelivery without duplicate rows.

### Command transcript

```bash
kubectl create configmap mysql-sink-script -n <ns> --from-file=app/mysql_sink_consumer.py
kubectl apply -f k8s/kafka/mysql-sink-consumer.yaml -n <ns>

# near-real-time check (simulation running)
kubectl exec -it mysql-0 -n <ns> -- mysql -u root -p \
  -e "SELECT COUNT(*) FROM stedi.risk_events;"   # run twice, count climbs

# integrity
SELECT event_key, COUNT(*) FROM risk_events GROUP BY event_key HAVING COUNT(*) > 1;  -- 0 rows

# lag monitoring (from kafka-client pod)
kafka-consumer-groups.sh --describe --group mysql-sink \
  --bootstrap-server kafka.<ns>.svc.cluster.local:9092

# scaling experiment
kubectl scale deployment mysql-sink-consumer -n <ns> --replicas=0   # lag builds
kubectl scale deployment mysql-sink-consumer -n <ns> --replicas=3   # lag drains
```

### Partition reasoning answer key

The topic was created with one partition, so only one consumer in the `mysql-sink` group can own it — replicas 2 and 3 join the group and sit idle. To let them help: recreate (or alter) the topic with ≥3 partitions; Kafka then assigns one partition per consumer and throughput scales. This is the week's core lesson — scaling consumers without scaling partitions magnifies nothing.

## Gotchas

- **`pip install` at container start takes ~1 min per replica** and needs egress; if the cluster blocks internet egress, pre-build an image instead.
- **kafka-python vs Python 3.12**: if `KafkaConsumer` import fails with `ModuleNotFoundError: kafka.vendor`, pin `kafka-python-ng` instead — kafka-python releases have lagged newer Pythons.
- **Lag shows `-` while consumers rebalance**; wait for the group to stabilize before recording baseline numbers.
- **Scaling to 0 mid-poll logs a flood of CommitFailedError** on restart — harmless, but tell students to expect it.
- **Counts that never climb** usually mean the simulation from 4.5 stopped (`GET /simulation` to check) rather than a consumer bug.
- **`kafka-consumer-groups.sh --describe` returns nothing** until the consumer has committed at least once; produce a few events first.
