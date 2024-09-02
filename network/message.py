from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class MessageType(Enum):
    """Enum class representing the type of messages that can be sent over the
    network."""

    TRANSACTION = auto()
    BLOCK_HEADER = auto()
    STAKEHOLDER_SIGNATURE = auto()
    WRAPPED_BLOCK = auto()
    TRAINING_DECLARATION = auto()
    EMPLOYEE_ALIVE = auto()
    EMPLOYEE_FINISHED = auto()
    RESULT_LOCAL_BLOCKCHAIN = auto()


@dataclass
class Message:
    """A class incorporating MessageType and its content."""

    msg_type: MessageType
    content: Any

    def __init__(self, msg_type: MessageType, content: Any = None):
        self.msg_type = msg_type
        self.content = content
