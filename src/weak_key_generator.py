
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd, isqrt
from time import perf_counter

from Crypto.Util.number import getPrime

from .rsa import RSAKeyPair


@dataclass(frozen=True)
class WeakRSAKeyPair:

    n: int
    e: int
    d: int
    p: int
    q: int
    phi: int

    requested_bits: int
    modulus_bits: int
    d_bits: int
    target_ratio: float # d / approximate_threshold 控制d与Wiener边界的接近程度，0.5表示d接近Wiener边界的一半
    approximate_threshold: int # Wiener边界的整数近似值
    d_to_threshold: float # 最终找到的 d 与 Wiener 边界的比值，d / approximate_threshold
    below_wiener_bound: bool
    generation_elapsed_s: float

    @property
    def public_key(self) -> tuple[int, int]:

        return self.n, self.e

    @property
    def key_pair(self) -> RSAKeyPair:

        return RSAKeyPair(self.n, self.e, self.d, self.p, self.q, self.phi)


# 【自己实现】 Wiener 边界的整数近似计算。
# 用于构造一个差不多的 d。是否真正满足严格不等式，交给下面的 is_below_wiener_bound 判断。
def approximate_wiener_threshold(n: int) -> int:
    # d < n^(1/4) / 3，返回整数近似值 floor(sqrt(sqrt(n))) // 3。
    return isqrt(isqrt(n)) // 3


# 【自己实现】判断 d 是否低于 Wiener 边界。
def is_below_wiener_bound(d: int, n: int) -> bool:
    # d < n**(1/4) / 3 同时取4次方：81*d**4 < n，从而避免浮点舍入误差。
    return 81 * d**4 < n


def _ratio_as_fraction(value: int | float | str | Fraction) -> Fraction:
    """把用户输入的比例转换为分数，避免对巨大浮点数进行运算。"""

    try:
        # 先转成字符串，可让 0.25 这样的十进制浮点数准确得到 1/4，
        # 而不是得到其冗长的二进制浮点展开。
        ratio = value if isinstance(value, Fraction) else Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("d_target_ratio 必须是有限正数") from exc

    if ratio <= 0:
        raise ValueError("d_target_ratio 必须为正数")
    return ratio


# 【自己实现】寻找接近 target 且与 phi 互素的奇数 d。
def _nearest_odd_coprime(target: int, phi: int) -> int:
    """寻找接近 target、> 1 且与 phi 互素的奇数 d。  """

    # 两个p和q都是奇数prime，对应的 phi 一定是偶数，因此偶数 d 不可能与其互素。
    # 算法从最接近 target 的奇数开始，交替检查其上方和下方的奇数，使最终值尽量接近 target。

    center = target
    # 如果 target 是偶数，向上取奇数。
    if center % 2 == 0:
        center += 1

    # 如果 target 超过 phi，直接抛出异常，避免过多无效循环。
    if center >= phi:
        raise ValueError("目标私钥指数必须小于 phi")

    offset = 0
    while True:
        upper = center + offset
        if upper < phi and gcd(upper, phi) == 1:
            return upper

        lower = center - offset
        if lower > 1 and gcd(lower, phi) == 1:
            return lower

        offset += 2


# 【自己实现】弱 RSA 参数构造和合法性检查。
def generate_weak_rsa(
    bits: int,
    d_target_ratio: int | float | str | Fraction = 0.5,
) -> WeakRSAKeyPair:
    """生成一组 d 被故意选小、但数学上仍合法的 RSA 密钥。"""
    # d_target_ratio 用来缩放与 Wiener 边界的接近程度。用来做多组实验

    ratio = _ratio_as_fraction(d_target_ratio)
    prime_bits = (bits + 1) // 2

    # 记录开始时间，方便计算生成耗时。
    started = perf_counter()

    while True:

        p = getPrime(prime_bits)
        q = getPrime(prime_bits)
        if p == q:
            continue

        n = p * q
        if n.bit_length() != bits:
            continue

        phi = (p - 1) * (q - 1)
        threshold = approximate_wiener_threshold(n)

        # ratio 是 Fraction，因此这里不会因为浮点数而丢失精度。
        target_d = round(ratio * threshold)

        # 寻找接近 target_d 附近满足条件的 d。
        d = _nearest_odd_coprime(target_d, phi)

        # Python 的 pow 可以直接求模逆，使 e*d ≡ 1 (mod phi)。
        e = pow(d, -1, phi)

        # 计算耗时。
        elapsed = perf_counter() - started

        return WeakRSAKeyPair(
            n=n,
            e=e,
            d=d,
            p=p,
            q=q,
            phi=phi,
            requested_bits=bits,
            modulus_bits=n.bit_length(),
            d_bits=d.bit_length(),
            target_ratio=float(ratio),
            approximate_threshold=threshold,
            d_to_threshold=d / threshold,
            below_wiener_bound=is_below_wiener_bound(d, n),
            generation_elapsed_s=elapsed,
        )
