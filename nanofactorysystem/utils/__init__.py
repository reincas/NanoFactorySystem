import math


def n_zero_padding_required(n:int) -> int:
    return math.ceil(math.log(n + 1))
