import os
import asyncio
import signal
from dotenv import load_dotenv
from loguru import logger

from sync_service import CalendarSyncService

# Setup logging
logger.add(
    "logs/sync_service.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

# Load environment variables
load_dotenv()

class ServiceManager:
    def __init__(self):
        self.sync_service = CalendarSyncService(
            db_host=os.getenv("POSTGRES_HOST", "localhost"),
            db_port=os.getenv("POSTGRES_PORT", "5432"),
            db_name=os.getenv("POSTGRES_DB", "vrchat_events"),
            db_user=os.getenv("POSTGRES_USER", "vrchat_user"),
            db_password=os.getenv("POSTGRES_PASSWORD"),
            credentials_file=os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS",
                "credentials.json"
            )
        )
        self._shutdown = False

    async def start(self):
        """Start the sync service"""
        await self.sync_service.start()
        
        # Keep the service running
        while not self._shutdown:
            await asyncio.sleep(1)

    async def shutdown(self, sig=None):
        """Gracefully shutdown the service"""
        if sig:
            logger.info(f"Received exit signal {sig.name}...")
        
        self._shutdown = True
        logger.info("Shutting down sync service...")
        await self.sync_service.stop()
        
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        logger.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.get_event_loop().stop()

async def main():
    # Initialize service manager
    manager = ServiceManager()

    # load environment variables
    load_dotenv()
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s,
            lambda s=s: asyncio.create_task(manager.shutdown(s))
        )

    try:
        await manager.start()
    finally:
        loop.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted")
    finally:
        logger.info("Sync service shutdown complete")