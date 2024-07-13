from typing import List
import os
import shutil
import logging
import subprocess
from pathlib import Path
from lib.data_models import BotConfig
from ..crud import create_bot

logger = logging.getLogger("flow")


async def install_or_update_bot(
    bot_id: str, bot_fsm_code: str, bot_requirements_txt: str, index_urls: List[str]
):
    requirements_txt = "openai\ncryptography\njb-manager-bot\n" + bot_requirements_txt

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


async def handle_bot_installation_or_update(bot_config: BotConfig):
    bot_id = bot_config.bot_id
    bot_fsm_code = bot_config.bot_fsm_code
    if not bot_fsm_code:
        raise ValueError("FSM code is required")
    bot_requirements_txt = (
        bot_config.bot_requirements_txt if bot_config.bot_requirements_txt else ""
    )
    index_urls = bot_config.index_urls if bot_config.index_urls else []
    await install_or_update_bot(
        bot_id=bot_id,
        bot_fsm_code=bot_fsm_code,
        bot_requirements_txt=bot_requirements_txt,
        index_urls=index_urls,
    )
    jb_bot = await create_bot(
        bot_id=bot_id,
        name=bot_config.bot_name,
        code=bot_fsm_code,
        requirements=bot_requirements_txt,
        index_urls=index_urls,
        required_credentials=bot_config.bot_required_credentials,
        version=bot_config.bot_version,
    )
    if jb_bot:
        return jb_bot
