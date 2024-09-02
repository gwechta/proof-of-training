import copy
import hashlib
import pickle
from datetime import datetime
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
    Ed25519PrivateKey,
)

from model.model import ExampleModel
from network.cryptographic_utils import (
    encode_to_bytes,
    sign_message,
)


class HashSignSerialPoTMessage:
    """This class offers abstraction and a common interface for messages that
    are hashable, signable, serializable."""

    def __init__(self, model: ExampleModel, public_key: Ed25519PublicKey):
        self.id_m = model.id
        self.id_s = model.get_id_s()
        self.public_key = encode_to_bytes(public_key)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.signature: Optional[bytes] = None

    def dumps_without_sig(self) -> bytes:
        signature_tmp = copy.deepcopy(self.signature)
        self.signature = None
        data = pickle.dumps(self)
        self.signature = signature_tmp
        return data

    def calculate_hash(self) -> bytes:
        data = self.dumps_without_sig()
        return hashlib.sha256(data).digest()

    def sign(self, private_key: Ed25519PrivateKey) -> None:
        signature = sign_message(private_key=private_key, message=pickle.dumps(self))
        self.set_signature(signature)

    def set_signature(self, signature: bytes) -> None:
        self.signature = signature

    def set_timestamp(self, timestamp: str) -> None:
        self.timestamp = timestamp

    def get_id(self) -> str:
        return self.calculate_hash().hex()[:8]
