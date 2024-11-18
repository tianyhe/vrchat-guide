import requests
import json
from loguru import logger
import time

def test_embedding_server(host="127.0.0.1", port=8501):
    """Test the FAISS embedding server"""
    url = f"http://{host}:{port}"
    test_data = {
        "texts": [
            "This is a test sentence for embedding.",
            "Another test sentence to verify the embedding server."
        ]
    }
    
    try:
        logger.info("Testing embedding server...")
        response = requests.post(f"{url}/encode", json=test_data)
        
        if response.status_code == 200:
            embeddings = response.json()
            if isinstance(embeddings, list) and len(embeddings) == 2:
                logger.info("✓ Embedding server is working correctly!")
                logger.info(f"  - Generated embeddings of shape: {len(embeddings)}x{len(embeddings[0])}")
                return True
        else:
            logger.error(f"Embedding server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to embedding server at {url}")
        return False
    except Exception as e:
        logger.error(f"Error testing embedding server: {e}")
        return False

def test_free_text_server(host="127.0.0.1", port=8500):
    """Test the free text functions server"""
    url = f"http://{host}:{port}"
    test_data = {
        "text": "This is a test document about VRChat events.",
        "question": "What is this document about?"
    }
    
    try:
        logger.info("Testing free text server...")
        response = requests.post(f"{url}/answer", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            if "answer" in result:
                logger.info("✓ Free text server is working correctly!")
                logger.info(f"  - Sample response: {result['answer']}")
                return True
        else:
            logger.error(f"Free text server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to free text server at {url}")
        return False
    except Exception as e:
        logger.error(f"Error testing free text server: {e}")
        return False

def wait_for_servers(max_attempts=5, delay=2):
    """Wait for servers to start up"""
    logger.info(f"Waiting for servers to start (max {max_attempts} attempts)...")
    
    for attempt in range(max_attempts):
        if attempt > 0:
            time.sleep(delay)
            logger.info(f"Attempt {attempt + 1}...")
            
        embedding_ok = test_embedding_server()
        free_text_ok = test_free_text_server()
        
        if embedding_ok and free_text_ok:
            logger.info("Both servers are running and responding correctly!")
            return True
            
    logger.error("Could not verify both servers are running after maximum attempts")
    return False

if __name__ == "__main__":
    logger.info("Starting SUQL servers test...")
    wait_for_servers()