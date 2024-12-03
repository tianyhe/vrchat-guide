from typing import Optional, Dict, List
from pythonosc import udp_client
import asyncio
import threading
from loguru import logger


class VRChatOSC:
    """Handle VRChat OSC protocol communication."""

    VRCHAT_CHAR_LIMIT = 144  # VRChat character limit

    def __init__(self, client: udp_client.SimpleUDPClient):
        self.client = client
        self.chatbox_address = "/chatbox/input"
        self.typing_address = "/chatbox/typing"
        self.expression_address = "/avatar/parameters/"
        self.stop_flag = False
        self._setup_expressions()

    def _setup_expressions(self):
        """Setup default VRChat expressions/gestures."""
        self.expressions: Dict[str, str] = {
            "wave": "Wave",
            "point": "Point",
            "clap": "Clap",
            "dance": "Dance",
        }

    def _count_utf16_units(self, text: str) -> int:
        """Count UTF-16 code units in text."""
        return len(text.encode("utf-16le")) // 2

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks respecting word boundaries."""
        if self._count_utf16_units(text) <= self.VRCHAT_CHAR_LIMIT:
            return [text]

        words = text.split()
        chunks = []
        current_chunk = ""

        for i, word in enumerate(words):
            # Handle long words
            while self._count_utf16_units(word) > self.VRCHAT_CHAR_LIMIT - 6:
                part = word[: self.VRCHAT_CHAR_LIMIT - 6]
                word = word[self.VRCHAT_CHAR_LIMIT - 6 :]
                chunks.append(current_chunk + " " + part if current_chunk else part)
                current_chunk = word

            # Check if adding word exceeds limit
            potential_chunk = current_chunk + " " + word if current_chunk else word
            if i != len(words) - 1:
                potential_chunk_len = self._count_utf16_units(
                    potential_chunk + " ... ..."
                )
            else:
                potential_chunk_len = self._count_utf16_units(potential_chunk + " ...")

            if potential_chunk_len <= self.VRCHAT_CHAR_LIMIT:
                current_chunk = potential_chunk
            else:
                chunks.append(current_chunk)
                current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def send_chatbox(self, message: str, typing_animation: bool = True):
        """Send message to VRChat chatbox with chunking support."""
        try:
            chunks = self._split_into_chunks(message)
            self.stop_flag = False

            for i, chunk in enumerate(chunks):
                if self.stop_flag:
                    break

                # Add continuation indicators
                if i > 0:
                    chunk = "... " + chunk
                if i < len(chunks) - 1:
                    chunk = chunk + " ..."

                # Show typing for first chunk or between chunks
                if typing_animation:
                    await self._show_typing_animation()

                self.client.send_message(self.chatbox_address, [chunk, True])

                # Delay between chunks
                if i < len(chunks) - 1:
                    await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Error sending message to VRChat: {e}")
            raise

    async def send_expression(self, expression: str):
        """Send expression/gesture to VRChat avatar."""
        try:
            if expression in self.expressions:
                address = self.expression_address + self.expressions[expression]
                self.client.send_message(address, 1.0)
                await asyncio.sleep(0.5)
                self.client.send_message(address, 0.0)
        except Exception as e:
            logger.error(f"Error sending expression to VRChat: {e}")

    async def _show_typing_animation(self, duration: float = 1.0):
        """Show typing animation in VRChat."""
        try:
            self.client.send_message(self.typing_address, True)
            await asyncio.sleep(duration)
            self.client.send_message(self.typing_address, False)
        except Exception as e:
            logger.warning(f"Typing animation failed: {e}")

    def stop_message_chain(self):
        """Stop sending remaining message chunks."""
        self.stop_flag = True
