import os
import sys
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_dir)
from database.database_init import VRChatDatabaseManager
from embedding_server.server import VRChatEmbeddingServer
from database.sync_service import CalendarSyncService
class VRChatServices:
    def __init__(
        self,
        db_host: str = "127.0.0.1",
        db_port: str = "5432",
        db_name: str = "vrchat_events",
        db_user: str = "vrchat_user",
        db_password: str = os.getenv("DB_PASSWORD", "NEUcs7980"),
        embedding_host: str = "127.0.0.1",
        embedding_port: str = "8608",
        credentials_file: str = "credentials.json",
        text_sources_dir: str = "data",
    ):
        # Database configuration
        self.db_config = {
            "db_host": db_host,
            "db_port": db_port,
            "db_name": db_name,
            "db_user": db_user,
            "db_password": db_password
        }
        
        # Embedding server configuration
        self.embedding_config = {
            "host": embedding_host,
            "port": embedding_port
        }
        
        # Service instances
        self.db_manager: Optional[VRChatDatabaseManager] = None
        self.embedding_server: Optional[VRChatEmbeddingServer] = None
        self.calendar_sync: Optional[CalendarSyncService] = None
        
        # Paths
        self.credentials_file = credentials_file
        self.text_sources = {
            "general_info": os.path.join(text_sources_dir, "vrchat_general_info.txt"),
            "community": os.path.join(text_sources_dir, "vrchat_community_guidelines.txt"),
            "guide": os.path.join(text_sources_dir, "vrchat_user_guide.txt")
        }
        
        # FastAPI app
        self.app = FastAPI(title="VRChat Services")
        
    async def initialize_database(self):
        """Initialize database manager and sync service"""
        try:
            self.db_manager = VRChatDatabaseManager(
                **self.db_config,
                credentials_file=self.credentials_file
            )
            await self.db_manager.initialize()
            
            # Initialize calendar sync service
            self.calendar_sync = CalendarSyncService(
                **self.db_config,
                credentials_file=self.credentials_file
            )
            await self.calendar_sync.start()
            
            logger.info("Database and calendar sync services initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database services: {e}")
            return False

    def initialize_embedding_server(self):
        """Initialize embedding server"""
        try:
            # Convert db_config to match embedding server expectations
            embedding_db_config = {
                "host": self.db_config["db_host"],
                "port": self.db_config["db_port"],
                "dbname": self.db_config["db_name"],
                "user": self.db_config["db_user"],
                "password": self.db_config["db_password"]
            }
            
            self.embedding_server = VRChatEmbeddingServer(
                db_config=embedding_db_config,
                text_sources=self.text_sources
            )
            
            # Add startup event to sync with database
            @self.app.on_event("startup")
            async def startup_event():
                self.embedding_server.sync_with_database()
                self.embedding_server.load_text_sources()
            
            logger.info("Embedding server initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize embedding server: {e}")
            return False

    async def start_services(self):
        """Start all services"""
        # Initialize database first
        db_success = await self.initialize_database()
        if not db_success:
            raise RuntimeError("Failed to initialize database services")
            
        # Initialize embedding server
        embed_success = self.initialize_embedding_server()
        if not embed_success:
            raise RuntimeError("Failed to initialize embedding server")
            
        # Start embedding server
        config = uvicorn.Config(
            self.app, 
            host=self.embedding_config["host"],
            port=int(self.embedding_config["port"]),
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start embedding server: {e}")
            raise

    async def stop_services(self):
        """Stop all services gracefully"""
        try:
            if self.calendar_sync:
                await self.calendar_sync.stop()
            
            if self.db_manager:
                await self.db_manager.shutdown()
                
            logger.info("All services stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            raise

    def get_connection_details(self) -> dict:
        """Get connection details for VRChatBot"""
        return {
            "database": {
                "host": self.db_config["db_host"],
                "port": self.db_config["db_port"],
                "name": self.db_config["db_name"],
                "user": self.db_config["db_user"],
                "password": self.db_config["db_password"]
            },
            "embedding_server": f"http://{self.embedding_config['host']}:{self.embedding_config['port']}"
        }

# Startup script
async def main():
    services = VRChatServices()
    try:
        await services.start_services()
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
    finally:
        await services.stop_services()

if __name__ == "__main__":
    asyncio.run(main())