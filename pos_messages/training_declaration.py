from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from model.model import ExampleModel
from pos_messages.pos_message import PoSMessage


class TrainingDeclaration(PoSMessage):
    """A class representing a training declaration in the PoT consensus
    mechanism."""

    def __init__(
        self,
        model: ExampleModel,
        training_secret_commitment: bytes,
        coinstake: float,
        public_key: Ed25519PublicKey,
    ):
        super().__init__(model, coinstake, public_key)
        self.training_secret_commitment = training_secret_commitment
        self.h_s = model.get_hashed_serialization()
