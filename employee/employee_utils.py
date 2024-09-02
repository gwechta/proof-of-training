import logging
from typing import Tuple, Type

from model.model import ExampleModel, ExampleDataset

logger = logging.getLogger()


def select_stage() -> Tuple[Type[ExampleModel], Type[ExampleDataset]]:
    """Select the next stage.

    This function mocks the node's internal logic of selecting the next stage.

    Returns:
        Tuple[Type[ExampleModel], Type[ExampleDataset]]: The selected stage.
    """
    return ExampleModel, ExampleDataset
