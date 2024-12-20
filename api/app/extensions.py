import os
import logging
from lib.kafka_utils import KafkaProducer, KafkaException
from lib.data_models import Flow, Channel, Indexer, Logger

logger = logging.getLogger("jb-manager-api")

channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")
if not channel_topic:
    raise ValueError("KAFKA_CHANNEL_TOPIC is not set in the environment")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
if not flow_topic:
    raise ValueError("KAFKA_FLOW_TOPIC is not set in the environment")
indexer_topic = os.getenv("KAFKA_INDEXER_TOPIC")
if not indexer_topic:
    raise ValueError("KAFKA_INDEXER_TOPIC is not set in the environment")
logger_topic = os.getenv("KAFKA_LOGGER_TOPIC")
if not logger_topic:
    raise ValueError("KAFKA_LOGGER_TOPIC is not set in the environment")
logger.info("Channel Topic: %s", channel_topic)
logger.info("Flow Topic: %s", flow_topic)
logger.info("Indexer Topic: %s", indexer_topic)
logger.info("Logger Topic: %s", logger_topic)
# Connect Kafka Producer automatically using env variables
# and SASL, if applicable
producer = KafkaProducer.from_env_vars()


def produce_message(message: Flow | Channel | Indexer | Logger):
    if isinstance(message, Flow):
        topic = flow_topic
    elif isinstance(message, Channel):
        topic = channel_topic
    elif isinstance(message, Indexer):
        topic = indexer_topic
    elif isinstance(message, Logger):
        topic = logger_topic
    else:
        raise ValueError("Invalid message type")
    try:
        logger.info("Sending msg to %s topic: %s", topic, message)
        producer.send_message(
            topic=topic, value=message.model_dump_json(exclude_none=True)
        )
    except KafkaException as e:
        return e
