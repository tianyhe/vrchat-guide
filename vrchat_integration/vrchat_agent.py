from osc.handler import VRChatOSCHandler
from pythonosc.udp_client import SimpleUDPClient
from voice.manager import VRChatVoiceManager
import asyncio
from worksheets.agent import Agent
   

from vrchat_guide.vrchatbot import (
        update_profile,
        add_event,
        prompt_dir,
        suql_knowledge,
        suql_parser,
)


class VRChatVoiceManager:
    def __init__(self, ip="127.0.0.1", port=9001):
        self.osc_client = SimpleUDPClient(ip, port)
        
    async def send_voice_command(self, text):
        # Send TTS commands via OSC
        self.osc_client.send_message("/avatar/parameters/Speech", text)


class VRChatAgent:
    def __init__(self, bot):
        self.bot = bot
        self.dlg_history = []  # Store dialog history in VRChatAgent
        self.osc_handler = VRChatOSCHandler(self.bot)
        self.voice_manager = VRChatVoiceManager()
        
    async def start(self):
        # Start OSC server
        server_task = asyncio.create_task(
            asyncio.start_server(
                self.osc_handler.server.serve_forever,
                self.osc_handler.server.server_address[0],
                self.osc_handler.server.server_address[1]
            )
        )
        
        # Initialize conversation
        if len(self.dlg_history) == 0:
            await self.voice_manager.send_voice_command(self.bot.starting_prompt)

        # Start conversation loop
        while True:
            try:
                # Handle VRChat interactions and voice input through OSC handlers
                await asyncio.sleep(0.1)  # Prevent CPU hogging
            except Exception as e:
                print(f"Error in VRChat agent loop: {e}")


def main():
    bot = Agent(
            botname="VRChatBot",
            description="You an assistant at VRChat and help users with all their queries related to finding events and adding them to their calendar. You can search for events, ask me anything about the event and add the interested one to calendar",
            prompt_dir=prompt_dir,
            starting_prompt="""Hello! I'm your VRChat Guide. I can help you with:
- Create / Update your VRChat profile with your preferences
- Explore / Learn about upcoming VRChat events and add them to your calendar
- Asking me any question related to the details of the VRChat events I purposed

How can I help you today?""",
            args={},
            api=[update_profile, add_event],
            knowledge_base=suql_knowledge,
            knowledge_parser=suql_parser,
        )  # Your existing VRChat guide bot
    vrchat_agent = VRChatAgent(bot)
    asyncio.run(vrchat_agent.start())

if __name__ == "__main__":
    main()
