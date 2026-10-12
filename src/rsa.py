"""RSA 运算与普通 RSA 密钥生成。

本模块直接对整数消息执行 RSA 运算，没有使用 OAEP 或其他填充方案，
因此仅供本项目的数学演示和实验使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .number_theory import gcd, generate_prime, mod_inverse


@dataclass(frozen=True)
class RSAKeyPair:
    """保存一对 RSA 密钥的全部数学字段。

    n 和 e 构成公钥；d、p、q 和 phi 是秘密字段，绝不能传给攻击函数。
    """

    n: int
    e: int
    d: int
    p: int
    q: int
    phi: int

    @property
    def public_key(self) -> tuple[int, int]:
        """按照惯例以 (n, e) 顺序返回公钥。"""

        return self.n, self.e


# 【课程核心代码】RSA 加解密和密钥生成需填写实际编写者，并能现场解释。
def _validate_transform_inputs(value: int, exponent: int, n: int, name: str) -> None:
    """检查 RSA 变换共同需要满足的整数取值条件。"""

    if n <= 1:
        raise ValueError("RSA 模数 n 必须大于 1")
    if exponent <= 0:
        raise ValueError("RSA 指数必须为正数")
    if not 0 <= value < n:
        raise ValueError(f"{name} 必须满足 0 <= {name} < n")


def rsa_encrypt(message: int, e: int, n: int) -> int:
    """按照 message**e mod n 加密一个 RSA 整数。

    合法消息必须满足 0 <= message < n。本函数不进行编码，也不使用
    安全填充，仅用于演示 RSA 的代数过程。
    """

    _validate_transform_inputs(message, e, n, "消息")
    return pow(message, e, n)


def rsa_decrypt(ciphertext: int, d: int, n: int) -> int:
    """按照 ciphertext**d mod n 解密一个 RSA 整数。"""

    _validate_transform_inputs(ciphertext, d, n, "密文")
    return pow(ciphertext, d, n)


def generate_normal_rsa(
    bits: int,
    rng: Any = None,
    primality_rounds: int = 40,
) -> RSAKeyPair:
    """生成模数位数恰好为 bits 的普通 RSA 密钥对。

    使用标准公钥指数 65537。两个素数具有相同位数，因此大小相近。如果
    它们的乘积位数不符合要求，或者 65537 与 phi 不互素，就重新生成
    整对素数。

    参数：
        bits: 要求的 n 位数。至少为 17，才能使合法的模数和欧拉函数值
            有可能大于固定指数 65537。
        rng: 可选的密码学安全随机数源。
        primality_rounds: 每个素数候选执行 Miller--Rabin 检测的轮数。
    """

    if bits < 17:
        raise ValueError("使用 e=65537 的普通 RSA 至少需要 17-bit 模数")
    if primality_rounds <= 0:
        raise ValueError("素性检测轮数 primality_rounds 必须为正数")

    public_exponent = 65_537
    # 等位数素数满足项目中“大小接近”的要求。请求奇数位模数时，乘积可能
    # 多出一位，因此后面还必须检查 n 的准确位数。
    prime_bits = (bits + 1) // 2

    while True:
        p = generate_prime(prime_bits, rng=rng, rounds=primality_rounds)
        q = generate_prime(prime_bits, rng=rng, rounds=primality_rounds)

        if p == q:
            continue

        n = p * q
        if n.bit_length() != bits:
            continue

        phi = (p - 1) * (q - 1)
        # 合法 RSA 公钥指数必须位于 (1, phi) 内，并且与 phi 互素。
        # 通过重新采样素数，可以始终保留约定俗成的固定指数 65537。
        if public_exponent >= phi or gcd(public_exponent, phi) != 1:
            continue

        private_exponent = mod_inverse(public_exponent, phi)
        return RSAKeyPair(
            n=n,
            e=public_exponent,
            d=private_exponent,
            p=p,
            q=q,
            phi=phi,
        )
