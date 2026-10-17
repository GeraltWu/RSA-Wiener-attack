"""仅使用公开信息实现 Wiener 连分数攻击。"""

from __future__ import annotations

from dataclasses import dataclass
from math import isqrt
from time import perf_counter

from .continued_fraction import continued_fraction, convergents


@dataclass(frozen=True)
class AttackResult:
    """保存恢复出的 d, p, q, 和攻击诊断数据。"""

    d: int
    p: int
    q: int
    candidate_index: int
    convergents_checked: int
    elapsed_s: float


# 【自己实现】Wiener 攻击流程及每个候选的验证逻辑。
def wiener_attack(e: int, n: int) -> AttackResult | None:
    """尝试仅从公开的 (e, n) 恢复存在 Wiener 弱点的 RSA 密钥。
    当 d 足够小且 RSA 素数满足 Wiener 定理的假设时，k/d 会非常接近 e/n。
    算法逐一检查渐近分数 k/d，只有当候选能够精确重建 p 和 q 时才接受。
    """

    started = perf_counter()
    # 计算 e/n 的 continued fraction coefficients。
    coefficients = continued_fraction(e, n)

    for index, (k, candidate_d) in enumerate(convergents(coefficients)):
        checked = index + 1

        # 因为 e < n，第一个渐近分数是 0/1；k=0 无法作为 e*d-1 的除数。
        if k == 0:
            continue

        ed_minus_one = e * candidate_d - 1
        # RSA 恒等式要求 phi = (e*d - 1)/k 必须为整数。
        if ed_minus_one % k != 0:
            continue

        # 得到可能的 phi(n) ，并检查它是否能精确重建 p 和 q。
        candidate_phi = ed_minus_one // k
        if candidate_phi <= 0:
            continue

        # 因为 phi(n)=(p-1)(q-1)=n-(p+q)+1
        # p+q = n-phi(n)+1，pq = n
        # 可以构造一个方程让 p 和 q 成为它的两个根。x = p 或 x = q
        # 这个方程就是 (x-p)(x-q) = 0
        # 因此 p、q 是方程 x^2 - (p+q)*x + pq = 0 的两个根。
        # 接下来检查判别式 delta = b^2 - 4ac >= 0，就能判断 p、q 是否存在。
        factor_sum = n - candidate_phi + 1 # p+q
        discriminant = factor_sum * factor_sum - 4 * n
        if discriminant < 0:
            continue

        # delta = (p+q)²-4pq = p²+2pq+q²-4pq = p²-2pq+q² = (p-q)²。
        # 必须保证 p、q 是整数，先保证 p - q 是整数
        # 可以检查 delta 能否开平方得到整数。
        root = isqrt(discriminant) # root = abs(p - q)
        if root * root != discriminant:
            continue

        # (p+q)+(p-q) = 2p，(p+q)-(p-q) = 2q (如果p>q，反过来也一样)
        # 2p 和 2q 都必须为偶数，p、q 才会是整数。
        if (factor_sum + root) % 2 != 0 or (factor_sum - root) % 2 != 0:
            continue

        p = (factor_sum + root) // 2
        q = (factor_sum - root) // 2

        # 精确分解是决定性验证。再次检查 phi 和模逆等式，是为了明确保证
        # 每个被接受的候选都满足全部 RSA 不变量。
        if (
            p > 1
            and q > 1
            and p * q == n
            and (p - 1) * (q - 1) == candidate_phi
            and (e * candidate_d) % candidate_phi == 1
        ):
            return AttackResult(
                d=candidate_d,
                p=p,
                q=q,
                candidate_index=index,
                convergents_checked=checked,
                elapsed_s=perf_counter() - started,
            )

    return None
