from typing import List
import os
import shutil
import logging
import subprocess
from pathlib import Path
from ..extensions import produce_message
from lib.data_models import BotConfig, BotIntent
from ..crud import create_bot
from .bot_input import create_flow_logger_input

logger = logging.getLogger("flow")

async def install_bot(
    bot_id: str, bot_fsm_code: str, bot_requirements_txt: str, index_urls: List[str]
):
    requirements_txt = (
        "openai\ncryptography\njb-manager-bot==0.2.3\n" + bot_requirements_txt
    )

    bots_parent_directory = Path(__file__).parent.parent.parent
    bots_root_directory = Path(os.path.join(bots_parent_directory, "bots"))
    bot_dir = Path(os.path.join(bots_root_directory, bot_id))

    # remove directory if it already exists
    if bot_dir.exists():
        shutil.rmtree(bot_dir)

    bot_dir.mkdir(exist_ok=True, parents=True)

    # copy the contents of Path(__file__).parent/template into the bot's directory
    template_dir = Path(os.path.join(bots_parent_directory, "template"))
    for item in template_dir.iterdir():
        if item.is_dir():
            shutil.copytree(item, bot_dir / item.name)
        else:
            shutil.copy2(item, bot_dir)

    bot_code_file = Path(os.path.join(bot_dir, "bot.py"))
    bot_code_file.write_text(bot_fsm_code)

    # create a requirements.txt file in the bot's directory
    requirements_file = Path(os.path.join(bot_dir, "requirements.txt"))
    requirements_file.write_text(requirements_txt)

    # create a venv inside the bot's directory
    venv_dir = Path(os.path.join(bot_dir, ".venv"))
    subprocess.run(["python3", "-m", "venv", venv_dir])
    install_command = [str(venv_dir / "bin" / "pip"), "install"]
    for index_url in index_urls:
        install_command.extend(["--extra-index-url", index_url])
    install_command.extend(["-r", requirements_file])
    subprocess.run(install_command)
    logger.info("Installed bot %s", bot_id)


async def delete_bot(bot_id: str):
    bots_parent_directory = Path(__file__).parent.parent.parent
    bots_root_directory = Path(os.path.join(bots_parent_directory, "bots"))
    bot_dir = Path(os.path.join(bots_root_directory, bot_id))
    shutil.rmtree(bot_dir)
    logger.info("Deleted bot %s", bot_id)


async def handle_bot(bot_config: BotConfig):
    if bot_config.intent == BotIntent.DELETE:
        await delete_bot(bot_config.bot_id)
    elif bot_config.intent == BotIntent.INSTALL:
        if not bot_config.bot:
            logger.error("Bot config missing bot")
            return
        await install_bot(
            bot_id=bot_config.bot_id,
            bot_fsm_code=bot_config.bot.fsm_code,
            bot_requirements_txt=bot_config.bot.requirements_txt,
            index_urls=bot_config.bot.index_urls,
        )
        await create_bot(
            bot_id=bot_config.bot_id,
            name=bot_config.bot.name,
            code=bot_config.bot.fsm_code,
            requirements=bot_config.bot.requirements_txt,
            index_urls=bot_config.bot.index_urls,
            required_credentials=bot_config.bot.required_credentials,
            version=bot_config.bot.version,
        )
    else:
        flow_logger_object = await create_flow_logger_input(
            turn_id="", 
            session_id="", 
            msg_intent = "Incoming", 
            flow_intent = "Bot", 
            sent_to_service="",
            status="Invalid intent in bot config"
        )
        produce_message(flow_logger_object)
        logger.error("Invalid intent in bot config")
