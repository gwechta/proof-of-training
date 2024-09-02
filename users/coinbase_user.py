import math

from network.transaction import Transaction
from users.user import User


class CoinbaseUser(User):
    """Class for representing a coinbase user.

    A special type of user that is used as sender of coinbase (block
    building) rewards.
    """

    def __init__(self, block_index: int):
        super().__init__(name="Coinbase User")
        self.block_index = block_index

    def create_transaction(self, receiver, **kwargs) -> Transaction:  # type: ignore
        return super().create_transaction(
            amount=self.coinbase_reward(self.block_index),
            receiver=receiver,
            employee_name=receiver.name,
        )

    @staticmethod
    def coinbase_reward(n: int) -> float:
        """Calculate coinbase reward amount."""
        return 1000 - 999 * (math.sqrt(n) / (math.sqrt(n) + 10))
