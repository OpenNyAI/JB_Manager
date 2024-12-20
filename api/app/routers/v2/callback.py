from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Request
from lib.channel_handler import ChannelHandler, channel_map
from ...handlers.v2.callback import handle_callback
from ...extensions import produce_message

logger = logging.getLogger("jb-manager-api")
router = APIRouter(
    prefix="/callback",
)


@router.post("/{provider}/{bot_identifier}")
async def callback(provider: str, bot_identifier: str, request: Request):
    data = await request.json()
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    chosen_channel: Optional[type[ChannelHandler]] = None
    for channel in channel_map.values():
        if provider == channel.get_channel_name() and channel.is_valid_data(data):
            chosen_channel = channel
            break
    if chosen_channel is None:
        logger.error("No valid channel found")
        return 404

    async for err, channel_input, api_logger_input in handle_callback(
        bot_identifier=bot_identifier,
        callback_data=data,
        headers=headers,
        query_params=query_params,
        chosen_channel=chosen_channel,
    ):
        if err:
            produce_message(api_logger_input)
            raise HTTPException(status_code=400, detail=str(err))
        elif channel_input:
            produce_message(channel_input)
        produce_message(api_logger_input)
    return 200
