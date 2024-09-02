import logging
import random
from datetime import datetime
from typing import List

from blockchain.block import Block
from network.transaction import Transaction
from poa_messages.wrapped_block import WrappedBlock
from simulation.constants import EMPLOYEES_NUM, STAKEHOLDERS_NUM
from simulation.simulation import Simulation
from users.user import User

logger = logging.getLogger()


class Blockchain:
    """A class representing a PoT blockchain.

    It aggregates blocks and provides methods for adding new blocks and
    checking their validity.
    """

    def __init__(self, owner_name: str) -> None:
        self.owner_name = owner_name
        self.chain: List[Block] = []
        self.all_transactions: List[Transaction] = []

    def __str__(self) -> str:
        """Display the blockchain nicely."""
        blockchain_str = "\n" + "#" * 40
        for block in self.chain:
            blockchain_str += "\n" + self._format_block(block) + "#" * 40
        return blockchain_str

    def get_chain_length(self) -> int:
        return len(self.chain)

    def append_genesis_block(self) -> None:
        """Create the first (genesis) block."""
        user_a, user_b = User(name="Genesis A", balance=EMPLOYEES_NUM), User(
            name="Genesis B", balance=0
        )
        employees_names = Simulation().get_employees_names()
        new_block = Block(
            index=0,
            previous_hash="0".encode(),
            timestamp="1969-07-20 20:17:40",  # Apollo landing
            block_header=None,
            coinbase_transaction=None,
            transactions=[
                user_a.create_transaction(
                    amount=1, receiver=user_b, employee_name=employee_name
                )
                for employee_name in employees_names
            ],
            # create initial transactions for the first follow the coin procedure
            stakeholders_signatures=None,
        )
        self.add_block(new_block=new_block)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, new_block: Block) -> None:
        self.all_transactions.extend(
            new_block.transactions
        )  # transactions are aggregated in the blockchain object for easier accessing
        # in follow the coin procedure
        self.chain.append(new_block)

    def is_chain_valid(self) -> bool:
        """Check if the blockchain is valid.

        Returns:
            bool: True if the blockchain is valid, False otherwise.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def follow_the_coin(self, rand_source: bytes) -> List[str]:
        """Randomly selects a fixed number of stakeholders from the set of all
        employees who have participated in transactions on the blockchain.

        This method mocks behaviour of a real follow-the-coin procedure.
        It does not 'follow' the current owners (inheritors) of uniformly selected
        transactions, it selects some subset of all employee names.
        Since in this simulation all users and nodes are online all the time,
        there is no threat that selected stakeholder will be offline, as it is in
        typical permission-less blockchain networks.

        Args:
            rand_source (bytes): A source of randomness used to seed the random
            number generator.

        Returns:
            List[str]: A list of the selected stakeholders' (employees') names.
        """
        random.seed(rand_source)
        possible_stakeholders = set(
            [tx.employee_name for tx in self.all_transactions]
        )  # unique employee names
        selected_stakeholders = random.sample(possible_stakeholders, k=STAKEHOLDERS_NUM)
        return selected_stakeholders

    def append_fitted_wrapped_block(self, wrapped_block: WrappedBlock) -> None:
        """Appends a new block to the blockchain, after verifying that the
        parent block hash of the new block matches the hash of the latest block
        in the chain.

        Args:
            wrapped_block (WrappedBlock): The wrapped block to be added to the
            blockchain.
        """
        latest_block = self.get_latest_block()
        if wrapped_block.block_header.parent_block_hash != latest_block.hash:
            logger.warning(
                f"{self.owner_name} blockchain fork happened, "
                f"between block indexes {latest_block.index}:{latest_block.index + 1} "
                f"{latest_block.hash=} does not equal "
                f"{wrapped_block.block_header.parent_block_hash=}."
            )
        # translate wrapped block object to block object
        block = Block(
            index=latest_block.index + 1,
            previous_hash=latest_block.hash,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            block_header=wrapped_block.block_header,
            coinbase_transaction=wrapped_block.coinbase_transaction,
            transactions=wrapped_block.transactions,
            stakeholders_signatures=wrapped_block.stakeholders_signatures,
        )
        self.add_block(new_block=block)

    def _format_block(self, block: Block) -> str:
        formatted_block = f"Block #{block.index}\n"
        formatted_block += f"Employee Name {self.owner_name}\n"
        formatted_block += f"Timestamp: {block.timestamp}\n"
        formatted_block += f"Previous Hash: {block.previous_hash!r}\n"
        formatted_block += "Transactions:\n"
        formatted_block += "-" * 40 + "\n"

        for transaction in block.transactions:
            formatted_block += self._format_transaction(transaction)
            formatted_block += "-" * 40 + "\n"

        return formatted_block

    @staticmethod
    def _format_transaction(transaction: Transaction) -> str:
        formatted_transaction = f"ID: {transaction.id[:8]} | "
        formatted_transaction += f"Sender: {transaction.sender.name} | "
        formatted_transaction += f"Receiver: {transaction.receiver.name} | "
        formatted_transaction += f"Amount: {transaction.amount} | "
        formatted_transaction += f"Employee Name: {transaction.employee_name}\n"
        return formatted_transaction

    def count_transferred_coins(self) -> float:
        coin_count = 0.0
        for t in self.all_transactions:
            coin_count += t.amount
        return coin_count
