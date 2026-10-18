"""精确计算连分数及其渐近分数。"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


# 【自己实现】使用连续整除计算连分数系数。
def continued_fraction(numerator: int, denominator: int) -> list[int]:

    coefficients: list[int] = []
    a, b = numerator, denominator

    # 使用欧几里得除法依次得到连分数系数。
    while b != 0:
        quotient, remainder = a // b, a % b
        coefficients.append(quotient)
        a, b = b, remainder

    return coefficients


# 【自己实现】从右向左计算每个连分数前缀对应的渐近分数。
def convergents(coefficients: Iterable[int]) -> Iterator[tuple[int, int]]:
    """依次生成每个连分数前缀对应的 (分子, 分母)。"""

    values = list(coefficients)

    # 每次取一个更长的前缀，得到一个新的渐近分数。
    for end in range(1, len(values) + 1):
        prefix = values[:end]

        # 从最右边的系数开始，把它看成 coefficient/1。
        numerator = prefix[-1]
        denominator = 1

        # 从右向左计算 coefficient + 1/current_value。
        for coefficient in reversed(prefix[:-1]):
            numerator, denominator = (
                coefficient * numerator + denominator,
                numerator,
            )
        # 每次 yield 一个新的渐近分数 (分子, 分母)，给调用者使用。
        yield numerator, denominator
