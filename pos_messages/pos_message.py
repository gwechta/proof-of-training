from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from blockchain.blockchain_utils import pos_td_difficulty, pos_bh_difficulty
from simulation.hashable_serializable_message import HashSignSerialPoTMessage
from model.model import ExampleModel
from network.cryptographic_utils import count_leading_zeros


@dataclass
class PoSMessage(HashSignSerialPoTMessage):
    """A class representing a PoS message.

    It is used as an abstraction of PoS type messages.
    """

    id_s: str
    timestamp: str

    def __init__(
        self, model: ExampleModel, coinstake: float, public_key: Ed25519PublicKey
    ):
        super().__init__(model=model, public_key=public_key)
        self.coinstake = coinstake
        self.signature = None

    def check_meeting_pos_td_difficulty(self) -> bool:
        return count_leading_zeros(self.calculate_hash()) >= pos_td_difficulty(
            coinstake=self.coinstake
        )

    def check_meeting_pos_bh_difficulty(self) -> bool:
        return count_leading_zeros(self.calculate_hash()) >= pos_bh_difficulty(
            coinstake=self.coinstake
        )
