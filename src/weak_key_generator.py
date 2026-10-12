"""生成故意存在 Wiener 漏洞的 RSA 教学密钥。

实现中只削弱私钥指数的选择。素数候选仍来自密码学安全的随机数源，两个
素数仍然互不相同且大小接近，并且会检查普通 RSA 的全部一致性等式。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from time import perf_counter
from typing import Any

from .number_theory import gcd, generate_prime, integer_sqrt, mod_inverse
from .rsa import RSAKeyPair


@dataclass(frozen=True)
class WeakRSAKeyPair:
    """保存一组故意削弱的 RSA 密钥及其生成诊断信息。"""

    n: int
    e: int
    d: int
    p: int
    q: int
    phi: int
    requested_bits: int
    modulus_bits: int
    d_bits: int
    target_ratio: float
    approximate_threshold: int
    d_to_threshold: float
    below_wiener_bound: bool
    generation_elapsed_s: float

    @property
    def public_key(self) -> tuple[int, int]:
        """仅返回公开信息 (n, e)。"""

        return self.n, self.e

    @property
    def key_pair(self) -> RSAKeyPair:
        """返回不包含生成元数据的 RSA 数学字段。"""

        return RSAKeyPair(self.n, self.e, self.d, self.p, self.q, self.phi)


def approximate_wiener_threshold(n: int) -> int:
    """返回整数近似值 floor(sqrt(sqrt(n))) // 3。

    整个计算只使用整数平方根，尤其不会把 2048-bit 模数转换成浮点数。
    """

    if n <= 0:
        raise ValueError("n 必须为正数")
    return integer_sqrt(integer_sqrt(n)) // 3


def is_below_wiener_bound(d: int, n: int) -> bool:
    """使用整数精确判断课程边界 d < n**(1/4) / 3。

    当 d 和 n 为正数时，对不等式两边取四次方，可得到等价判断
    81*d**4 < n，从而避免浮点舍入误差。
    """

    if d <= 0 or n <= 0:
        raise ValueError("d 和 n 都必须为正数")
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


def _nearest_odd_coprime(target: int, phi: int) -> int:
    """寻找接近 target、大于 1 且与 phi 互素的奇数 d。

    两个奇 RSA 素数对应的 phi 一定是偶数，因此偶数 d 不可能与其
    互素。算法从最接近目标的奇数开始，交替检查其上方和下方的候选，使
    最终值尽量接近请求比例。
    """

    center = max(3, target)
    if center % 2 == 0:
        center += 1

    # 教学实验中的目标比例相对于 phi 应当非常小。如果比例导致 d 超出
    # 合法 RSA 范围，应明确报告输入无效，不能悄悄换成差异很大的私钥指数。
    if center >= phi:
        raise ValueError("目标私钥指数必须小于 phi")

    offset = 0
    while True:
        upper = center + offset
        if upper < phi and gcd(upper, phi) == 1:
            return upper

        if offset != 0:
            lower = center - offset
            if lower > 1 and gcd(lower, phi) == 1:
                return lower

        offset += 2


# 【课程核心代码】弱密钥构造需填写实际编写者，并能解释为何密钥仍然合法。
def generate_weak_rsa(
    bits: int,
    d_target_ratio: int | float | str | Fraction = 0.5,
    rng: Any = None,
    primality_rounds: int = 40,
) -> WeakRSAKeyPair:
    """生成一组私钥指数被故意选小、但数学上仍合法的 RSA 密钥。

    d_target_ratio 用来缩放课程中的近似边界
    T = floor(sqrt(sqrt(n))) // 3。例如，0.5 表示希望私钥指数接近
    该边界的一半。返回值是合法 RSA 密钥，但它被故意设计为不安全，只能
    用于本地教学实验。
    """

    if bits < 16:
        raise ValueError("弱 RSA 生成至少需要 16-bit 模数")
    if primality_rounds <= 0:
        raise ValueError("素性检测轮数 primality_rounds 必须为正数")

    ratio = _ratio_as_fraction(d_target_ratio)
    prime_bits = (bits + 1) // 2
    started = perf_counter()

    while True:
        p = generate_prime(prime_bits, rng=rng, rounds=primality_rounds)
        q = generate_prime(prime_bits, rng=rng, rounds=primality_rounds)
        if p == q:
            continue

        n = p * q
        if n.bit_length() != bits:
            continue

        phi = (p - 1) * (q - 1)
        threshold = approximate_wiener_threshold(n)
        if threshold < 3:
            # 这是针对异常小教学参数的防御性判断。
            continue

        # 使用精确分数运算，将 ratio*T 四舍五入到最接近的整数。
        scaled = ratio.numerator * threshold
        target_d = (scaled + ratio.denominator // 2) // ratio.denominator

        # 不切实际的大比例可能使 d 超出合法 RSA 范围。此时让辅助函数明确
        # 抛出 ValueError，避免无限重新采样；改变 p、q 不会从数量级上改变
        # phi/T，因此继续采样也无法真正解决问题。
        d = _nearest_odd_coprime(target_d, phi)

        e = mod_inverse(d, phi)

        # 下面的检查明确记录并强制执行 RSA 的定义性不变量。除非前面的
        # 核心算法存在错误，否则这些条件不应失败。
        if not (1 < e < phi and (e * d) % phi == 1):
            raise AssertionError("生成的数值无法构成合法 RSA 密钥")

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
