import logging
from typing import Tuple, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

logger = logging.getLogger()


def generate_key_pair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


def generate_key_pair_bytes() -> Tuple[bytes, bytes]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return encode_to_bytes(private_key), encode_to_bytes(public_key)


def encode_to_bytes(
    asymmetric_key: Union[Ed25519PrivateKey, Ed25519PublicKey]
) -> bytes:
    """Encodes an Ed25519PrivateKey or Ed25519PublicKey object to bytes using
    the PEM format. If the input is of type Ed25519PrivateKey, the output will
    be the private key bytes. If the input is of type Ed25519PublicKey, the
    output will be the public key bytes.

    Args:
        asymmetric_key (Union[Ed25519PrivateKey, Ed25519PublicKey]): The Ed25519 key
        object to encode.

    Returns:
        bytes: The encoded key bytes.

    Raises:
        ValueError: If the input is not of type Ed25519PrivateKey or Ed25519PublicKey.
    """
    match asymmetric_key:
        case Ed25519PrivateKey():  # type:ignore[misc]
            return asymmetric_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        case Ed25519PublicKey():  # type:ignore[misc]
            return asymmetric_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        case _:
            raise ValueError(
                "Only arguments of type Ed25519PrivateKey or Ed25519PublicKey are "
                "expected."
            )


def decode_public_key_from_bytes(
    asymmetric_public_key_bytes: bytes,
) -> Ed25519PublicKey:
    """Decodes a public key from bytes using the Ed25519 algorithm.

    Args:
        asymmetric_public_key_bytes: The public key bytes to decode.

    Returns:
        Ed25519PublicKey: The decoded public key.
    """
    return serialization.load_pem_public_key(asymmetric_public_key_bytes)


def sign_message(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
    """Sign a message.

    Args:
        private_key: The private key to sign the message with.
        message: The message to sign.

    Returns:
        bytes: The signature of the message.
    """
    signature = private_key.sign(message)
    return signature


def verify_signature(
    public_key: Union[Ed25519PublicKey, bytes], message: bytes, signature: bytes
) -> bool:
    """Verify a signature.

    Args:
        public_key: The public key to verify the signature with.
        message: The message to verify.
        signature: The signature to verify.

    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    if isinstance(public_key, bytes):
        public_key = decode_public_key_from_bytes(public_key)
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        logger.error(f"Signature verification failed for {message!r}.")
        return False


def count_leading_zeros(bytes_obj: bytes) -> int:
    """Count the number of leading zeros in a byte string.

    Used for difficulty functions of PoS and PoA.

    Args:
        bytes_obj: The byte string to count leading zeros in.

    Returns:
        int: The number of leading zeros in the byte string.
    """
    bit_string = "".join(format(byte, "08b") for byte in bytes_obj)
    leading_zeros_num = len(bit_string) - len(bit_string.lstrip("0"))
    return leading_zeros_num
