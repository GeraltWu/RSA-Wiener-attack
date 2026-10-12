"""RSA 实现所需的基础数论算法。
"""

from __future__ import annotations

import secrets
from typing import Any


# 在执行开销更大的 Miller--Rabin 模幂前，先用这些小素数试除，
# 可以快速排除大量合数候选。
_SMALL_PRIMES = (
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
)


# 【课程核心代码】以下函数需要在作者声明中填写实际编写者，并能现场解释。
def gcd(a: int, b: int) -> int:
    """返回两个整数的最大公约数。

    欧几里得算法反复利用 gcd(a, b) == gcd(b, a mod b)。当第二个数
    变为零时，第一个数的绝对值就是最大公约数。按照约定，
    gcd(0, 0) 返回零。
    """

    a, b = abs(a), abs(b)
    while b != 0:
        a, b = b, a % b
    return a


def integer_sqrt(n: int) -> int:
    """返回 floor(sqrt(n))，全程只使用整数运算。

    牛顿迭代公式为 next_x = (x + n//x)//2。当新值不再减小时，当前值
    就是平方根的向下取整。该函数用于替代 Python 3.8 才提供的 math.isqrt。
    """

    if n < 0:
        raise ValueError("n 必须为非负数")
    if n < 2:
        return n

    # 初值取在真实平方根上方，保证迭代单调下降。
    x = 1 << ((n.bit_length() + 1) // 2)
    while True:
        next_x = (x + n // x) // 2
        if next_x >= x:
            return x
        x = next_x


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """返回 (g, x, y)，使 a*x + b*y == g == gcd(a, b)。

    算法在计算每个欧几里得余数的同时，记录该余数关于原始 a、b
    的线性组合系数。即使输入中存在负数，返回的最大公约数仍保证非负。
    """

    # 每轮循环都保持以下不变量：
    # old_r = a*old_x + b*old_y，且 r = a*x + b*y。
    old_r, r = abs(a), abs(b)
    old_x, x = 1, 0
    old_y, y = 0, 1

    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_x, x = x, old_x - quotient * x
        old_y, y = y, old_y - quotient * y

    # 上面的循环使用输入的绝对值，因此这里恢复系数的符号，
    # 使 Bézout 等式最终使用调用者传入的原始整数表示。
    if a < 0:
        old_x = -old_x
    if b < 0:
        old_y = -old_y

    return old_r, old_x, old_y


def mod_inverse(a: int, modulus: int) -> int:
    """返回 a 在模 modulus 意义下的乘法逆元。

    参数：
        a: 需要求逆的整数，也允许传入标准剩余系之外的值。
        modulus: 大于 1 的正模数。

    异常：
        ValueError: 模数不合法，或逆元不存在时抛出。

    当且仅当 gcd(a, modulus) == 1 时逆元存在。若
    a*x + modulus*y == 1，对等式两边取模 modulus，即可看出
    x 就是所需逆元。
    """

    if modulus <= 1:
        raise ValueError("模数必须大于 1")

    divisor, coefficient, _ = extended_gcd(a, modulus)
    if divisor != 1:
        raise ValueError(f"{a} 在模 {modulus} 意义下不存在乘法逆元")

    # Python 的取模运算会把可能为负的 Bézout 系数规范化到
    # [0, modulus - 1] 区间内。
    return coefficient % modulus


def is_probable_prime(
    n: int,
    rounds: int = 40,
    rng: Any = None,
) -> bool:
    """使用 Miller--Rabin 算法判断 n 是否为大概率素数。

    参数：
        n: 待检测的整数。
        rounds: 独立随机底数的检测轮数。对奇合数而言，每轮误判概率至多
            为 1/4，因此默认 40 轮是较保守的教学设置。
        rng: 可选随机数源。默认使用 secrets.SystemRandom，避免在
            素数生成过程中额外引入弱随机数漏洞。

    返回：
        False 表示已经证明 n 是合数；True 表示 n 通过
        全部检测，是大概率素数，但并不构成形式化的素数证明。
    """

    if rounds <= 0:
        raise ValueError("检测轮数 rounds 必须是正整数")
    if n < 2:
        return False

    # 这些判断既直接处理小素数本身，也能低成本排除能被小素数整除的候选。
    for prime in _SMALL_PRIMES:
        if n == prime:
            return True
        if n % prime == 0:
            return False

    # 将 n - 1 分解为 2**s * d，其中 d 为奇数；这是 Miller--Rabin
    # 见证检测所需的标准形式。
    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    random_source = rng if rng is not None else secrets.SystemRandom()
    for _ in range(rounds):
        # 底数 0、1 和 n-1 无法揭示合数，因此从 [2, n-2] 中选择。
        base = random_source.randrange(2, n - 1)
        value = pow(base, d, n)

        # 若结果为模 n 意义下的 1 或 -1，则当前见证立即通过。
        if value in (1, n - 1):
            continue

        # 连续平方依次检查 base**(2**r * d)。若得到 -1，则本轮通过；
        # 如果始终无法得到 -1，就可确定候选数是合数。
        for _ in range(s - 1):
            value = pow(value, 2, n)
            if value == n - 1:
                break
        else:
            return False

    return True


def generate_prime(
    bits: int,
    rng: Any = None,
    rounds: int = 40,
) -> int:
    """生成一个位数恰好为 bits 的奇数大概率素数。

    将最高位置 1 以保证准确位数；将最低位置 1，因为所有大于 2 的素数
    都是奇数。每次独立随机采样候选，而不是从某个数开始顺序递增，从而
    避免以可预测方式遍历相邻奇数。
    """

    if bits < 2:
        raise ValueError("素数位数至少为 2")
    if rounds <= 0:
        raise ValueError("检测轮数 rounds 必须是正整数")

    random_source = rng if rng is not None else secrets.SystemRandom()
    high_bit = 1 << (bits - 1)

    while True:
        candidate = random_source.getrandbits(bits)
        candidate |= high_bit  # 强制最高位为 1，保证准确位数
        candidate |= 1  # 强制最低位为 1，保证候选为奇数

        if is_probable_prime(candidate, rounds=rounds, rng=random_source):
            return candidate
