import logging


def init_logger(
    file_log_level: int = logging.DEBUG, console_log_level: int = logging.INFO
) -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s]: %(message)s")
    file_handler = logging.FileHandler("pot_sim.log", mode="w", encoding="utf-8")
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
