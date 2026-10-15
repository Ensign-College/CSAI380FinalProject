"""Kafka → MySQL sink consumer — week 5 (5.5 Scaling and Downstream Integration).

Reads STEDI risk events from the Kafka topic and inserts them into MySQL.
Runs inside the cluster; see starter/k8s/kafka/mysql-sink-consumer.yaml.
"""

import json
import os

from kafka import KafkaConsumer
import mysql.connector

KAFKA_BROKER = os.environ["KAFKA_BROKER"]
KAFKA_TOPIC = os.environ["KAFKA_TOPIC"]
CONSUMER_GROUP = os.environ.get("CONSUMER_GROUP", "mysql-sink")

MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "stedi")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]  # injected via secretKeyRef

DDL = """
CREATE TABLE IF NOT EXISTS risk_events (
    event_key VARCHAR(128) PRIMARY KEY,
    payload JSON,
    kafka_partition INT,
    kafka_offset BIGINT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def main() -> None:
    db = mysql.connector.connect(
        host=MYSQL_HOST, database=MYSQL_DATABASE, user=MYSQL_USER, password=MYSQL_PASSWORD
    )
    cursor = db.cursor()
    cursor.execute(DDL)
    db.commit()

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: v.decode("utf-8"),
    )
    print(f"consuming {KAFKA_TOPIC} from {KAFKA_BROKER} as group {CONSUMER_GROUP}", flush=True)

    for message in consumer:
        # TODO(student): build a unique event_key from the message (hint:
        # partition and offset uniquely identify a Kafka message) and INSERT
        # the row. Use INSERT ... ON DUPLICATE KEY UPDATE (an "upsert") so a
        # replayed message never creates a duplicate row.
        raise NotImplementedError("implement the insert")


if __name__ == "__main__":
    main()
