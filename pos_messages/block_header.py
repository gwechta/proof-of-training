from __future__ import annotations

from typing import List
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from model.model import ExampleModel
from network.cryptographic_utils import encode_to_bytes, verify_signature
from pos_messages.pos_message import PoSMessage
from pos_messages.training_declaration import TrainingDeclaration

if TYPE_CHECKING:
    from blockchain.blockchain import Blockchain


class BlockHeader(PoSMessage):
    """A class representing a block header in the PoT consensus mechanism."""

    def __init__(
        self,
        model: ExampleModel,
        blockchain: Blockchain,
        training_secret: bytes,
        coinstake: float,
        public_key: Ed25519PublicKey,
        training_declarations: List[TrainingDeclaration],
    ) -> None:
        super().__init__(model, coinstake, public_key)
        self.parent_block_hash = blockchain.get_latest_block().calculate_hash()
        self.block_index = blockchain.get_latest_block().index + 1
        self.training_secret = training_secret
        self.public_key = encode_to_bytes(public_key)
        self.training_declarations = training_declarations

    def check_included_training_declarations(self) -> bool:
        """Check if all training declarations included in the block header are
        sound.

        Returns:
             bool: True if all training declarations are sound, False otherwise.
        """
        for td in self.training_declarations:
            training_secret_commitment = td.training_secret_commitment  # signature
            public_key = td.public_key
            if (
                verify_signature(
                    public_key=public_key,
                    message=self.training_secret,
                    signature=training_secret_commitment,
                )
                is False
            ):
                return False
        return True
