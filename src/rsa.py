"""RSA 运算与普通 RSA 密钥生成。

本模块直接对整数消息执行 RSA 运算，没有使用 OAEP 或其他填充方案，
因此仅供本项目的数学演示和实验使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from Crypto.Util.number import getPrime


@dataclass(frozen=True)
class RSAKeyPair:
    """保存一对 RSA 密钥的全部字段。
    n、e 构成公钥；d、p、q 和 phi 是不公开的。
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

# AI编写的边界条件检查，并加到各个位置
def _validate_transform_inputs(value: int, exponent: int, n: int, name: str) -> None:
    """检查 RSA 变换共同需要满足的整数取值条件。"""

    if n <= 1:
        raise ValueError("RSA 模数 n 必须大于 1")
    if exponent <= 0:
        raise ValueError("RSA 指数必须为正数")
    if not 0 <= value < n:
        raise ValueError(f"{name} 必须满足 0 <= {name} < n")


def rsa_encrypt(message: int, e: int, n: int) -> int:
    """message**e mod n，这里默认 message 是一个整数。"""

    _validate_transform_inputs(message, e, n, "消息")
    # 三参数 pow 完成模幂运算，Python 提供。
    return pow(message, e, n)


def rsa_decrypt(ciphertext: int, d: int, n: int) -> int:
    """ciphertext**d mod n 解密。"""

    _validate_transform_inputs(ciphertext, d, n, "密文")

    return pow(ciphertext, d, n)


# 【自己实现】正常组织 RSA 参数并检查各项合法条件。
def generate_normal_rsa(bits: int) -> RSAKeyPair:
    # 这里的e使用常用的固定值 65537，保证了加密和解密的效率。
    # 如果 bits 太小，e 可能大于 phi，因此需要检查位数。
    if bits < 17:
        raise ValueError("e=65537，所以至少需要 17-bit 的 n 才能保证 e < phi。")
    e = 65_537

    # 保证p*q的位数能达到bits，所以要向上取整
    prime_bits = (bits + 1) // 2

    while True:

        p = getPrime(prime_bits)
        q = getPrime(prime_bits)

        # 首先排除 p 和 q 相等的情况，避免 n 变成完全平方数。
        if p == q:
            continue

        n = p * q
        if n.bit_length() != bits:
            continue

        phi = (p - 1) * (q - 1)

        # 通过重新采样素数，可以始终保留约定俗成的固定指数 65537。
        if e >= phi or gcd(e, phi) != 1:
            continue

        # Python 的 pow 可以直接求模逆，使 e*d ≡ 1 (mod phi)。
        d = pow(e, -1, phi)
        return RSAKeyPair(
            n=n,
            e=e,
            d=d,
            p=p,
            q=q,
            phi=phi,
        )
