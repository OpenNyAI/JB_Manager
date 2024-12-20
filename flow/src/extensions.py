import os
import logging
from lib.kafka_utils import KafkaProducer, KafkaConsumer
from lib.data_models import Channel, Language, RAG, Flow, Logger

logging.basicConfig()
logger = logging.getLogger("flow")
logger.setLevel(logging.INFO)


logger.info("Starting Listening")

flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
if not flow_topic:
    raise ValueError("KAFKA_FLOW_TOPIC is not set")
retriever_topic = os.getenv("KAFKA_RETRIEVER_TOPIC")
if not retriever_topic:
    raise ValueError("KAFKA_RETRIEVER_TOPIC is not set")
language_topic = os.getenv("KAFKA_LANGUAGE_TOPIC")
if not language_topic:
    raise ValueError("KAFKA_LANGUAGE_TOPIC is not set")
channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")
if not channel_topic:
    raise ValueError("KAFKA_CHANNEL_TOPIC is not set")
logger_topic = os.getenv("KAFKA_LOGGER_TOPIC")
if not logger_topic:
    raise ValueError("KAFKA_LOGGER_TOPIC is not set")

logger.info("Connecting to topic %s", flow_topic)

consumer = KafkaConsumer.from_env_vars(
    group_id="cooler_group_id", auto_offset_reset="latest"
)
logger.info("Connecting to topic %s", language_topic)
logger.info("Connecting to topic %s", retriever_topic)
logger.info("Connecting to topic %s", channel_topic)
logger.info("Connecting to topic %s", logger_topic)
producer = KafkaProducer.from_env_vars()

logger.info("Connected to Kafka Topics")


def produce_message(message: Channel | Language | RAG | Flow| Logger):
    if isinstance(message, Channel):
        topic = channel_topic
    elif isinstance(message, Language):
        topic = language_topic
    elif isinstance(message, RAG):
        topic = retriever_topic
    elif isinstance(message, Flow):
        topic = flow_topic
    elif isinstance(message, Logger):
        topic = logger_topic
    else:
        raise ValueError("Invalid message type")

    logger.info("Sending msg to %s topic: %s", topic, message)
    producer.send_message(topic=topic, value=message.model_dump_json(exclude_none=True))
