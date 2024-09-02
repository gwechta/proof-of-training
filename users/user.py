from dataclasses import dataclass
from typing import Optional

from faker import Faker

from network.cryptographic_utils import generate_key_pair_bytes
from network.transaction import Transaction

faker = Faker()  # generating random names


@dataclass
class User:
    """Class for representing a user object.

    In contrast to real blockchain networks *user*'s behaviour to
    simplify simulation is controlled by UsersPuppeteer process, and
    thus users are jus object and not processes.
    """

    name: str
    balance: float

    def __init__(self, name: str = None, balance: float = 0):
        self.name = (
            name if name is not None else faker.name()
        )  # allow for custom name, if not provided, generate random name
        self.balance = balance
        self.private_key, self.public_key = generate_key_pair_bytes()

    def create_transaction(
        self, amount: float, receiver: "User", employee_name: Optional[str] = None
    ) -> Transaction:
        """Create a transaction between two users."""
        return Transaction(
            sender=self, amount=amount, receiver=receiver, employee_name=employee_name
        )
