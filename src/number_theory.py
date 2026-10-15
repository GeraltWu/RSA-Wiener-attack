"""RSA 实现所需的基础数论算法。"""

from __future__ import annotations


# 【自己实现】使用欧几里得算法计算最大公约数。
def gcd(a: int, b: int) -> int:
    """返回两个整数的最大公约数。

    欧几里得算法反复利用 gcd(a, b) == gcd(b, a mod b)。当第二个数
    变为零时，第一个数的绝对值就是最大公约数。按照约定，
    gcd(0, 0) 返回零。
    """
    while b != 0:
        a, b = b, a % b

    # 最大公约数取非负值。
    return abs(a)


# 【自己实现】扩展欧几里得算法及回代过程。
def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """返回 (g, x, y), g == a*x + b*y。

    参数 a、b 为非负整数。算法先递归执行普通欧几里得除法，到达余数为零的
    情况后，再逐层回代得到原始 a、b 的系数。
    """

    # 递归终点：a*1 + 0*0 = a。
    if b == 0:
        return a, 1, 0

    quotient = a // b
    remainder = a % b

    # 向下递归，就是普通gcd。
    g, x1, y1 = extended_gcd(b, remainder)

    # remainder = a - quotient*b，把下一层等式代回当前一层。
    x = y1
    y = x1 - quotient * y1
    return g, x, y


# 【自己实现】根据扩展欧几里得结果计算模逆。
def mod_inverse(a: int, modulus: int) -> int:
    """返回 a 模 modulus 的乘法逆元。
    当且仅当 gcd(a, modulus) == 1 时逆元存在。若 a*x + modulus*y == 1，x 就是所需逆元。
    """
    # 先把 a 化到非负，再交给扩展欧几里得算法。
    normalized_a = a % modulus
    divisor, coefficient, _ = extended_gcd(normalized_a, modulus)
    if divisor != 1:
        raise ValueError(f"{a} 在模 {modulus} 意义下不存在乘法逆元")

    # Python 的取模运算会把可能为负的coefficient规范化到非负。
    return coefficient % modulus
