import os
import time
import asyncio
import random
import argparse
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime

import torch
from pythonosc import udp_client
from loguru import logger

from vrchat_guide.vrchatbot import (
    update_profile,
    add_event,
    prompt_dir,
    suql_knowledge,
    suql_parser,
)
from vrchat_guide.vrchat_interface.audio import (
    STTService,
    TTSService,
    AudioService,
    AudioDeviceManager,
)
from vrchat_guide.vrchat_interface.osc import VRChatOSC
from vrchat_guide.vrchat_interface.filler_words import FillerWords, FillerType
from vrchat_guide.metrics.utils import MetricsManager
from worksheets.agent import Agent
from worksheets.chat import generate_next_turn


class VRChatInterface:
    """Interface for integrating the agent with VRChat.

    Handles coordination between:
    - Speech-to-text (STT) for user input
    - Text-to-speech (TTS) for agent responses
    - OSC communication with VRChat
    - Filler words and expressions during responses
    - Metrics tracking
    """

    def __init__(self):
        # Device setup
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.metrics = MetricsManager(
            metrics_dir="logs/metrics",
            session_timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.running = True

        # Initialize core services
        self._init_audio_services()
        self._init_vrchat_services()

        # Paths
        self.audio_path = Path("./speech/current_conversation.wav")
        self.audio_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_audio_services(self):
        """Initialize TTS and STT services."""
        try:
            # Initialize audio manager first
            self.audio_manager = AudioDeviceManager()
            self.mic_channel = self.audio_manager.get_virtual_mic_channel()

            if self.mic_channel is None:
                raise RuntimeError("Could not find virtual microphone channel")

            # Initialize services
            self.tts = TTSService(self.device)
            self.stt = STTService(self.device)
            self.audio_service = AudioService()  # Reference the audio service

            logger.info(
                f"Audio services initialized successfully (mic channel: {self.mic_channel})"
            )

        except Exception as e:
            logger.error(f"Failed to initialize audio services: {str(e)}")
            raise RuntimeError(f"Audio services initialization failed: {str(e)}")

    def _init_vrchat_services(self):
        """Initialize VRChat-related services."""
        try:
            self.vrc_client = self._setup_osc_client()
            self.osc = VRChatOSC(self.vrc_client)
            self.filler_words = FillerWords()
        except Exception as e:
            logger.error(f"Failed to initialize VRChat services: {e}")
            raise RuntimeError("VRChat services initialization failed")

    @staticmethod
    def _setup_osc_client() -> udp_client.SimpleUDPClient:
        """Setup OSC client for VRChat communication."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--ip", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=9000)
        args = parser.parse_args()
        return udp_client.SimpleUDPClient(args.ip, args.port)

    async def get_user_input(self) -> Optional[str]:
        """Get user input via speech-to-text with error handling."""
        with self.metrics.measure_latency("stt"):
            try:
                audio_data = await self.stt.listen_and_record(self.audio_path)
                transcript = await self.stt.transcribe(audio_data)
                if not transcript:
                    await self._handle_failed_input()
                return transcript
            except Exception as e:
                logger.error(f"Error getting user input: {e}")
                await self._handle_failed_input()
                return None

    async def _handle_failed_input(self):
        """Handle failed speech input gracefully."""
        filler = self.filler_words.get_filler(FillerType.QUESTION)
        await self.send_agent_response(
            "I'm sorry, I couldn't hear that clearly. Could you repeat that?",
            filler.expression,
        )

    async def send_agent_response(self, text: str, expression: Optional[str] = None):
        """Send agent response with coordinated TTS, OSC, and expressions."""
        with self.metrics.measure_latency("agent_response"):
            try:
                # Send thinking indicator while processing
                thinking_filler = self.filler_words.get_thinking_filler()
                await self.osc.send_chatbox(thinking_filler.text)
                if thinking_filler.expression:
                    await self.osc.send_expression(thinking_filler.expression)

                # Split response into chunks and coordinate TTS/OSC
                await self._send_coordinated_response(text, expression)

            except Exception as e:
                logger.error(f"Error sending agent response: {e}")
                raise

    async def _send_coordinated_response(
        self, text: str, expression: Optional[str] = None
    ):
        """Coordinate TTS and OSC message chunking."""
        chunks = self.osc._split_into_chunks(text)

        for i, chunk in enumerate(chunks):
            if not self.running:
                break

            # Add continuation indicators
            if i > 0:
                chunk = "... " + chunk
            if i < len(chunks) - 1:
                chunk = chunk + " ..."

            # Coordinate OSC and TTS
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.osc.send_chatbox(chunk))
                tg.create_task(self.tts.speak(chunk, self.mic_channel))

            # Send expression if provided
            if expression and i == len(chunks) - 1:
                await self.osc.send_expression(expression)

            # Delay between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)

    async def run(self):
        """Run the VRChat interface with proper initialization and cleanup."""
        print("Initializing VRChat interface...")
        try:
            # Start session
            self.metrics.logger.start_session(user_id="vrchat_user")

            # Add debug logging for agent initialization
            logger.info("Initializing agent...")
            agent = Agent(
                botname="VRChatBot",
                description="VRChat assistant helping with events and calendar",
                prompt_dir=prompt_dir,
                starting_prompt="Hello! I'm VRChat Guide. I can help you get the best experience possible. How should I address you?",
                args={"device": self.device},
                api=[update_profile, add_event],
                knowledge_base=suql_knowledge,
                knowledge_parser=suql_parser,
            ).load_from_gsheet("1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU")

            logger.info("Agent initialized successfully")

            print("Prompts directory:", prompt_dir)

            # Add debug for response sending
            greeting_filler = self.filler_words.get_filler(FillerType.SHORT)
            logger.info(f"Sending greeting with filler: {greeting_filler.expression}")
            await self.send_agent_response(
                agent.starting_prompt, greeting_filler.expression
            )

            while self.running:
                # Start listening with cue
                await self.audio_service.start_listening()  # Use audio_service from interface

                user_input = await self.get_user_input()
                if user_input:
                    # Stop listening
                    await self.audio_service.stop_listening()  # Stop listening

                    logger.info(f"Received user input: {user_input}")
                    response_filler = self.filler_words.get_response_filler(
                        "?" in user_input
                    )
                    logger.info(
                        f"Sending response with filler: {response_filler.expression}"
                    )
                    # response = await agent.get_response(user_input)
                    await generate_next_turn(user_input, agent)
                    response = agent.dlg_history[-1].system_response
                    await self.send_agent_response(response, response_filler.expression)

                    # Small pause before next turn
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.exception(f"Critical error in VRChat interface: {e}")
        finally:
            # End session
            self.metrics.logger.end_session()
            await self._cleanup()

    async def handle_interrupt(self):
        """Handle user interruption."""
        if self.tts.is_speaking:
            self.tts.is_speaking = False
            filler = self.filler_words.get_filler(FillerType.SHORT)
            await self.send_agent_response("Oh, please go ahead.", filler.expression)

    async def _cleanup(self):
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up VRChat interface...")
        self.osc.stop_message_chain()
        if hasattr(self, "audio_service"):
            await self.audio_service.stop_listening()  # Add this line
        if self.audio_path.exists():
            self.audio_path.unlink()


async def main():
    interface = VRChatInterface()  # Assuming this is your interface class name
    try:
        await interface.run()
    except KeyboardInterrupt:
        print("\nShutting down VRChat interface...")
    finally:
        if hasattr(interface, "cleanup"):
            await interface.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
