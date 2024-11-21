import json
import os
import sys
import time
from dotenv import load_dotenv

import chainlit as cl
from loguru import logger

from worksheets.agent import Agent
from worksheets.annotation_utils import get_agent_action_schemas, get_context_schema
from worksheets.chat_chainlit import generate_next_turn_cl
from worksheets.modules import CurrentDialogueTurn
from vrchat_guide.metrics.utils import MetricsManager
from vrchat_guide.metrics.log_config import LogConfig

load_dotenv()

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_dir, "..", ".."))

# Set session ID to current timestamp
session_timestamp = str(int(time.time()))

from vrchat_guide.vrchatbot import (
        update_profile,
        add_event,
        prompt_dir,
        suql_knowledge,
        suql_parser,
)

# Initialize logging
log_config = LogConfig()
logger.add(log_config.debug_dir / f"debug_{session_timestamp}.log")

# Initialize metrics manager
metrics_manager = MetricsManager(
    metrics_dir=str(log_config.metrics_dir),
    session_timestamp=session_timestamp
)

# Update conversation save location
conversation_file = log_config.get_session_path(session_timestamp, "conversation")
prompts_file = log_config.get_session_path(session_timestamp, "prompts")

# Unhappy paths
unhappy_paths = [
    "**- Change your mind about the username you want to use**",
    "**- Change your mind about the experience level you want to set**",
    "**- Change your mind about the device mode you want to set**",
    "**- Change your mind about the social preferences you want to set**",
    "**- Change your mind about event you would to attend in the middle of conversation**",
    "**- Change your mind about your preference for the event you would like to attend in the middle of conversation**",
]

unhappy_paths = "\n" + "\n".join(unhappy_paths)


def convert_to_json(dialogue: list[CurrentDialogueTurn]):
    """Convert a conversation into a JSON format."""
    json_dialogue = []
    for turn in dialogue:
        json_turn = {
            "user": turn.user_utterance,
            "bot": turn.system_response,
            "turn_context": get_context_schema(turn.context),
            "global_context": get_context_schema(turn.global_context),
            "system_action": get_agent_action_schemas(turn.system_action),
            "user_target_sp": turn.user_target_sp,
            "user_target": turn.user_target,
            "user_target_suql": turn.user_target_suql,
        }
        json_dialogue.append(json_turn)
    return json_dialogue



@cl.on_chat_start
async def initialize():
    try:
        cl.user_session.set(
            "bot",
            Agent(
                botname="VRChatBot",
                description="You are an assistant at VRChat and help users with all their queries related to finding events, adding them to their calendar, and providing general information about VRChat. You can search for events, answer any questions about the event, add the interested ones to the calendar, and provide general information stored in your knowledge base.",
                prompt_dir=prompt_dir,
                starting_prompt="""Hello! I'm your VRChat Guide. I can help you with:
- Create / Update your VRChat profile with your preferences
- Explore / Learn about upcoming VRChat events and add them to your calendar
- Answer any general queries, provide onboarding tips, and FAQs

How can I help you today?""",
                args={},
                api=[update_profile, add_event],
                knowledge_base=suql_knowledge,
                knowledge_parser=suql_parser,
            ).load_from_gsheet(
                gsheet_id="1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU",
            ),
        )

        # Initialize metrics for this session
        metrics_manager.logger.start_session(session_timestamp)

        # Initialize conversation directory
        # if not os.path.exists(os.path.join(current_dir, "user_conversation")):
        #     os.mkdir(os.path.join(current_dir, "user_conversation"))
        # user_id = cl.user_session.get("id")
        # logger.info(f"Chat started for user - {session_timestamp}")
        # if not os.path.exists(os.path.join(current_dir, "user_conversation", session_timestamp)):
        #     os.mkdir(os.path.join(current_dir, "user_conversation", session_timestamp))
        await cl.Message(
            f"Here is your session id: **{session_timestamp}**\n"
            + cl.user_session.get("bot").starting_prompt
            + f"\n\nPlease be a difficult user who asks several questions, here are some examples: {unhappy_paths}"
        ).send()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


@cl.on_message
async def get_user_message(message):
    try:
        start_time = time.time()
        bot = cl.user_session.get("bot")
        
        await generate_next_turn_cl(message.content, bot)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log metrics for this turn
        metrics_manager.handle_dialogue_turn(bot.dlg_history[-1], response_time)
        
        cl.user_session.set("bot", bot)
        
        response = bot.dlg_history[-1].system_response
        await cl.Message(response).send()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


@cl.on_chat_end
async def on_chat_end():
    try:
        # End metrics session
        metrics_manager.logger.end_session()

        # Log conversation history
        bot = cl.user_session.get("bot")
        if len(bot.dlg_history):
            with open(conversation_file, "w") as f:
                json.dump(convert_to_json(bot.dlg_history), f, indent=4)
        else:
            # If there's no conversation history, create an empty JSON file
            with open(conversation_file, "w") as f:
                json.dump([], f)

        logger.info(f"Chat ended for user - {session_timestamp}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
