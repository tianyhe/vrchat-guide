import json
import os
import sys
from dotenv import load_dotenv

import chainlit as cl
from loguru import logger

from worksheets.agent import Agent
from worksheets.annotation_utils import get_agent_action_schemas, get_context_schema
from worksheets.chat_chainlit import generate_next_turn_cl
from worksheets.modules import CurrentDialogueTurn

load_dotenv()

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_dir, "..", ".."))


from vrchatbot.vrchatbot import (
        update_profile,
        add_event,
        prompt_dir,
        suql_knowledge,
        suql_parser,
)

logger.remove()

logger.add(
    os.path.join(current_dir, "..", "user_logs", "user_logs.log"), rotation="1 day"
)

# Unhappy paths
unhappy_paths = [
    "**- Change your mind about the username you want to use**",
    "**- Change your mind about the experience level you want to set**",
    "**- Change your mind about the device mode you want to set**",
    "**- Change your mind about the social preferences you want to set**",
    "**- Change your mind about event you would to attend in the middle of conversation**",
    "**- Change your mind about the event details in the middle of the conversation (eg. change the event name, change the event location, change the event description, change the event attendees)**",
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
    cl.user_session.set(
        "bot",
        Agent(
            botname="VRChatBot",
            description="You an assistant at VRChat and help users with all their queries related to finding events and adding them to their calendar. You can search for events, ask me anything about the event and add the interested one to calendar",
            prompt_dir=prompt_dir,
            starting_prompt="""Hello! I'm your VRChat Guide. I can help you with:
- Create / Update your VRChat profile with your preferences
- Explore / Learn about upcoming VRChat events and add them to your calendar
- Asking me any question related to the details of the VRChat events I purposed

How can I help you today?""",
            args={},
            api=[update_profile, add_event],
            knowledge_base=suql_knowledge,
            knowledge_parser=suql_parser,
        ).load_from_gsheet(
            gsheet_id="1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU",
        ),
    )

    if not os.path.exists(os.path.join(current_dir, "user_conversation")):
        os.mkdir(os.path.join(current_dir, "user_conversation"))
    user_id = cl.user_session.get("id")
    logger.info(f"Chat started for user {user_id}")
    if not os.path.exists(os.path.join(current_dir, "user_conversation", user_id)):
        os.mkdir(os.path.join(current_dir, "user_conversation", user_id))
    await cl.Message(
        f"Here is your user id: **{user_id}**\n"
        + cl.user_session.get("bot").starting_prompt
        + f"\n\nPlease be a difficult user who asks several questions, here are some examples: {unhappy_paths}"
    ).send()


@cl.on_message
async def get_user_message(message):
    bot = cl.user_session.get("bot")
    await generate_next_turn_cl(message.content, bot)

    cl.user_session.set("bot", bot)

    response = bot.dlg_history[-1].system_response
    await cl.Message(response).send()


@cl.on_chat_end
def on_chat_end():
    user_id = cl.user_session.get("id")
    if not os.path.exists(
        os.path.join(
            current_dir,
            "user_conversation",
            user_id,
        )
    ):
        os.mkdir(
            os.path.join(
                current_dir,
                "user_conversation",
                user_id,
            )
        )

    bot = cl.user_session.get("bot")
    if len(bot.dlg_history):
        with open(
            os.path.join(
                current_dir,
                "user_conversation",
                user_id,
                "conversation.json",
            ),
            "w",
        ) as f:
            json.dump(convert_to_json(bot.dlg_history), f)
    else:
        os.rmdir(os.path.join(current_dir, "user_conversation", user_id))

    logger.info(f"Chat ended for user {user_id}")
