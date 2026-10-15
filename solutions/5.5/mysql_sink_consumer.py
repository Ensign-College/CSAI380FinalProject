"""Completed solution for starter/app/mysql_sink_consumer.py (TODO solved)."""

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
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]

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
        # Solution: partition+offset uniquely identify the message; the upsert
        # keeps redelivered messages from creating duplicate rows.
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


if __name__ == "__main__":
    main()
