from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
import logging
import asyncio

class VRChatOSCHandler:
    def __init__(self, bot, ip="127.0.0.1", port=9000):
        self.bot = bot
        self.dispatcher = Dispatcher()
        self.server = ThreadingOSCUDPServer((ip, port), self.dispatcher)
        self.setup_handlers()

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("VRChatOSC")
        
    def setup_handlers(self):
        # Map VRChat OSC addresses to handlers
        self.dispatcher.map("/avatar/parameters/Voice", self.handle_voice)
        self.dispatcher.map("/avatar/parameters/Interact", self.handle_interaction)
        
    async def handle_voice(self, address, *args):
        self.logger.info(f"Received voice input: {args}")
        # Handle voice input from VRChat
        voice_data = args[0]
        await self.bot.generate_next_turn(voice_data)
        
    async def handle_interaction(self, address, *args):
        # Handle avatar interaction triggers
        interaction_type = args[0]
        # Process different interaction types
