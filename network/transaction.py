from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from users.user import User


@dataclass
class Transaction:
    """Class for representing transaction between two users."""

    sender: User
    amount: float
    receiver: User

    def __init__(self, sender: User, amount: float, receiver: User, employee_name: str):
        self.sender = sender
        self.amount = amount
        self.receiver = receiver
        self.employee_name = employee_name
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = (
            str(sender) + str(amount) + str(receiver) + self.timestamp
        ).encode()  # used for calculating the id of the transaction
        self.id = hashlib.sha256(data).hexdigest()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Transaction):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

    def set_employee_name(self, employee_name: str) -> None:
        self.employee_name = employee_name
