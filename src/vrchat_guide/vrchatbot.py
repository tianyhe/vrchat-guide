import asyncio
import os
import sys
import random
from uuid import uuid4
from typing import Dict, List

from suql.agent import postprocess_suql

from worksheets import (
    Config,
    SUQLKnowledgeBase,
    conversation_loop,
)

from worksheets.agent.agent import Agent
from worksheets.agent.builder import TemplateLoader
from worksheets.agent.config import agent_api
from worksheets.core.worksheet import get_genie_fields_from_ws
from worksheets.knowledge.parser import SUQLParser
from worksheets import Config, OpenAIModelConfig


# Define API functions


@agent_api("update_profile", "Update VRChat user profile")
def update_profile(
    username: str,
    experience_level: str,
    device_mode: str,
    social_preferences: str,
    **kwargs,
):
    return {
        "status": "success",
        "params": {
            "username": username,
            "experience_level": experience_level.value,
            "device_mode": device_mode.value,
            "social_preferences": social_preferences.value,
        },
        "response": {"session_id": uuid4()},
    }


@agent_api("event_detail_to_individual_params", "Get event details")
def event_detail_to_individual_params(event_detail):
    if event_detail.value is None:
        return {}
    event_detail = event_detail.value
    event_details = {}
    for field in get_genie_fields_from_ws(event_detail):
        event_details[field.name] = field.value

    return event_details


@agent_api("add_event", "Add an event to VRChat calendar")
def add_event(event: str, attendees: list = None, notes: str = None, **kwargs):
    return {
        "status": "success",
        "params": {
            "iCalUID": event.value.id.value,
            "attendees": attendees or [],  # Default to an empty list if None
            "notes": notes or "",  # Default to an empty string if None
        },
        "response": {"session_id": str(uuid4())},  # Ensure UUID is a string
    }


# Define result postprocessing function for SUQL queries

def result_postprocess(results: List[Dict], columns: List[str]) -> List[Dict]:
    processed_results = []
    for result in results:
        if "_id" in result:
            result = {
                "id": result["_id"],
                "summary": result.get("summary", ""),
                "start_time": result.get("start_time"),
                "end_time": result.get("end_time"),
                "location": result.get("location", ""),
                "description": result.get("description", ""),
            }
        processed_results.append(result)
    return processed_results


# Define path to the prompts


current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

config = Config.load_from_yaml(os.path.join(current_dir, "config.yaml"))

starting_prompt = TemplateLoader.load(
    os.path.join(current_dir, "starting_prompt.md"), format="jinja2"
)


# Define Knowledge Base
suql_knowledge_base = SUQLKnowledgeBase(
    model_config=config,
    tables_with_primary_keys={"events": "_id"},
    database_name="vrchat_events",
    embedding_server_address="http://127.0.0.1:8509",
    source_file_mapping={
        "vrchat_general_info": os.path.join(current_dir, "./data/vrchat_general_info.txt"),
        "vrchat_community_guidelines": os.path.join(current_dir, "./data/vrchat_community_guidelines.txt"),
        "vrchat_user_guide": os.path.join(current_dir, "./data/vrchat_user_guide.txt"),
    },
    postprocessing_fn=None,  # custom functions to postprocess SUQL queries
    result_postprocessing_fn=result_postprocess,  # custom functions to postprocess SUQL results
    db_username="select_user",
    db_password="select_user",
)

# Define the SUQL Parser
suql_parser = SUQLParser(
    model_config=config
)




async def main():
    print("inside async main in vrchat_bot.py")
    try:
        vrchatbot = Agent(
            botname="VRChat Assistant",
            description="You are a VRChat assistant that helps users discover events, answer questions, add events to their calendar, and guide them through onboarding and navigation with helpful tips.",
            config=config,
            starting_prompt=starting_prompt.render(),
            api=[update_profile, event_detail_to_individual_params, add_event],
            knowledge_base=suql_knowledge_base,
            knowledge_parser=suql_parser,
        )
        vrchatbot.load_runtime_from_specification(
            gsheet_id="1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU",
        )
        print("bot loaded in main in vrchat_bot.py, calling conversation_loop")
        await conversation_loop(vrchatbot, "vrchat_bot.json")
    
    except Exception as e:
        print(f"Failed to start VRChat bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting VRChat bot...")
    asyncio.run(main())
