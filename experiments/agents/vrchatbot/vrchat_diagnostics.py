import asyncio
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from loguru import logger
from suql.agent import postprocess_suql
from worksheets.knowledge import SUQLKnowledgeBase
from experiments.agents.vrchatbot.database.database_init import VRChatDatabaseManager

# Configure logging
logger.remove()
logger.add(sys.stdout, level="DEBUG")
logger.add("vrchat_diagnostics.log", level="DEBUG", rotation="500 MB")

# Database configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "name": "vrchat_events",
    "user": "vrchat_user",
    "password": "NEUcs7980"
}

def test_direct_database():
    """Test direct database connection and query"""
    logger.info("=== Testing Direct Database Connection ===")
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG["name"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Test 1: Count events
            cur.execute("SELECT COUNT(*) as count FROM events;")
            count = cur.fetchone()
            logger.info(f"Total events in database: {count['count']}")
            
            # Test 2: Check table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'events';
            """)
            columns = cur.fetchall()
            logger.info("Table structure:")
            for col in columns:
                logger.info(f"  {col['column_name']}: {col['data_type']}")
            
            # Test 3: Sample event data
            cur.execute("""
                SELECT * FROM events 
                WHERE start_time > CURRENT_TIMESTAMP 
                ORDER BY start_time 
                LIMIT 1;
            """)
            sample = cur.fetchone()
            logger.info(f"Sample event: {sample}")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Direct database test failed: {e}")
        return False

def test_suql_configuration(suql_knowledge: SUQLKnowledgeBase):
    """Test SUQL knowledge base configuration"""
    logger.info("=== Testing SUQL Configuration ===")
    try:
        logger.info("SUQL Knowledge Base Settings:")
        logger.info(f"Database name: {suql_knowledge.database_name}")
        logger.info(f"Host: {suql_knowledge.db_host}")
        logger.info(f"Port: {suql_knowledge.db_port}")
        logger.info(f"Tables: {suql_knowledge.tables_with_primary_keys}")
        logger.info(f"Embedding server: {suql_knowledge.embedding_server_address}")
        logger.info(f"Source mappings: {suql_knowledge.source_file_mapping}")
        return True
    except Exception as e:
        logger.error(f"SUQL configuration test failed: {e}")
        return False

def test_suql_queries(suql_knowledge: SUQLKnowledgeBase):
    """Test various SUQL queries"""
    logger.info("=== Testing SUQL Queries ===")
    
    test_queries = [
        # Basic count query
        "SELECT COUNT(*) FROM events;",
        
        # Simple select with time filter
        """
        SELECT _id, summary, start_time, end_time 
        FROM events 
        ORDER BY start_time 
        LIMIT 3;
        """,
        
        # Distinct locations
        "SELECT DISTINCT summary FROM events LIMIT 5;",
        
        # Complex query with text search where summary or description contains "[VRC]"
        """
        SELECT * FROM events 
        WHERE summary LIKE '%[VRC]%' OR description LIKE '%[VRC]%'
        ORDER BY start_time 
        LIMIT 2;
        """
    ]
    
    results = {}
    for query in test_queries:
        try:
            logger.info(f"\nExecuting query:\n{query}")
            result = suql_knowledge.run(query)
            logger.info(f"Result: {result}")
            results[query] = result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            results[query] = f"Error: {str(e)}"
    
    return results

async def test_sync_process():
    """Test database sync process"""
    logger.info("=== Testing Database Sync Process ===")
    try:
        db_manager = VRChatDatabaseManager(
            db_host=DB_CONFIG["host"],
            db_port=DB_CONFIG["port"],
            db_name=DB_CONFIG["name"],
            db_user=DB_CONFIG["user"],
            db_password=DB_CONFIG["password"]
        )
        
        # Initialize and sync
        success = await db_manager.initialize()
        if not success:
            logger.error("Database initialization failed")
            return False
            
        # Check status
        status = await db_manager.check_database_status()
        logger.info(f"Sync status: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Sync process test failed: {e}")
        return False

async def main():
    """Run all diagnostic tests"""
    try:
        # Test 1: Direct database connection
        db_success = test_direct_database()
        if not db_success:
            logger.error("Direct database tests failed, stopping diagnostics")
            return
            
        # Test 2: Database sync
        sync_success = await test_sync_process()
        if not sync_success:
            logger.error("Sync process failed, stopping diagnostics")
            return
            
        # Test 3: Initialize SUQL
        suql_knowledge = SUQLKnowledgeBase(
            llm_model_name="gpt-4o",
            tables_with_primary_keys={"events": "_id"},
            database_name=DB_CONFIG["name"],
            embedding_server_address="http://127.0.0.1:8608",
            source_file_mapping={
                "vrchat_general_info": os.path.join(os.path.dirname(__file__), "data/vrchat_general_info.txt")
            },
            db_host=DB_CONFIG["host"],
            db_port=DB_CONFIG["port"],
            db_username=DB_CONFIG["user"],
            db_password=DB_CONFIG["password"],
            postprocessing_fn=postprocess_suql
        )
        
        # Test 4: SUQL configuration
        config_success = test_suql_configuration(suql_knowledge)
        if not config_success:
            logger.error("SUQL configuration test failed, stopping diagnostics")
            return
            
        # Test 5: SUQL queries
        query_results = test_suql_queries(suql_knowledge)
        
        # Print summary
        logger.info("\n=== Diagnostic Summary ===")
        logger.info(f"Direct Database Connection: {'Success' if db_success else 'Failed'}")
        logger.info(f"Database Sync: {'Success' if sync_success else 'Failed'}")
        logger.info(f"SUQL Configuration: {'Success' if config_success else 'Failed'}")
        logger.info("\nQuery Results Summary:")
        for query, result in query_results.items():
            logger.info(f"\nQuery: {query}")
            logger.info(f"Result: {result}")
            
    except Exception as e:
        logger.error(f"Diagnostic execution failed: {e}")
    finally:
        logger.info("\n=== Diagnostics Complete ===")

if __name__ == "__main__":
    logger.info("Starting VRChat SUQL diagnostics...")
    asyncio.run(main())