import asyncio
import datetime
import json
import os
from decimal import Decimal
from uuid import uuid4

from loguru import logger
from suql.agent import postprocess_suql

from worksheets.agent import Agent
from worksheets.interface_utils import conversation_loop
from worksheets.knowledge import SUQLKnowledgeBase, SUQLParser
from worksheets.utils import num_tokens_from_string

# Define your APIs

def update_profile(
        username: str,
        experience_level: str,
        device_mode: str,
        social_preferences: str,
        **kwargs,
):
    outcome = {
        "status": "success",
        "params": {
            "username": username.value,
            "experience_level": experience_level.value,
            "device_mode": device_mode.value,
            "social_preferences": social_preferences.value,
        },
        "response": {
            "session_id": uuid4(),
        },
    }
    return outcome


def add_event(
        iCalUID: str,
        summary: str,
        start: datetime.datetime,
        end: datetime.datetime,
        location: str,
        description: str,
        attendees: list,
        **kwargs,
):
        outcome = {
                "status": "success",
                "params": {
                "iCalUID": iCalUID.value,
                "summary": summary.value,
                "start": start.value,
                "end": end.value,
                "location": location.value,
                "description": description.value,
                "attendees": attendees.value,
                },
                "response": {
                "session_id": uuid4(),
                },
        }
        return outcome


# Define path to the prompts

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

# Define Knowledge Base
suql_knowledge = SUQLKnowledgeBase(
    # llm_model_name="azure/gpt-4o",
    llm_model_name="gpt-4o",
    tables_with_primary_keys={"events": "_id"},
    database_name="events",
    embedding_server_address="http://127.0.0.1:8509",
    source_file_mapping={
        "vrchat_general_info": os.path.join(current_dir, "vrchat_general_info.txt")
    },
    postprocessing_fn=postprocess_suql,
    result_postprocessing_fn=None,
    # api_base="https://ovaloairesourceworksheet.openai.azure.com/",
    # api_version="2024-08-01-preview",
)

# Define the SUQL React Parser
suql_parser = SUQLParser(
    llm_model_name="gpt-4o",
    # llm_model_name="gpt-4",
)

# Define the agent
vrchat_bot = Agent(
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
)


if __name__ == "__main__":
    # Run the conversation loop
    asyncio.run(conversation_loop(vrchat_bot, "vrchat_bot.json"))