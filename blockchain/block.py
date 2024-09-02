import hashlib
from dataclasses import dataclass
from typing import List, Optional

from network.transaction import Transaction
from poa_messages.stakeholder_signature import StakeholderSignature
from pos_messages.block_header import BlockHeader


@dataclass
class Block:
    """A class representing a PoT blockchain block."""

    previous_hash: bytes
    hash: bytes

    def __init__(
        self,
        index: int,
        previous_hash: bytes,
        timestamp: str,
        block_header: Optional[BlockHeader],
        coinbase_transaction: Optional[Transaction],
        transactions: List[Transaction],
        stakeholders_signatures: Optional[List[StakeholderSignature]],
    ):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.block_header = block_header
        self.coinbase_transaction = coinbase_transaction
        self.transactions = transactions
        self.stakeholders_signatures = stakeholders_signatures
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> bytes:
        """Calculate the hash of the block."""
        data = (
            str(self.index)
            + self.previous_hash.hex()
            + self.timestamp
            + str(self.block_header)
            + str(self.coinbase_transaction)
            + "".join(str(transaction) for transaction in self.transactions)
            if self.transactions
            else ""
            + "".join(str(signature) for signature in self.stakeholders_signatures)
            if self.stakeholders_signatures
            else ""
        )
        return hashlib.sha256(data.encode("utf-8")).digest()
