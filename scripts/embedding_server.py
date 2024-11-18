from suql.faiss_embedding import MultipleEmbeddingStore
from loguru import logger
import os

def init_embedding_store(data_dir: str):
    """Initialize the embedding store for VRChat events"""
    try:
        # Create embedding store instance
        embedding_store = MultipleEmbeddingStore()

        # Add main events table
        embedding_store.add(
            table_name="events",
            primary_key_field_name="_id",
            free_text_field_name="description",
            db_name="vr_event_hub",
            user="select_user",
            password="select_user",
            chunking_param=512,
            cache_embedding=True
        )

        # Add events table summary field
        embedding_store.add(
            table_name="events",
            primary_key_field_name="_id",
            free_text_field_name="summary",
            db_name="vr_event_hub",
            user="select_user",
            password="select_user",
            chunking_param=0,
            cache_embedding=True
        )

        return embedding_store

    except Exception as e:
        logger.error(f"Failed to initialize embedding store: {e}")
        raise

if __name__ == "__main__":
    # Server configuration
    # TODO: Set these values through config/server_config.yaml
    HOST = "127.0.0.1"
    PORT = 8501
    DATA_DIR = "src/vrchat_guide/data"  # Adjust this path as needed

    logger.info("Initializing VRChat Guide Embedding Server...")
    
    try:
        # Initialize and start server
        embedding_store = init_embedding_store(DATA_DIR)
        logger.info(f"Starting embedding server on {HOST}:{PORT}")
        embedding_store.start_embedding_server(host=HOST, port=PORT)
        
    except Exception as e:
        logger.error(f"Failed to start embedding server: {e}")
        raise