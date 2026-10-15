"""仅使用公开信息实现 Wiener 连分数攻击。"""

from __future__ import annotations

from dataclasses import dataclass
from math import isqrt
from time import perf_counter

from .continued_fraction import continued_fraction, convergents


@dataclass(frozen=True)
class AttackResult:
    """保存恢复出的 RSA 私钥指数、因数和攻击诊断信息。"""

    d: int
    p: int
    q: int
    candidate_index: int
    convergents_checked: int
    elapsed_s: float


# 【自己实现】Wiener 攻击流程及每个候选的验证逻辑。
def wiener_attack(e: int, n: int) -> AttackResult | None:
    """尝试仅从公开的 (e, n) 恢复存在 Wiener 弱点的 RSA 密钥。

    恒等式 e*d - k*phi(n) = 1 表明：当 d 足够小且 RSA 素数满足
    Wiener 定理的假设时，k/d 会非常接近 e/n。算法逐一检查渐近
    分数 k/d，只有当候选能够精确重建 n 的整数因数时才接受。

    返回：
        成功时返回 AttackResult，否则返回 None。None 仅
        表示本次攻击没有找到密钥，并不能证明该 RSA 密钥是安全的。

    异常：
        ValueError: 输入不满足本实现要求的公钥范围时抛出，即必须满足
            n > 1 且 1 < e < n。
    """

    if n <= 1:
        raise ValueError("n 必须大于 1")
    if not 1 < e < n:
        raise ValueError("e 必须满足 1 < e < n")

    started = perf_counter()
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

        candidate_phi = ed_minus_one // k
        if candidate_phi <= 0:
            continue

        # 因为 phi(n)=(p-1)(q-1)=n-(p+q)+1，正确的 phi 可以给出
        # s=p+q。因此 p、q 是方程 x^2 - s*x + n = 0 的两个根。
        factor_sum = n - candidate_phi + 1
        discriminant = factor_sum * factor_sum - 4 * n
        if discriminant < 0:
            continue

        # isqrt 计算整数平方根，候选判别与验证逻辑由本函数完成。
        root = isqrt(discriminant)
        if root * root != discriminant:
            continue

        # 二次方程公式中的两个分子都必须为偶数，p、q 才会是整数。
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
