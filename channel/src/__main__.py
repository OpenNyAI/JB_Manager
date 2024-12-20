import asyncio
import json
import os
import logging
import traceback
from dotenv import load_dotenv

from lib.data_models import (
    Channel,
    ChannelIntent,
    Flow,
    Language,
)
from lib.kafka import KafkaHandler
from .handlers import process_incoming_messages, send_message_to_user

load_dotenv()

logging.basicConfig()
logger = logging.getLogger("channel")
logger.setLevel(logging.INFO)

channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")
if not channel_topic:
    raise ValueError("KAFKA_CHANNEL_TOPIC is not set in the environment")
language_topic = os.getenv("KAFKA_LANGUAGE_TOPIC")
if not language_topic:
    raise ValueError("KAFKA_LANGUAGE_TOPIC is not set in the environment")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
if not flow_topic:
    raise ValueError("KAFKA_FLOW_TOPIC is not set in the environment")
logger_topic = os.getenv("KAFKA_LOGGER_TOPIC")
if not logger_topic:
    raise ValueError("KAFKA_LOGGER_TOPIC is not set in the environment")

logger.info("Channel Topic: %s", channel_topic)
logger.info("Language Topic: %s", language_topic)
logger.info("Flow Topic: %s", flow_topic)
logger.info("Logger Topic: %s", logger_topic)

consumer = KafkaHandler.get_consumer()
producer = KafkaHandler.get_producer()


async def start_channel():
    """Starts the channel server"""
    logger.info("Starting Listening")
    while True:
        try:
            msg = consumer.receive_message(channel_topic)
            msg = json.loads(msg)
            logger.info("Input received: %s", msg)
            input_data = Channel(**msg)
            logger.info(
                "Input received in object form: %s",
                input_data.model_dump(exclude_none=True),
            )
            if input_data.intent == ChannelIntent.CHANNEL_IN:
                incoming_message, channel_logger_input = await process_incoming_messages(
                    turn_id=input_data.turn_id, bot_input=input_data.bot_input
                )
                if isinstance(incoming_message, Flow):
                    logger.info("Sending to flow")
                    producer.send_message(
                        flow_topic, incoming_message.model_dump_json(exclude_none=True)
                    )
                elif isinstance(incoming_message, Language):
                    logger.info("Sending to language")
                    producer.send_message(
                        language_topic,
                        incoming_message.model_dump_json(exclude_none=True),
                    )
            elif input_data.intent == ChannelIntent.CHANNEL_OUT:
                channel_logger_input = await send_message_to_user(
                    turn_id=input_data.turn_id, message=input_data.bot_output
                )
            producer.send_message(
                        logger_topic,
                        channel_logger_input.model_dump_json(exclude_none=True),
                    )
        except Exception as e:
            logger.error("Error %s", e)
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(start_channel())
