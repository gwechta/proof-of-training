from dataclasses import dataclass

from pos_messages.block_header import BlockHeader


@dataclass
class StakeholderSignature:
    """Class representing a signature of a stakeholder on a block header."""

    block_header_id: str

    def __init__(self, block_header: BlockHeader, public_key: bytes, signature: bytes):
        self.block_header = block_header
        self.block_header_id = (
            self.block_header.get_id()
        )  # just for dataclass representation
        self.public_key = public_key
        self.signature = signature
