from dataclasses import dataclass
from typing import List

from worksheets.environment import GenieContext


@dataclass
class CurrentDialogueTurn:
    """Represents a single turn in the dialogue."""

    # User's utterance in natural language
    user_utterance: str = None

    # User's target semantic representation
    user_target_sp: str = None

    # Final user target after rewrites
    user_target: str = None

    # System's response to the user
    system_response: str = None

    # System's target action
    system_target: str = None

    # System Dialogue acts
    system_action: List[str] = None

    # Flag to indicate if the user is asking a question
    user_is_asking_question: bool = False

    # Context for the current dialogue turn
    context: GenieContext = None

    # Global context for the dialogue
    global_context: GenieContext = None

    # User's target SUQL query
    user_target_suql: str = None
