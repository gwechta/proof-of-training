import logging
from typing import List, Dict, Union, Optional

from poa_messages.stakeholder_signature import StakeholderSignature

logger = logging.getLogger()


class StakeholderSignaturesBook:
    """A class for managing stakeholder signatures for a given block header.

    Each employee handles his own book.
    """

    def __init__(self, owner_name: str) -> None:
        """Initialize the StakeholderSignaturesBook.

        Args:
            owner_name: The name of the owner of the book.
        """
        self.book: Dict[
            str,
            Dict[
                str,
                Union[
                    bool,
                    Dict[
                        str,
                        Dict[str, Union[List[StakeholderSignature], Optional[bool]]],
                    ],
                ],
            ],
        ] = {}
        self.owner_name = owner_name

    def add_signature_to_book(
        self, ss: StakeholderSignature, roy: Optional[bool] = None
    ) -> None:
        """Add a signature to the StakeholderSignaturesBook.

        Args:
            ss: The signature to be added.
            roy: Flag determining being Roy stakeholder. Defaults to None.
        """
        id_s, id_bh = ss.block_header.id_s, ss.block_header.get_id()
        if id_s not in self.book:
            self.book[id_s] = {
                "open": True,
                "sh_info": {id_bh: {"sigs": [], "roy": roy}},
            }
        if id_bh not in self.book[id_s]["sh_info"]:
            self.book[id_s]["sh_info"][id_bh] = {"sigs": [], "roy": roy}

        if self.book[id_s]["open"] is False:
            logger.debug(
                f"{self.owner_name} in SS book {id_s}:{id_bh} is closed, {ss} will "
                f"not be appended."
            )
            return

        self.book[id_s]["sh_info"][id_bh]["sigs"].append(ss)

    def get_signatures_for_block_header(
        self, id_s: str, id_bh: str
    ) -> List[StakeholderSignature]:
        """Get the signatures for a given block header.

        Args:
            id_s: The training stage id.
            id_bh: The block header id.

        Returns:
            List[StakeholderSignature]: The signatures for the given block header.
        """
        try:
            return self.book[id_s]["sh_info"][id_bh]["sigs"]  # type: ignore
        except KeyError:
            return []

    def get_signatures_num(self, id_s: str, id_bh: str) -> int:
        """Get the number of signatures for a given block header.

        Args:
            id_s: The training stage id.
            id_bh: The block header id.

        Returns:
            int: The number of signatures for the given block header.
        """
        try:
            return len(self.book[id_s]["sh_info"][id_bh]["sigs"])
        except KeyError:
            return 0

    def close(self, id_s: str) -> None:
        """Close the book for a given stakeholder.

        It should happen after the block header for `id_s` was published.

        Args:
            id_s: The training stage id.
        """
        try:
            self.book[id_s]["open"] = False
        except KeyError:
            return

    def is_open(self, id_s: str) -> bool:
        """Check whether the book is open for a given stakeholder.

        Args:
            id_s: The training stage id.

        Returns:
            bool: True if the book is open, False otherwise.
        """
        if id_s in self.book:
            return self.book[id_s]["open"]  # type: ignore
        else:
            return True
