"""精确计算连分数及其渐近分数。"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


# 【自己实现】使用连续整除计算连分数系数。
def continued_fraction(numerator: int, denominator: int) -> list[int]:
    """返回一个有理数的简单连分数系数。

    计算过程只使用整数除法和余数，不会把有理数转换成浮点数。
    denominator 必须为正数。例如，43/19 得到 [2, 3, 1, 4]。
    """

    if denominator <= 0:
        raise ValueError("分母 denominator 必须为正数")

    coefficients: list[int] = []
    a, b = numerator, denominator

    # 这里执行的正是欧几里得算法中的商和余数步骤。
    # 最终余数变为零，表示该有理数的连分数展开已经结束。
    while b != 0:
        quotient, remainder = divmod(a, b)
        coefficients.append(quotient)
        a, b = b, remainder

    return coefficients


# 【自己实现】按照递推公式依次计算渐近分数。
def convergents(coefficients: Iterable[int]) -> Iterator[tuple[int, int]]:
    """依次生成每个连分数前缀对应的 (分子, 分母)。

    如果一个前缀以系数 a 结尾，其分子和分母满足相同的递推关系：

    p = a*p_prev1 + p_prev2
    q = a*q_prev1 + q_prev2

    本函数是迭代器，因此 Wiener 攻击可以逐个检查候选，无需预先分配并
    保存另一份完整列表。
    """

    p_prev2, p_prev1 = 0, 1
    q_prev2, q_prev1 = 1, 0

    for coefficient in coefficients:
        if not isinstance(coefficient, int):
            raise TypeError("连分数系数必须全部为整数")

        p = coefficient * p_prev1 + p_prev2
        q = coefficient * q_prev1 + q_prev2
        yield p, q

        p_prev2, p_prev1 = p_prev1, p
        q_prev2, q_prev1 = q_prev1, q
