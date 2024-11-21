from enum import Enum

class AVATAR_DATA(Enum):
    AVATAR_EXPRESSION_MAP = "Avatar Expressions Map"
    AVATAR_ACTION_MAP = "Avatar Actions Map"
    AVATAR_VOICE = "Avatar Voice"

class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2

class AGENT_MODE(Enum):
    NORMAL = 1
    EVENT = 2
    RESEARCH = 3
    DEBATE = 4
    PREDEFINED_RESEARCH = 5