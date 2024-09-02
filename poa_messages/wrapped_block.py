from dataclasses import dataclass
from typing import List

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from simulation.hashable_serializable_message import HashSignSerialPoTMessage
from model.model import ExampleModel
from users.coinbase_user import CoinbaseUser
from network.cryptographic_utils import verify_signature, decode_public_key_from_bytes
from network.transaction import Transaction
from users.user import User
from poa_messages.stakeholder_signature import StakeholderSignature
from pos_messages.block_header import BlockHeader


@dataclass
class WrappedBlock(HashSignSerialPoTMessage):
    """A class representing a wrapped block in the PoT consensus algorithm."""

    id_s: str
    timestamp: str

    def __init__(
        self,
        employee_user: User,
        model: ExampleModel,
        public_key: Ed25519PublicKey,
        transactions: List[Transaction],
        stakeholders_signatures: List[StakeholderSignature],
        block_header: BlockHeader,
    ) -> None:
        super().__init__(model=model, public_key=public_key)
        coinbase_user = CoinbaseUser(block_index=block_header.block_index)
        self.block_header = block_header
        self.coinbase_transaction = coinbase_user.create_transaction(
            receiver=employee_user
        )  # create coinbase transaction for the employee user
        self.transactions = transactions
        self.stakeholders_signatures = stakeholders_signatures
        self.signature = None

    def verify_stakeholder_signatures(self) -> bool:
        """Verify the signatures of all stakeholders in the wrapped block.

        Returns:
            bool: True if all signatures are valid, False otherwise.
        """
        for ss in self.stakeholders_signatures:
            public_key = decode_public_key_from_bytes(ss.public_key)
            signature = ss.signature
            message = ss.block_header.dumps_without_sig()
            if (
                verify_signature(
                    public_key=public_key, message=message, signature=signature
                )
                is False
            ):
                return False
        return True
