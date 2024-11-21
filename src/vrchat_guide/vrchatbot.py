import asyncio
import datetime
import yaml
import os
import sys
from decimal import Decimal
from typing import Dict, List
from uuid import uuid4

from loguru import logger
from suql.agent import postprocess_suql
from worksheets.agent import Agent
from worksheets.interface_utils import conversation_loop
from worksheets.knowledge import SUQLKnowledgeBase, SUQLParser


# Define API functions
def update_profile(username: str, experience_level: str, device_mode: str, social_preferences: str, **kwargs):
    return {
        "status": "success",
        "params": {
            "username": username.value,
            "experience_level": experience_level.value,
            "device_mode": device_mode.value,
            "social_preferences": social_preferences.value,
        },
        "response": {"session_id": uuid4()},
    }

def add_event(iCalUID: str, summary: str, start: datetime.datetime, end: datetime.datetime,
                location: str, description: str, attendees: list, **kwargs):
    return {
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
        "response": {"session_id": uuid4()},
    }


# Initialize paths to prompt and data directories
current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")
data_dir = os.path.join(current_dir, "data")


# DB configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "vrchat_events",
    "select_user": "select_user",    
    "select_password": "select_user",
    "creator_user": "creator_role",
    "creator_password": "creator_role",
    "embedding_server_address": "http://localhost:8501"
}


def result_postprocess(results: List[Dict], columns: List[str]) -> List[Dict]:
    processed_results = []
    for result in results:
        if '_id' in result:
            result = {
                'id': result['_id'],
                'summary': result.get('summary', ''),
                'start_time': result.get('start_time'),
                'end_time': result.get('end_time'),
                'location': result.get('location', ''),
                'description': result.get('description', '')
            }
        processed_results.append(result)
    return processed_results


# Initialize knowledge base
suql_knowledge = SUQLKnowledgeBase(
    llm_model_name="gpt-4o",
    tables_with_primary_keys={"events": "_id"},
    database_name=DB_CONFIG["dbname"],
    embedding_server_address=DB_CONFIG["embedding_server_address"],
    source_file_mapping={
        "vrchat_general_info": os.path.join(data_dir, "vrchat_general_info.txt"),
        "vrchat_community_guidelines": os.path.join(data_dir, "vrchat_community_guidelines.txt"),
        "vrchat_user_guide": os.path.join(data_dir, "vrchat_user_guide.txt"),
        "vrchat_events": os.path.join(data_dir, "vrchat_events.txt"),
    },
    db_host=DB_CONFIG["host"],
    db_port=DB_CONFIG["port"],
    db_username=DB_CONFIG["select_user"],
    db_password=DB_CONFIG["select_password"],
    postprocessing_fn=postprocess_suql,
    result_postprocessing_fn=result_postprocess,
)
# Initialize SUQL parser
suql_parser = SUQLParser(
    llm_model_name="gpt-4o",
)

# Configure logging
def prompt_filter(record):
    excluded_terms = [
        "prompt", "Prompt", "PROMPT",
        "gpt-4", "GPT", "token",
        "completion", "llama", "embedding"
    ]
    return not any(term in str(record["message"]) for term in excluded_terms)

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    filter=prompt_filter,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <white>{message}</white>"
)
logger.add(
    "vrchat_bot.log",
    level="DEBUG",
    filter=prompt_filter,
    rotation="500 MB"
)


# Only used when running directly (not imported)
async def main():
    print("inside async main in vrchat_bot.py")
    try:
        bot = Agent(
            botname="VRChatBot",
            description="You are an assistant at VRChat and help users with all their queries related to finding events and adding them to their calendar. You can search for events, answer questions about events and add them to calendar",
            prompt_dir=prompt_dir,
            starting_prompt="""Hello! I'm your VRChat Guide. I can help you with:
- Create / Update your VRChat profile with your preferences
- Explore / Learn about upcoming VRChat events and add them to your calendar
- Answer any questions related to VRChat events

How can I help you today?""",
            args={},
            api=[update_profile, add_event],
            knowledge_base=suql_knowledge,
            knowledge_parser=suql_parser,
        ).load_from_gsheet(
            gsheet_id="1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU",
        )
        print("bot loaded in main in vrchat_bot.py, calling conversation_loop")
        await conversation_loop(bot, "vrchat_bot.json")
        
    except Exception as e:
        logger.error(f"Failed to start VRChat bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting VRChat bot...")
    asyncio.run(main())