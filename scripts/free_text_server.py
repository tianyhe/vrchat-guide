from flask import Flask
from loguru import logger
from packages.suql.src.suql.free_text_fcns_server import start_free_text_fncs_server
import os
import yaml

# Load the configuration from the config file in ./config/server_config.yaml
server_config_path = os.path.join(os.path.dirname(__file__), "../config", "server_config.yaml")
server_config = yaml.safe_load(open(server_config_path))
fts_config = server_config["free_text_server"]

def setup_llm_config():
    """Setup LLM configuration for the free text server"""
    # Default configuration
    config = {
        "host": fts_config["host"],
        "port": fts_config["port"],
        "k": fts_config["k"],  # Number of relevant documents to consider
        "max_input_token": fts_config["max_input_token"],  # Maximum input tokens for context
        "engine": fts_config["engine"]  # Using the specified model
    }

    return config


if __name__ == "__main__":
    logger.info("Starting VRChat Free Text Functions Server...")
    
    try:
        # Get configuration
        config = setup_llm_config()
        
        # Start the server
        logger.info(f"Starting server on {config['host']}:{config['port']}")
        logger.info(f"Using model: {config['engine']}")
        logger.info(f"Context size: {config['k']} documents, {config['max_input_token']} max tokens")
        
        start_free_text_fncs_server(
            host=config["host"],
            port=config["port"],
            k=config["k"],
            max_input_token=config["max_input_token"],
            engine=config["engine"]
        )
        
    except Exception as e:
        logger.error(f"Failed to start free text server: {e}")
        raise