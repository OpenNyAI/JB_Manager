import asyncio
import json
import os
import logging
import traceback
from dotenv import load_dotenv
from lib.data_models import (
    Logger,
)
from lib.kafka import KafkaHandler
from .handlers import logging_data_into_db

load_dotenv()

logging.basicConfig()
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

logger_topic = os.getenv("KAFKA_LOGGER_TOPIC")
if not logger_topic:
    raise ValueError("KAFKA_LOGGER_TOPIC is not set in the environment")
logger.info("Logger Topic: %s", logger_topic)

consumer = KafkaHandler.get_consumer()
producer = KafkaHandler.get_producer()


async def start_logger():
    """Starts the logger server"""
    logger.info("Starting Listening")
    while True:
        try:
            msg = consumer.receive_message(logger_topic)
            msg = json.loads(msg)
            service_name = msg.get("source")
            logger.info("Input received: %s", msg)
            input_data = Logger(**msg)
            logger.info(
                "Input received in object form: %s",
                input_data.model_dump(exclude_none=True),
            )
            await logging_data_into_db(service_name=service_name,input_data=input_data)
        except Exception as e:
            logger.error("Error %s", e)
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(start_logger())
