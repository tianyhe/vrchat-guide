import asyncio
import datetime
import json
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

# Initialize paths
current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

async def check_services(max_retries=3, retry_delay=5):
    """Check if required services are running"""
    from .services_init import VRChatServices
    
    for attempt in range(max_retries):
        try:
            services = VRChatServices()
            connection_details = services.get_connection_details()
            
            # Test database connection
            import psycopg2
            conn = psycopg2.connect(
                host=connection_details["database"]["host"],
                port=connection_details["database"]["port"],
                dbname=connection_details["database"]["name"],
                user=connection_details["database"]["user"],
                password=connection_details["database"]["password"]
            )
            conn.close()
            
            # Test embedding server connection
            import requests
            # Just check if the server responds at all, don't look for specific endpoint
            embedding_response = requests.get(connection_details['embedding_server'])
            if embedding_response.status_code == 404:  # 404 is okay - means server is running
                logger.info("Embedding server is running")
            
            logger.info("Successfully connected to all services")
            return connection_details
            
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed to connect to services: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to services after {max_retries} attempts")
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed to connect to services: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to services after {max_retries} attempts")
                raise

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

# Initialize services and components
try:
    connection_details = asyncio.run(check_services())
    
    # Initialize knowledge base
    suql_knowledge = SUQLKnowledgeBase(
        llm_model_name="gpt-4o",
        tables_with_primary_keys={"events": "_id"},
        database_name=connection_details["database"]["name"],
        embedding_server_address=connection_details["embedding_server"],
        source_file_mapping={
            "vrchat_general_info": os.path.join(current_dir, "text_sources/vrchat_general_info.txt"),
            "vrchat_community_guidelines": os.path.join(current_dir, "text_sources/vrchat_community_guidelines.txt"),
            "vrchat_user_guide": os.path.join(current_dir, "text_sources/vrchat_user_guide.txt")
        },
        db_host=connection_details["database"]["host"],
        db_port=connection_details["database"]["port"],
        db_username=connection_details["database"]["user"],
        db_password=connection_details["database"]["password"],
        postprocessing_fn=postprocess_suql,
        result_postprocessing_fn=result_postprocess,
    )

    # Initialize SUQL parser
    suql_parser = SUQLParser(
        llm_model_name="gpt-4o",
    )

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

except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    raise

# Only used when running directly (not imported)
async def main():
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
        
        await conversation_loop(bot, "vrchat_bot.json")
        
    except Exception as e:
        logger.error(f"Failed to start VRChat bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting VRChat bot...")
    asyncio.run(main())