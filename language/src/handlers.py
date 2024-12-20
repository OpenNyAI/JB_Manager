"""
Handlers for Language Input and Output
"""
import uuid
import time
import traceback
from typing import List
import logging
import uuid
from lib.data_models import (
    Channel,
    ChannelIntent,
    Flow,
    FlowIntent,
    UserInput,
    MessageType,
    Message,
    TextMessage,
    AudioMessage,
    DocumentMessage,
    ImageMessage,
    ButtonMessage,
    Option,
    ListMessage,
    Logger,
    LanguageLogger,
)
from lib.model import LanguageCodes
from .extension import speech_processor, storage, translator
from .audio_converter import convert_to_wav_with_ffmpeg

logger = logging.getLogger("language")
logger.setLevel(logging.INFO)

async def measure_time_async(method, *args, **kwargs): 
    conversion_start_time = time.time() 
    result = await method(*args, **kwargs) 
    conversion_end_time = time.time() 
    response_time = conversion_end_time - conversion_start_time 
    return result, response_time

async def create_language_logger_input(turn_id: str, msg_id: str, msg_state: str,msg_language: str, msg_type: str, 
                                       t_language: str, t_type: str, t_model: str, response_time: str,
                                       status: str):
    id = str(uuid.uuid4())
    language_logger_input = Logger(
        source = "language",
        logger_obj = LanguageLogger(
            id = id,
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = msg_state,
            msg_language = msg_language,
            msg_type = msg_type,
            translated_to_language = t_language,
            translation_type = t_type,
            translation_model = t_model,
            response_time = response_time,
            status = status
        )
    )
    return language_logger_input

async def handle_input(
    turn_id: str, preferred_language: LanguageCodes, message: Message
):
    """Handler for Language Input"""
    english_text = None
    language_logger_inputs = []
    
    msg_id = str(uuid.uuid4())
    if msg_id is None :
        msg_id = ""

    if message.message_type == MessageType.TEXT:
        if not message.text:
            raise ValueError("Message text is empty")
        message_text = message.text.body
        logger.info(
            "Received %s text message %s", preferred_language.name, message_text
        )
        vernacular_text = message_text

        english_text, response_time = await measure_time_async(translator.translate_text, vernacular_text, preferred_language, LanguageCodes.EN)

        text_message = TextMessage(body=english_text)
        message = Message(
            message_type=MessageType.TEXT,
            text=text_message,
        )

        if text_message is None or message is None:
            status="Message object not created"
        else:
            status="Success"
            
        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Incoming", 
            msg_language = preferred_language,
            msg_type=message.message_type.value, 
            t_language = LanguageCodes.EN.value,
            t_type="Language translation",
            t_model="Dhruva/Azure",
            response_time=str(response_time),
            status=status)
        
        language_logger_inputs.append(language_logger_object)

    elif message.message_type == MessageType.AUDIO:
        if not message.audio:
            raise ValueError("Message audio is empty")
        audio_url = message.audio.media_url
        wav_data = await convert_to_wav_with_ffmpeg(audio_url)

        if not wav_data:
            status = "Conversion to audio failed"
        else:
            status = "Success"

        vernacular_text, response_time = await measure_time_async(speech_processor.speech_to_text, wav_data, preferred_language)

        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Incoming", 
            msg_language = preferred_language,
            msg_type=message.message_type.value, 
            t_language = preferred_language,
            t_type="Speech to text",
            t_model="Dhruva/Azure",
            response_time=str(response_time),
            status=status
        )
        
        language_logger_inputs.append(language_logger_object)

        logger.info("Vernacular Text %s", vernacular_text)

        english_text, response_time = await measure_time_async(translator.translate_text, vernacular_text, preferred_language, LanguageCodes.EN)

        logger.info("English Text %s", english_text)
        text_message = TextMessage(body=english_text)
        message = Message(
            message_type=MessageType.TEXT,
            text=text_message,
        )

        if text_message is None or message is None:
            status="Message object not created"
        else:
            status="Success"

        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Intermediate", 
            msg_language = preferred_language,
            msg_type="Text", 
            t_language = LanguageCodes.EN.value,
            t_type="Language Translation",
            t_model="Dhruva/Azure",
            response_time=str(response_time),
            status=status
        )
        
        language_logger_inputs.append(language_logger_object)

    flow_input = Flow(
        source="language",
        intent=FlowIntent.USER_INPUT,
        user_input=UserInput(turn_id=turn_id, message=message),
    )
    return flow_input, language_logger_inputs


async def handle_output(
    turn_id: str, preferred_language: LanguageCodes, message: Message
):
    logger.info("Preferred Language %s", preferred_language)
    logger.info("Message %s", message)

    msg_id = str(uuid.uuid4())

    media_output_url = None
    language_logger_inputs = []
    channel_inputs = []
    message_type = message.message_type
    if message_type == MessageType.TEXT:
        if not message.text:
            raise ValueError("Message text is empty")
        
        total_response_time: float = 0
        vernacular_body, response_time = await measure_time_async(translator.translate_text, message.text.body,LanguageCodes.EN,preferred_language)
        total_response_time += response_time

        translated_text_message = TextMessage(body=vernacular_body)

        if translated_text_message is None:
            status="Translated text message not created"
        else:
            status="Success"

        if message.text.header:
            translated_text_message.header, response_time = await measure_time_async(
                translator.translate_text, 
                message.text.header,
                LanguageCodes.EN,
                preferred_language)
            
            total_response_time += response_time

        if message.text.footer:
            translated_text_message.footer, response_time = await measure_time_async(
                translator.translate_text, 
                message.text.footer,
                LanguageCodes.EN,
                preferred_language)
            
            total_response_time += response_time

        logger.info("Vernacular Text %s", vernacular_body)
        channel_inputs.append(
            Channel(
                source="language",
                intent=ChannelIntent.CHANNEL_OUT,
                turn_id=turn_id,
                bot_output=Message(
                    message_type=MessageType.TEXT, text=translated_text_message
                ),
            )
        )

        if not channel_inputs:
            status="No response created for channel"
        
        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Outgoing Text", 
            msg_language = LanguageCodes.EN.value,
            msg_type=message.message_type.value, 
            t_language = preferred_language,
            t_type="Language translation",
            t_model="Dhruva/Azure",
            response_time=str(total_response_time),
            status=status)
        
        language_logger_inputs.append(language_logger_object)

        try:
            audio_content, response_time = await measure_time_async(speech_processor.text_to_speech, vernacular_body, preferred_language)

            if not audio_content:
                status = "Conversion to audio failed"
            else:
                status = "Success"

            fid = str(uuid.uuid4())
            filename = f"{fid}.mp3"
            await storage.write_file(filename, audio_content, "audio/mpeg")
            media_output_url = await storage.public_url(filename)
            translated_audio_message = AudioMessage(media_url=media_output_url)

            if translated_audio_message is None:
                status="Translated audio message not created"
            else:
                status="Success"
        
            channel_inputs.append(
                Channel(
                    source="language",
                    intent=ChannelIntent.CHANNEL_OUT,
                    turn_id=turn_id,
                    bot_output=Message(
                        message_type=MessageType.AUDIO, audio=translated_audio_message
                    ),
                )
            )

            language_logger_object = await create_language_logger_input(
                turn_id = turn_id,
                msg_id = msg_id,
                msg_state = "Outgoing Audio", 
                msg_language = preferred_language,
                msg_type=message.message_type.value, 
                t_language = preferred_language,
                t_type="Speech",
                t_model="Dhruva/Azure",
                response_time=str(response_time),
                status=status)
            language_logger_inputs.append(language_logger_object)

        except Exception as e:
            language_logger_object = await create_language_logger_input(
                turn_id = turn_id,
                msg_id = msg_id,
                msg_state = "Outgoing Audio Error", 
                msg_language = preferred_language,
                msg_type=message.message_type.value, 
                t_language = " ",
                t_type=" ",
                t_model="Dhruva/Azure",
                response_time=" ",
                status="Error in text to speech conversion")
            language_logger_inputs.append(language_logger_object)

            logger.error("Error in text to speech: %s", e)

    elif message_type == MessageType.DOCUMENT:
        if not message.document:
            raise ValueError("Message document is empty")
        
        vernacular_text, response_time = await measure_time_async(translator.translate_text, message.document.caption, LanguageCodes.EN, preferred_language)
        
        translated_document_message = DocumentMessage(
            url=message.document.url,
            caption=vernacular_text,
            name=message.document.name,
        )

        if translated_document_message is None:
            status="Translated document message not created"
        else:
            status="Success"
        
        channel_inputs.append(
            Channel(
                source="language",
                intent=ChannelIntent.CHANNEL_OUT,
                turn_id=turn_id,
                bot_output=Message(
                    message_type=MessageType.DOCUMENT,
                    document=translated_document_message,
                ),
            )
        )

        if not channel_inputs:
            status="No response created for channel"

        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Outgoing/Coming from flow", 
            msg_language = LanguageCodes.EN.value,
            msg_type=message.message_type.value, 
            t_language = preferred_language,
            t_type="Text",
            t_model="Dhruva/Azure",
            response_time=str(response_time),
            status=status)
        
        language_logger_inputs.append(language_logger_object)
        
    elif message_type == MessageType.IMAGE:
        if not message.image:
            raise ValueError("Message image is empty")

        vernacular_text, response_time = await measure_time_async(translator.translate_text, message.image.caption, LanguageCodes.EN, preferred_language)

        translated_image_message = ImageMessage(
            url=message.image.url,
            caption=vernacular_text,
        )

        if translated_image_message is None:
            status="Translated image message not created"
        else:
            status="Success"

        channel_inputs.append(
            Channel(
                source="language",
                intent=ChannelIntent.CHANNEL_OUT,
                turn_id=turn_id,
                bot_output=Message(
                    message_type=MessageType.IMAGE, image=translated_image_message
                ),
            )
        )

        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Outgoing/ Text", 
            msg_language = LanguageCodes.EN.value,
            msg_type="Image caption/Text", 
            t_language = preferred_language,
            t_type="Text",
            t_model="Dhruva/Azure",
            response_time=str(response_time),
            status=status)
        
        language_logger_inputs.append(language_logger_object)

    elif message_type == MessageType.BUTTON or message_type == MessageType.OPTION_LIST:
        if message_type == MessageType.BUTTON:
            interactive_message = message.button
        elif message_type == MessageType.OPTION_LIST:
            interactive_message = message.option_list

        if not interactive_message:
            raise ValueError("Interactive message is empty")
        
        total_response_time: float = 0
        vernacular_body, response_time = await measure_time_async(translator.translate_text, interactive_message.body, LanguageCodes.EN, preferred_language)
        total_response_time += response_time

        vernacular_options = [
            Option(
                option_id=option.option_id,
                option_text=option_text,
                response_time=response_time
            )
            for option in interactive_message.options
            for option_text, response_time in [await measure_time_async(translator.translate_text, option.option_text, LanguageCodes.EN, preferred_language)]
        ]
        total_response_time += response_time

        vernacular_header, response_time = await measure_time_async(translator.translate_text, interactive_message.header, LanguageCodes.EN, preferred_language)

        total_response_time += response_time
        vernacular_footer, response_time = await measure_time_async(translator.translate_text, interactive_message.footer, LanguageCodes.EN, preferred_language)
 
        total_response_time += response_time

        language_logger_object = await create_language_logger_input(
            turn_id = turn_id,
            msg_id = msg_id,
            msg_state = "Outgoing Text", 
            msg_language = LanguageCodes.EN.value,
            msg_type=message.message_type.value, 
            t_language = preferred_language,
            t_type=message.message_type.value,
            t_model="Dhruva/Azure",
            response_time=str(total_response_time),
            status="Success")
        
        language_logger_inputs.append(language_logger_object)

        if message_type == MessageType.BUTTON:
            translated_interactive_message = ButtonMessage(
                body=vernacular_body,
                header=vernacular_header,
                footer=vernacular_footer,
                options=vernacular_options,
            )
            channel_input = Channel(
                source="language",
                intent=ChannelIntent.CHANNEL_OUT,
                turn_id=turn_id,
                bot_output=Message(
                    message_type=MessageType.BUTTON,
                    button=translated_interactive_message,
                ),
            )

        else:
            conversion_start_time = time.time()

            translated_interactive_message = ListMessage(
                body=vernacular_body,
                header=vernacular_header,
                footer=vernacular_footer,
                options=vernacular_options,
                button_text=await translator.translate_text(
                    interactive_message.button_text,
                    LanguageCodes.EN,
                    preferred_language,
                ),
                list_title=await translator.translate_text(
                    interactive_message.list_title, LanguageCodes.EN, preferred_language
                ),
            )

            conversion_end_time = time.time()
            response_time = conversion_end_time - conversion_start_time

            if translated_interactive_message is None:
                status="Translated list message not created"
            else:
                status="Success"

            language_logger_object = await create_language_logger_input(
                turn_id = turn_id,
                msg_id = msg_id,
                msg_state = "Outgoing", 
                msg_language = LanguageCodes.EN.value,
                msg_type="Button text/ list title", 
                t_language = preferred_language,
                t_type="Button text/ list title",
                t_model="Dhruva/Azure",
                response_time=str(response_time),
                status=status)
            
            language_logger_inputs.append(language_logger_object)

            channel_input = Channel(
                source="language",
                intent=ChannelIntent.CHANNEL_OUT,
                turn_id=turn_id,
                bot_output=Message(
                    message_type=MessageType.OPTION_LIST,
                    option_list=translated_interactive_message,
                ),
            )
        channel_inputs.append(channel_input)
        try:
            audio_content, response_time = await measure_time_async(speech_processor.text_to_speech, vernacular_body, preferred_language)

            if not audio_content:
                status = "Conversion to audio failed"
            else:
                status = "Success"

            fid = str(uuid.uuid4())
            filename = f"{fid}.mp3"
            await storage.write_file(filename, audio_content, "audio/mpeg")
            audio_url = await storage.public_url(filename)
            translated_audio_message = AudioMessage(media_url=audio_url)

            if translated_audio_message is None:
                status="Translated audio message not created"
            else:
                status="Success"

            channel_inputs.append(
                Channel(
                    source="language",
                    intent=ChannelIntent.CHANNEL_OUT,
                    turn_id=turn_id,
                    bot_output=Message(
                        message_type=MessageType.AUDIO,
                        audio=translated_audio_message,
                    ),
                )
            )

            language_logger_object = await create_language_logger_input(
                turn_id = turn_id,
                msg_id = msg_id,
                msg_state = "Outgoing Audio", 
                msg_language = preferred_language,
                msg_type="Text", 
                t_language = preferred_language,
                t_type="Speech",
                t_model="Dhruva/Azure",
                response_time=str(response_time),
                status=status)
            
            language_logger_inputs.append(language_logger_object)

        except Exception as e:
            language_logger_object = await create_language_logger_input(
                turn_id = turn_id,
                msg_id = msg_id,
                msg_state = "Outgoing Audio Error", 
                msg_language = preferred_language,
                msg_type=message.message_type.value, 
                t_language = " ",
                t_type=" ",
                t_model="Dhruva/Azure",
                response_time=" ",
                status="Error in text to speech conversion")
            language_logger_inputs.append(language_logger_object)

            logger.error("Error in text to speech: %s %s", e, traceback.format_exc())

    return channel_inputs, language_logger_inputs
