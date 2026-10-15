"""RSA 运算与普通 RSA 密钥生成。

本模块直接对整数消息执行 RSA 运算，没有使用 OAEP 或其他填充方案，
因此仅供本项目的数学演示和实验使用。
"""

from __future__ import annotations

from dataclasses import dataclass

from Crypto.Util.number import getPrime

from .number_theory import gcd, mod_inverse


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
    # 三参数 pow 完成模幂运算，该算法由 Python 提供。
    return pow(message, e, n)


def rsa_decrypt(ciphertext: int, d: int, n: int) -> int:
    """按照 ciphertext**d mod n 解密一个 RSA 整数。"""

    _validate_transform_inputs(ciphertext, d, n, "密文")
    # 三参数 pow 完成模幂运算，该算法由 Python 提供。
    return pow(ciphertext, d, n)


# 【自己实现】组织普通 RSA 参数并检查各项合法条件。
def generate_normal_rsa(bits: int) -> RSAKeyPair:
    """生成模数位数恰好为 bits 的普通 RSA 密钥对。

    使用标准公钥指数 65537。两个素数具有相同位数，因此大小相近。如果
    它们的乘积位数不符合要求，或者 65537 与 phi 不互素，就重新生成
    整对素数。

    参数：
        bits: 要求的 n 位数。至少为 17，才能使合法的模数和欧拉函数值
            有可能大于固定指数 65537。

    素数由 PyCryptodome 的 getPrime 函数生成，本项目不实现素性检测。
    """

    if bits < 17:
        raise ValueError("使用 e=65537 的普通 RSA 至少需要 17-bit 模数")
    public_exponent = 65_537
    # 等位数素数满足项目中“大小接近”的要求。请求奇数位模数时，乘积可能
    # 多出一位，因此后面还必须检查 n 的准确位数。
    prime_bits = (bits + 1) // 2

    while True:
        # getPrime 负责素数生成和内部素性检测。
        p = getPrime(prime_bits)
        q = getPrime(prime_bits)

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
