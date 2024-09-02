import logging
from typing import List, Dict, Union

from pos_messages.training_declaration import TrainingDeclaration

logger = logging.getLogger()


class TrainingDeclarationsBook:
    """A class for managing training declaration for a given training stage.

    Each employee handles his own book.
    """

    def __init__(self, owner_name: str) -> None:
        self.book: Dict[str, Dict[str, Union[bool, List[TrainingDeclaration]]]] = {}
        self.owner_name = owner_name

    def add_training_declaration_to_book(self, td: TrainingDeclaration) -> None:
        """Add a training declaration to the book.

        Args:
            td: The training declaration to be added.
        """
        id_s = td.id_s
        if id_s not in self.book:
            self.book[id_s] = {"open": True, "training_declarations": []}

        if self.book[id_s]["open"] is False:
            logger.debug(
                f"{self.owner_name} in TD book {id_s} is closed, {td} will "
                f"not be appended."
            )
            return

        self.book[id_s]["training_declarations"].append(td)
        logger.debug(
            f"{self.owner_name} has {self.get_training_declarations_num(id_s)} "
            f"training_declarations."
        )

    def get_training_declarations(
        self,
        id_s: str,
    ) -> List[TrainingDeclaration]:
        """Get the list of training declarations for a given stage id.

        Args:
            id_s: The training stage id.

        Returns:
            The list of training declarations for a given stage id.
        """
        return self.book[id_s]["training_declarations"]  # type: ignore

    def get_training_declarations_num(self, id_s: str) -> int:
        """Get the number of training declarations for a given stage id.

        Args:
            id_s: The training stage id.

        Returns:
            The number of training declarations for a given stage id.
        """
        try:
            return len(self.book[id_s]["training_declarations"])
        except KeyError:
            return 0

    def close(self, id_s: str) -> None:
        """Close the book for a given stage id.

        Args:
            id_s: The training stage id.
        """
        self.book[id_s]["open"] = False
