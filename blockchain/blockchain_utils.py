import math


def pos_td_difficulty(coinstake: float) -> float:
    return 256 - math.log2(coinstake)  # example Training Declaration PoS difficulty


def pos_bh_difficulty(coinstake: float) -> float:
    return 256 - math.log2(coinstake)  # example Block Header PoS difficulty
