import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class FillerType(Enum):
    GENERAL = "general"
    QUESTION = "question"
    SHORT = "short"
    THINKING = "thinking"


@dataclass
class FillerWord:
    text: str
    type: FillerType
    expression: Optional[str] = None


class FillerWords:
    """Manage conversation filler words and expressions."""

    def __init__(self):
        self._initialize_fillers()

    def _initialize_fillers(self):
        """Initialize filler word collections."""
        self.fillers: Dict[FillerType, List[FillerWord]] = {
            FillerType.GENERAL: [
                FillerWord("I understand...", FillerType.GENERAL, "nod"),
                FillerWord("I see...", FillerType.GENERAL, "nod"),
                FillerWord("Right...", FillerType.GENERAL, "nod"),
            ],
            FillerType.QUESTION: [
                FillerWord("Could you clarify...", FillerType.QUESTION, "thinking"),
                FillerWord(
                    "Let me make sure I understand...", FillerType.QUESTION, "thinking"
                ),
                FillerWord("Just to confirm...", FillerType.QUESTION, "thinking"),
            ],
            FillerType.SHORT: [
                FillerWord("Okay!", FillerType.SHORT, "wave"),
                FillerWord("Got it!", FillerType.SHORT, "thumbsup"),
                FillerWord("Sure!", FillerType.SHORT, "wave"),
            ],
            FillerType.THINKING: [
                FillerWord("Hmm...", FillerType.THINKING, "thinking"),
                FillerWord("Let me think...", FillerType.THINKING, "thinking"),
                FillerWord("One moment...", FillerType.THINKING, "thinking"),
            ],
        }

    def get_filler(self, filler_type: FillerType) -> FillerWord:
        """Get random filler word of specified type."""
        return random.choice(self.fillers[filler_type])

    def get_thinking_filler(self) -> FillerWord:
        """Get random thinking filler word."""
        return self.get_filler(FillerType.THINKING)

    def get_response_filler(self, is_question: bool = False) -> FillerWord:
        """Get appropriate response filler based on context."""
        filler_type = FillerType.QUESTION if is_question else FillerType.GENERAL
        return self.get_filler(filler_type)
