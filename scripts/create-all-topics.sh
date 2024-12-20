#!/bin/bash

kafka_ready() {
    kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null 2>&1
}

# Wait for Kafka to be ready
while ! kafka_ready; do
    echo "Waiting for Kafka to be ready..."
    sleep 5
done

echo "Creating topics now"

kafka-topics.sh --create --bootstrap-server localhost:9092 --topic $KAFKA_FLOW_TOPIC --if-not-exists
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic $KAFKA_LANGUAGE_TOPIC --if-not-exists
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic $KAFKA_CHANNEL_TOPIC --if-not-exists
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic $KAFKA_RETRIEVER_TOPIC --if-not-exists
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic $KAFKA_LOGGER_TOPIC --if-not-exists
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic $KAFKA_INDEXER_TOPIC --if-not-exists

kafka-topics.sh --bootstrap-server localhost:9092 --list