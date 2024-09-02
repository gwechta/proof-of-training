import logging
import random
from multiprocessing import connection, Process
from time import sleep

from network.message import Message, MessageType
from simulation.constants import MAX_TRANSACTIONS_NUM
from users.user import User

logger = logging.getLogger()


class UsersPuppeteer(Process):
    """A class that represents a process that generates transactions between
    users."""

    def __init__(self, connection_up: connection.Connection, users_num: int) -> None:
        super().__init__(target=self.maneuver_users)
        self.connection = connection_up
        self.users_num = users_num
        self.users = [
            User(balance=random.randint(10, 100)) for _ in range(self.users_num)
        ]

    def maneuver_users(self) -> None:
        """Randomly select two users from the list of users and create a
        transaction between them.

        Send the transaction to the Broadcaster. Repeat the process
        until the `MAX_TRANSACTIONS_NUM` is reached.
        """
        logger.info(f"{self.name} is running.")
        transactions_num = 0
        while transactions_num < MAX_TRANSACTIONS_NUM:
            sleep(random.random())
            sample = random.sample(self.users, 2)
            sender, receiver = sample[0], sample[1]
            transaction = sender.create_transaction(
                receiver=receiver, amount=random.randint(1, 10)
            )
            self.connection.send(
                Message(msg_type=MessageType.TRANSACTION, content=transaction)
            )
            logger.debug(f"{self.name} sent {transaction}.")
            transactions_num += 1
